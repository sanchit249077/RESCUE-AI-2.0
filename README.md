# RescueAI v0.2
## AI-Based Early Warning & Landslide Risk Monitoring System in NER
### Quantum Minds — software-first project

RescueAI is a local, software-only prototype for monitoring landslide risk and generating early-warning decision support for the North Eastern Region.

## What is working now
- FastAPI REST backend
- Explainable baseline risk engine
- Optional Random Forest prototype model
- SQLite risk-history storage
- NER map dashboard
- Risk calculator
- Alerts endpoint
- Source registry endpoint
- API smoke tests
- Training pipeline separated from the API

## Important scientific boundary
The included ML training script uses **synthetic development labels** only. Its metrics must not be treated as real landslide-prediction performance. The next stage is to ingest validated NER landslide inventory and environmental features, then evaluate with leakage-safe spatial/temporal validation.

## Start

### Backend
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

### Train the prototype ML model
In another terminal:
```powershell
cd ml
python train_model.py
```

### Frontend
```powershell
cd frontend
python -m http.server 5500
```

Open `http://127.0.0.1:5500`

### API
`http://127.0.0.1:8000/docs`

## Real-data phase
The code is designed to move to validated sources. The current official source targets include:
- GSI Bhusanket: landslide inventory/susceptibility resources
- ISRO Bhuvan: landslide and geospatial layers
- Bhuvan IMD products: weather-related layers

Do not claim operational warnings from the prototype without field/agency validation.

## Recommended next implementation
1. Download and normalize GSI field-validated landslide inventory.
2. Build NER terrain features from DEM.
3. Join rainfall histories and forecasts.
4. Build event/non-event training samples.
5. Train RF/XGBoost baseline.
6. Calibrate probabilities.
7. Add spatial cross-validation by district.
8. Add live ingestion jobs and alert policy.


## Current development stage: Stage 4
We are now moving the MVP from synthetic/demo risk zones toward a real Sikkim geospatial dataset.

Run:
```bash
python ml/download_sikkim_inventory.py
python ml/inspect_sikkim_inventory.py
```

Then normalize and build the spatial grid using `docs/STAGE_4_SIKKIM_REAL_DATA.md`.

The real-data pipeline intentionally separates:
- susceptibility features
- trigger/time-series features
- exposure
- model target

This avoids treating a static landslide inventory as a complete early-warning model.
