from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi import HTTPException
from fastapi.responses import Response
from models import Workspace, Calculation
from seed import examples
from engine import calculate
import json
import os
import threading
import httpx
import hashlib
import csv

ROOT = Path(__file__).parent
app = FastAPI(title='Eiserion simulator')
DATA = Path(os.environ.get('EISERION_DATA_DIR', str(ROOT / 'data')))
LOCK = threading.RLock()

def read_store():
    with LOCK:
        if not (DATA / 'store.json').exists():
            return {'workspace':examples().model_dump(mode='json'), 'plans':{}, 'analyses':{}}
        return json.loads((DATA / 'store.json').read_text(encoding='utf-8'))

def write_store(data):
    with LOCK:
        DATA.mkdir(exist_ok=True, parents=True)
        temp = DATA / 'store.tmp'
        temp.write_text(json.dumps(data, indent=2), encoding='utf-8')
        temp.replace(DATA / 'store.json')

def fingerprint(request):
    return hashlib.sha256(request.model_dump_json().encode()).hexdigest()

@app.get('/api/workspace')
def workspace():
    return read_store()['workspace']

@app.put('/api/workspace')
def save_workspace(data: Workspace):
    ids=[s.id for s in data.scenarios]
    if len(ids)!=len(set(ids)):
        raise HTTPException(422, 'Scenario IDs must be unique')
    with LOCK:
        store=read_store(); store['workspace']=data.model_dump(mode='json'); write_store(store)
    return {'saved':True}

@app.get('/api/examples')
def sample_data():
    return examples().model_dump(mode='json')

@app.post('/api/calculate')
def calculation(request: Calculation):
    result=calculate(request.scenario, request.date)
    with LOCK:
        store=read_store()
        store['plans'][f'{request.scenario.id}:{request.date}']={'input_hash':fingerprint(request), 'result':result}
        write_store(store)
    return result

@app.post('/api/analyze')
async def analyze(request: Calculation):
    result=calculate(request.scenario, request.date)
    explanation='\n\n'.join([result['summary'], *result['reasons'], *result['alerts'], result['qus']['note']])
    source='Rule-based fallback'
    # The model can only select precomputed explanation IDs. No generated prose or
    # numbers are accepted, so it cannot invent measurements or override plans.
    statements=[result['summary'], *result['reasons'], *result['alerts'], result['qus']['note']]
    try:
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            response=await client.post('http://localhost:11434/api/chat',json={
                'model':'qwen3.5:4b','stream':False,'think':False,'format':'json',
                'messages':[{'role':'system','content':'You explain a fictional health simulation by prioritizing supplied statements. Return JSON with a single key order: an array of ALL statement indices in the best explanatory order. Do not generate numbers, advice, diagnoses, or new statements.'},
                {'role':'user','content':json.dumps({'profile':request.scenario.profile.model_dump(), 'results':result, 'statements':dict(enumerate(statements))})}],
                'options':{'temperature':0,'num_predict':256}})
            response.raise_for_status()
            order=json.loads(response.json()['message']['content'])['order']
            if not isinstance(order,list) or any(type(i) is not int for i in order) or sorted(order)!=list(range(len(statements))):
                raise ValueError('Invalid explanation selection')
            explanation='\n\n'.join(statements[i] for i in order)
            source='Qwen-assisted explanation (verified statements)'
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        pass
    output={'source':source, 'text':explanation,'input_hash':fingerprint(request)}
    with LOCK:
        store=read_store(); store['analyses'][f'{request.scenario.id}:{request.date}']=output; write_store(store)
    return output

@app.get('/api/export')
def export():
    return Response(json.dumps(read_store(),indent=2),media_type='application/json',headers={'Content-Disposition':'attachment; filename="eiserion-mock-data.json"'})

@app.get('/api/nasa-data')
def nasa_data():
    with (ROOT / 'nasa_data' / 'lettuce_elements.csv').open(newline='', encoding='utf-8') as file:
        rows = list(csv.DictReader(file))
    return {
        'dataset': 'ISS-grown lettuce elemental analysis (VEG-01A, VEG-01B, VEG-03A)',
        'study': 'https://osdr.nasa.gov/bio/repo/data/studies/OSD-267',
        'catalog': 'https://catalog.data.gov/dataset/microbiological-and-nutritional-analysis-of-lettuce-crops-grown-on-the-international-space',
        'table': 'https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2020.00199/pdf',
        'unit': 'mg/g dry leaf tissue',
        'statistic': 'published mean and standard error; n=3 per group',
        'rows': [{**row, 'mean_mg_per_g_dry': float(row['mean_mg_per_g_dry']), 'standard_error_mg_per_g_dry': float(row['standard_error_mg_per_g_dry'])} for row in rows],
    }

@app.get('/api/health')
def health():
    return {'status': 'ok', 'simulated': True}

app.mount('/', StaticFiles(directory=ROOT / 'static', html=True), name='static')
