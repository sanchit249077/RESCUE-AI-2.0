from pathlib import Path
from typing import Optional
import csv
import json
import sqlite3
import datetime as dt
import joblib
import numpy as np

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "sample_ner_risk_zones.csv"
MODEL_FILE = BASE_DIR / "ml" / "rescueai_rf.joblib"
DB_FILE = BASE_DIR / "data" / "rescueai.db"

app = FastAPI(
    title="RescueAI API",
    description="Software-first landslide risk monitoring and early-warning prototype for NER.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FEATURES = [
    "rainfall_24h_mm",
    "rainfall_7d_mm",
    "slope_deg",
    "elevation_m",
    "geology_risk",
    "landcover_change",
    "historical_risk",
]


class RiskRequest(BaseModel):
    rainfall_24h_mm: float = Field(ge=0, le=1000)
    rainfall_7d_mm: float = Field(ge=0, le=3000)
    slope_deg: float = Field(ge=0, le=90)
    elevation_m: float = Field(ge=0, le=9000)
    geology_risk: float = Field(ge=0, le=1)
    landcover_change: float = Field(ge=0, le=1)
    historical_risk: float = Field(ge=0, le=1)


def init_db():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS risk_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            risk_score REAL NOT NULL,
            risk_level TEXT NOT NULL,
            confidence REAL NOT NULL,
            inputs_json TEXT NOT NULL
        )
        """)
        conn.commit()


@app.on_event("startup")
def startup():
    init_db()


def clamp(x: float, lo=0.0, hi=1.0) -> float:
    return max(lo, min(hi, x))


def rainfall_score(r24: float, r7: float) -> float:
    short_term = clamp(r24 / 220.0)
    cumulative = clamp(r7 / 700.0)
    return 0.65 * short_term + 0.35 * cumulative


def slope_score(slope: float) -> float:
    return clamp((slope - 15.0) / 35.0)


def elevation_score(elevation: float) -> float:
    return clamp((elevation - 300.0) / 2200.0)


def baseline_engine(req: RiskRequest):
    factors = {
        "rainfall": rainfall_score(req.rainfall_24h_mm, req.rainfall_7d_mm),
        "slope": slope_score(req.slope_deg),
        "elevation": elevation_score(req.elevation_m),
        "geology": req.geology_risk,
        "landcover_change": req.landcover_change,
        "historical_risk": req.historical_risk,
    }
    weights = {
        "rainfall": 0.32,
        "slope": 0.20,
        "elevation": 0.08,
        "geology": 0.16,
        "landcover_change": 0.10,
        "historical_risk": 0.14,
    }
    score = 100 * sum(factors[k] * weights[k] for k in factors)
    level = "CRITICAL" if score >= 80 else "HIGH" if score >= 60 else "MODERATE" if score >= 35 else "LOW"
    spread = sum(abs(v - 0.5) for v in factors.values()) / len(factors)
    confidence = clamp(0.70 + 0.25 * spread) * 100
    top = sorted(
        ((k, factors[k] * weights[k]) for k in factors),
        key=lambda x: x[1],
        reverse=True
    )[:3]
    return {
        "risk_score": round(score, 1),
        "risk_level": level,
        "confidence": round(confidence, 1),
        "factors": {k: round(v, 3) for k, v in factors.items()},
        "top_contributors": [
            {"factor": k, "contribution": round(v * 100, 1)}
            for k, v in top
        ],
        "engine": "explainable_baseline_v0.2",
    }


def load_model():
    if not MODEL_FILE.exists():
        return None
    try:
        return joblib.load(MODEL_FILE)
    except Exception:
        return None


def ml_predict(req: RiskRequest):
    model = load_model()
    if model is None:
        return None
    x = np.array([[getattr(req, f) for f in FEATURES]], dtype=float)
    prob = float(model.predict_proba(x)[0, 1])
    score = 100 * prob
    level = "CRITICAL" if score >= 80 else "HIGH" if score >= 60 else "MODERATE" if score >= 35 else "LOW"
    return {
        "risk_score": round(score, 1),
        "risk_level": level,
        "confidence": round(max(prob, 1 - prob) * 100, 1),
        "engine": "random_forest_prototype_v0.2",
        "warning": "Model is trained on synthetic development data; do not use for operational decisions."
    }


def save_event(result, req):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO risk_events(created_at, risk_score, risk_level, confidence, inputs_json) VALUES(?,?,?,?,?)",
            (
                dt.datetime.now(dt.timezone.utc).isoformat(),
                result["risk_score"],
                result["risk_level"],
                result["confidence"],
                req.model_dump_json(),
            ),
        )
        conn.commit()


def load_zones():
    rows = []
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "id": r["id"], "location": r["location"], "state": r["state"],
                "lat": float(r["lat"]), "lon": float(r["lon"]),
                "risk_score": float(r["risk_score"]), "risk_level": r["risk_level"],
                "vulnerable_villages": int(r["vulnerable_villages"]),
                "road_risk": float(r["road_risk"]), "confidence": float(r["confidence"]),
            })
    return rows


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "RescueAI",
        "version": app.version,
        "ml_model_available": MODEL_FILE.exists(),
    }


@app.get("/api/sources")
def sources():
    return {
        "sources": [
            {"name": "GSI Bhusanket", "purpose": "Landslide inventory and susceptibility resources",
             "url": "https://bhusanket.gsi.gov.in/"},
            {"name": "ISRO Bhuvan", "purpose": "Landslide, land-cover and geospatial layers",
             "url": "https://bhuvan-app1.nrsc.gov.in/bhuvan2d/bhuvan/bhuvan2d.php"},
            {"name": "Bhuvan IMD Weather Products", "purpose": "Weather and soil-moisture products",
             "url": "https://bhuvan-app1.nrsc.gov.in/imd/"},
            {"name": "OpenStreetMap", "purpose": "Roads, settlements and routing base layers",
             "url": "https://www.openstreetmap.org/"},
        ]
    }


@app.get("/api/risk-summary")
def risk_summary():
    zones = load_zones()
    counts = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
    for z in zones:
        counts[z["risk_level"]] += 1
    return {
        "total_zones": len(zones),
        "levels": counts,
        "critical": sorted(zones, key=lambda x: x["risk_score"], reverse=True)[:5],
    }


@app.get("/api/zones")
def zones(
    state: Optional[str] = Query(default=None),
    min_score: float = Query(default=0, ge=0, le=100),
):
    data = load_zones()
    if state:
        data = [z for z in data if z["state"].lower() == state.lower()]
    return [z for z in data if z["risk_score"] >= min_score]


@app.post("/api/risk-score")
def calculate_risk(req: RiskRequest):
    result = baseline_engine(req)
    save_event(result, req)
    return result


@app.post("/api/ml-predict")
def ml_risk(req: RiskRequest):
    result = ml_predict(req)
    if result is None:
        raise HTTPException(status_code=503, detail="Prototype ML model not trained. Run python ml/train_model.py first.")
    save_event(result, req)
    return result


@app.get("/api/history")
def history(limit: int = Query(default=20, ge=1, le=200)):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute(
            "SELECT id, created_at, risk_score, risk_level, confidence FROM risk_events ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = [
            {"id": r[0], "created_at": r[1], "risk_score": r[2], "risk_level": r[3], "confidence": r[4]}
            for r in cur.fetchall()
        ]
    return rows


@app.get("/api/alerts")
def alerts():
    data = load_zones()
    out = []
    for z in sorted(data, key=lambda x: x["risk_score"], reverse=True):
        if z["risk_score"] >= 80:
            out.append({
                "severity": "CRITICAL",
                "location": z["location"],
                "state": z["state"],
                "message": "Immediate review recommended: high landslide risk and exposed road/village assets.",
                "risk_score": z["risk_score"],
                "recommended_actions": [
                    "Issue targeted public warning",
                    "Review road access and alternate routes",
                    "Check shelter readiness",
                ],
            })
    return out[:10]
