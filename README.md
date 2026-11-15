# Eiserion — local simulation prototype

A small astronaut health **simulation** with manually entered fictional data. Python performs all calculations. Runs locally without sensors, external data APIs, Node, or Ollama.

The **NASA Data** page also contains real published measurements from the ISS lettuce VEG-01A, VEG-01B and VEG-03A experiments, transcribed from Table 7 of the primary research article. Calcium, magnesium and potassium means and standard errors are shown in mg/g dry leaf tissue. See [dataset provenance](./nasa_data/README.md) and the [NASA dataset catalog](https://catalog.data.gov/dataset/microbiological-and-nutritional-analysis-of-lettuce-crops-grown-on-the-international-space). These crop measurements are separate from the simulated astronaut records and cannot be converted into crew nutrient intake without serving data.

## Run on Windows

Python 3.10+ is required (tested here with Python 3.14.2).

```powershell
cd C:\Users\MSI\Downloads\nasahack
python -m pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. After dependencies are installed, double-click [start.bat](./start.bat). Stop the server with Ctrl+C. The app is intentionally bound to your computer only.

## Quick public demo on Render

1. Create a GitHub repository and upload this project folder to it. Keep `data/store.json` out of the repository; `.gitignore` already excludes `data/`.
2. In [Render](https://dashboard.render.com/), select **New → Blueprint**, connect the repository, and apply [render.yaml](./render.yaml). Select the free plan if prompted.
3. Open the resulting `https://...onrender.com` link. Check `/api/health` if the site does not load.

The blueprint installs Python dependencies, launches FastAPI, and serves the site. No Node build is needed. Render's free web service sleeps after inactivity and its local filesystem is temporary, so saved demo edits can disappear on sleep, restart, or redeploy. Export JSON before leaving if you need a copy. This version has one shared mock workspace and no login: visitors can see and edit each other's demo data. Do not enter real personal or medical data. The Qwen button uses a local Ollama address, so on Render it falls back to rule-based explanations unless a reachable Ollama service is configured in code.

## Try the core loop

1. Select **Balanced mission day** and today's date.
2. Open Nutrition and change energy from 2500 to 1000 kcal. The live workout changes from 40 to 24 minutes.
3. Open Exercise and change duration from 40 to 100 minutes at intensity 5. Tomorrow's energy changes from 2360 to 2600 kcal; the reduced workout remains 24 minutes.
4. Change recovery, condition, completion status, exercise type, or configured targets and inspect the explanations.
5. Click **Save data**. Reload to verify persistence.
6. Open Dashboard → Compare scenarios to compare the three editable examples.

Inputs recalculate after a short typing pause. Missing nutrition is blank/null; zero is an explicitly recorded zero. Select a new date to enter another day's records. One aggregate nutrition record and one exercise session are supported per date per scenario. Recovery/profile settings apply to the entire scenario, rather than being historical daily measurements.

Astronaut Profile offers blank scenarios, duplication, deletion, reset, and JSON export. Destructive UI actions ask for confirmation. Reset replaces the in-memory workspace; **Save data** commits it. QUS records support add/edit/delete. Exercise lets you edit tomorrow's workout or restore the engine proposal. Overrides remain visibly separate from recalculated proposals.

## Simple architecture

- [app.py](./app.py): FastAPI routes, atomic local JSON writes, export and optional Ollama integration.
- [models.py](./models.py): validated inputs.
- [engine.py](./engine.py): pure calculation rules and QUS comparisons.
- [seed.py](./seed.py): three editable fictional example profiles and datasets.
- [static/](./static/): plain JavaScript, CSS and accessible HTML/SVG charts, with hover values.
- `data/store.json`: created on first calculation/save; holds profiles, records, latest plans per scenario/date, and explanations. Export includes all of these. Plans/explanations carry input hashes; historical explanation entries can describe older inputs. The UI always recalculates and clears its explanation on edits.

Plain JavaScript replaces the proposed React/Vite stack to keep this testing version dependency-light. No build step. Local JSON replaces SQLite. This is a single-user prototype: multiple browser tabs may overwrite each other's saved workspace.

## Transparent demonstration rules

- Workload = minutes × intensity × completion factor (completed 1, partial 0.5, not completed 0). Sets/reps/resistance are recorded and displayed but not independently counted in the workload metric.
- Workout baseline = 25/40/50 minutes for beginner/intermediate/experienced.
- Duration factors: missing nutrition or exercise 0.7; energy or protein below 80% of target 0.6; recovery ≤4 or non-good condition 0.5; workload >400 units 0.75. The lowest applicable factor wins; factors are not compounded.
- Tomorrow's energy = configured base + activity adjustment (−150/0/+150 kcal) + workload × exercise type factor × 0.8. Type factors: resistance 1, cycling 1.1, running 1.2, mobility 0.4.
- Added exercise energy is assigned to carbohydrate at 4 kcal/g. Protein = body weight × configurable g/kg. Other nutrient targets remain fixed. Independently editable macro targets need not sum exactly to the energy target; the nutrition page displays macro-derived calories separately.
- Height, age and mission day provide context, not physiological predictions.
- QUS differences use good-quality entries at the same location and an earlier date. Same-date entries use the last entered as latest. No cross-location trend, BMD conversion, bone-loss percentage, diagnosis, or causal inference is produced. Device/protocol comparability remains unknown.

The energy formula, workout thresholds and activity/type factors are **illustrative software heuristics**, not validated astronaut requirements. Reference context for configurable defaults: [NIH exercise and protein](https://ods.od.nih.gov/factsheets/ExerciseAndAthleticPerformance-HealthProfessional/) describes 1.2–2.0 g/kg for athletes; this demo starts at 1.4. [NIH calcium](https://ods.od.nih.gov/factsheets/Calcium-Consumer/) lists 1000 mg for adults 19–50; [NIH vitamin D](https://ods.od.nih.gov/factsheets/VitaminD-Consumer/) lists 600 IU for adults 19–70. These are general reference examples, not individualized or universal spaceflight targets. Other editable defaults are demo inputs. Do not use this prototype for clinical or dietary decisions.

## Optional local Qwen

Install Ollama separately, then:

```powershell
ollama pull qwen3.5:4b
ollama serve
```

Use AI Analysis → **Explain with local Qwen**. The backend connects to `http://localhost:11434/api/chat`, with a 20-second timeout. Numerical results and plans remain entirely Python-owned. For this simple version, Qwen prioritizes a set of verified explanatory statements rather than generating unrestricted medical prose. Invalid model output, missing model, connection failure or timeout produces a complete rule-based explanation. The source badge identifies the route used. Live Qwen availability is not required.

## Tests

```powershell
python -m unittest discover -v
node --check static/app.js
```

Tests cover adaptive directions, missing versus zero input, completion and recovery, QUS comparability, API persistence/export, validation, offline fallback and rejection of unsupported model output. API tests use temporary storage. Node is optional and only used for the JavaScript syntax check.
