#!/usr/bin/env python3
"""
node_wnba_engine/serve.py

HTTP inference API for the WNBA engine — a thin FastAPI wrapper around
``model.predict.predict``. This is the web process for the Railway "inference
API" service: it binds to ``$PORT`` and exposes the model's moneyline/totals
predictions over JSON.

Run locally:
    uvicorn serve:app --reload --port 8000

Run in a container (Railway / Docker):
    uvicorn serve:app --host 0.0.0.0 --port ${PORT:-8000}

Endpoints:
    GET  /            -> service banner + loaded model versions
    GET  /health      -> liveness/readiness probe
    POST /predict     -> body: PredictRequest (see below)
    GET  /predict     -> same, via query params (?home=...&away=...)

The model artifacts (.pkl) and the DuckDB feature store must be present.
Override the DB location with WNBA_DB_PATH (e.g. a mounted Railway volume).
"""

from __future__ import annotations

import os
import pathlib
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

_ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

from model.predict import predict  # noqa: E402
from model.stack_train import load_latest_model  # noqa: E402

app = FastAPI(
    title="WNBA Ensemble Inference API",
    version="1.0.0",
    description="Moneyline + totals predictions from the WNBA ensemble model.",
)


class PredictRequest(BaseModel):
    home: str = Field(..., description="Home team name (fuzzy matched)")
    away: str = Field(..., description="Away team name (fuzzy matched)")
    ml_home: Optional[float] = Field(None, description="Decimal odds: home win")
    ml_away: Optional[float] = Field(None, description="Decimal odds: away win")
    total_line: Optional[float] = Field(None, description="Total points line")
    over_odds: Optional[float] = Field(None, description="Decimal odds: over")
    under_odds: Optional[float] = Field(None, description="Decimal odds: under")


def _model_versions() -> dict:
    versions = {}
    for target in ("moneyline", "totals"):
        try:
            meta = load_latest_model(target)
            versions[target] = {
                "version": meta.get("version"),
                "auc": meta.get("auc_test"),
            }
        except FileNotFoundError:
            versions[target] = None
    return versions


@app.get("/")
def root() -> dict:
    return {
        "service": "wnba-ensemble-inference",
        "status": "ok",
        "db_path": os.getenv("WNBA_DB_PATH", str(_ROOT / "db" / "wnba.duckdb")),
        "models": _model_versions(),
    }


@app.get("/health")
def health() -> dict:
    """Readiness probe: 200 only if at least the moneyline model loads."""
    try:
        load_latest_model("moneyline")
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"model not loaded: {e}")
    return {"status": "healthy"}


def _run(req: PredictRequest) -> dict:
    try:
        result = predict(
            home_team=req.home,
            away_team=req.away,
            ml_home=req.ml_home,
            ml_away=req.ml_away,
            total_line=req.total_line,
            over_odds=req.over_odds,
            under_odds=req.under_odds,
        )
    except FileNotFoundError as e:
        # No trained model on disk.
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:  # noqa: BLE001 - surface DB/feature errors as 400
        raise HTTPException(status_code=400, detail=f"prediction failed: {e}")

    if "error_ml" in result:
        raise HTTPException(status_code=503, detail=result["error_ml"])
    return {"home": req.home, "away": req.away, **result}


@app.post("/predict")
def predict_post(req: PredictRequest) -> dict:
    return _run(req)


@app.get("/predict")
def predict_get(
    home: str,
    away: str,
    ml_home: Optional[float] = None,
    ml_away: Optional[float] = None,
    total_line: Optional[float] = None,
    over_odds: Optional[float] = None,
    under_odds: Optional[float] = None,
) -> dict:
    return _run(
        PredictRequest(
            home=home,
            away=away,
            ml_home=ml_home,
            ml_away=ml_away,
            total_line=total_line,
            over_odds=over_odds,
            under_odds=under_odds,
        )
    )
