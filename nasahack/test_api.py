import json
import tempfile
import unittest
from pathlib import Path
from datetime import date
from unittest.mock import patch, AsyncMock
import httpx
from fastapi.testclient import TestClient
import app as module

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.old=module.DATA
        module.DATA=Path(self.temp.name)
        self.client=TestClient(module.app)
        self.workspace=self.client.get('/api/workspace').json()
        self.body={'scenario':self.workspace['scenarios'][0],'date':str(date.today())}
    def tearDown(self):
        module.DATA=self.old
        self.temp.cleanup()
    def test_crud_and_export(self):
        s=self.workspace['scenarios'][0]
        s['profile']['name']='Test Pilot'
        del s['days'][str(date.today())]
        self.assertEqual(self.client.put('/api/workspace',json=self.workspace).status_code,200)
        restored=self.client.get('/api/workspace').json()['scenarios'][0]
        self.assertEqual(restored['profile']['name'],'Test Pilot')
        self.assertNotIn(str(date.today()),restored['days'])
        self.assertEqual(self.client.post('/api/calculate',json=self.body).status_code,200)
        self.assertTrue(self.client.get('/api/export').json()['plans'])
    def test_invalid_input_rejected(self):
        self.body['scenario']['profile']['weight']=-5
        self.assertEqual(self.client.post('/api/calculate',json=self.body).status_code,422)
    def test_offline_fallback(self):
        with patch('httpx.AsyncClient.post',new=AsyncMock(side_effect=httpx.ConnectError('offline'))):
            response=self.client.post('/api/analyze',json=self.body)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['source'],'Rule-based fallback')
        self.assertTrue(self.client.get('/api/export').json()['analyses'])
    def test_model_cannot_inject_numbers(self):
        response=httpx.Response(200,json={'message':{'content':json.dumps({'order':[999],'text':'Invented bone loss'})}},request=httpx.Request('POST','http://localhost'))
        with patch('httpx.AsyncClient.post',new=AsyncMock(return_value=response)):
            result=self.client.post('/api/analyze',json=self.body).json()
        self.assertEqual(result['source'],'Rule-based fallback')
        self.assertNotIn('Invented',result['text'])
    def test_valid_model_selection(self):
        result=module.calculate(module.Calculation.model_validate(self.body).scenario,date.today())
        count=2+len(result['reasons'])+len(result['alerts'])
        response=httpx.Response(200,json={'message':{'content':json.dumps({'order':list(reversed(range(count)))})}},request=httpx.Request('POST','http://localhost'))
        with patch('httpx.AsyncClient.post',new=AsyncMock(return_value=response)):
            result=self.client.post('/api/analyze',json=self.body).json()
        self.assertIn('Qwen-assisted',result['source'])

    def test_published_nasa_table(self):
        data=self.client.get('/api/nasa-data').json()
        self.assertEqual(len(data['rows']),18)
        ca=[r for r in data['rows'] if r['experiment']=='VEG-01A' and r['environment']=='Flight' and r['element']=='Ca']
        self.assertEqual(ca[0]['mean_mg_per_g_dry'],4.97)
        self.assertIn('dry leaf tissue',data['unit'])

if __name__=='__main__':unittest.main()
