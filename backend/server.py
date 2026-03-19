import asyncio
import json
import os
import sys
import time
import warnings
from typing import Any, Dict, Optional

# Suppress sklearn feature-name warnings that crash the async WS event loop
warnings.filterwarnings("ignore", message="X does not have valid feature names")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from backend.data.database import init_db, insert, recent_alerts, stats
from backend.ml.explainer import explain_prediction
from backend.ml.generator import TrafficGenerator
from backend.ml.predictor import Predictor

app = FastAPI(title="AEGIS IDS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictors: dict = {}
active_dataset: str = "ciciot"
traffic_mode: str = "normal"
generator = TrafficGenerator()


class PredictRequest(BaseModel):
    features: Dict[str, Any]
    dataset: Optional[str] = "ciciot"


class ModeRequest(BaseModel):
    mode: str
    dataset: Optional[str] = "ciciot"


@app.on_event("startup")
def startup_event():
    init_db()

    for ds in ["ciciot", "nslkdd"]:
        try:
            predictors[ds] = Predictor(ds)
            print(f"Loaded {ds}")
        except Exception as e:
            print(f"Could not load {ds}: {e}")

    print("AEGIS API ready - visit http://127.0.0.1:8000/docs")


@app.get("/")
def root():
    return {
        "status": "AEGIS IDS Online",
        "datasets": list(predictors.keys()),
        "mode": traffic_mode,
        "docs": "/docs",
    }


@app.get("/stats")
def get_stats():
    return stats()


@app.get("/alerts")
def get_alerts(limit: int = 50):
    return recent_alerts(limit)



@app.get("/metrics")
def get_metrics(dataset: str = "ciciot"):
    ds = dataset.lower()
    if ds not in predictors:
        raise HTTPException(status_code=404, detail="Dataset not found")
    predictor = predictors[ds]
    return {
        "dataset": ds,
        "metrics": predictor.get_metrics(),
        "selected_features": predictor.feature_names,
    }


@app.get("/threshold")
def get_threshold():
    predictor = predictors.get(active_dataset)
    if not predictor:
        return {"error": "no predictor loaded"}, 500
    return {
        "current": predictor._threshold(),
        "dataset": active_dataset,
        "window_size": len(predictor._window),
    }


@app.get("/status")
def get_status():
    return {
        "mode": traffic_mode,
        "dataset": active_dataset,
        "datasets_loaded": list(predictors.keys()),
        "ws_clients": "active",
    }


@app.post("/predict")
def predict(req: PredictRequest):
    global active_dataset

    ds = (req.dataset or active_dataset).lower()
    predictor = predictors.get(ds) or predictors.get(active_dataset)

    if not predictor:
        return {"error": "predictor not available"}, 500

    result = predictor.predict(req.features)

    shap_vals: Dict[str, Any] = {}
    if result.get("is_attack"):
        try:
            shap_vals = explain_prediction(predictor, req.features)
        except Exception:
            shap_vals = {}

    record = {
        **result,
        "timestamp": time.time(),
        "shap_vals": shap_vals,
    }
    insert(record)

    return {**result, "shap_vals": shap_vals}


@app.post("/mode")
def set_mode(req: ModeRequest):
    global traffic_mode, active_dataset

    traffic_mode = req.mode
    active_dataset = (req.dataset or active_dataset).lower()
    return {"mode": traffic_mode, "dataset": active_dataset}


@app.websocket("/stream")
async def websocket_stream(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            try:
                sample = generator.next_sample(traffic_mode)
                predictor = predictors.get(active_dataset)
                if not predictor:
                    await asyncio.sleep(0.5)
                    continue

                result = predictor.predict(sample)

                shap_vals: Dict[str, Any] = {}
                if result.get("is_attack"):
                    try:
                        shap_vals = explain_prediction(predictor, sample)
                    except Exception:
                        shap_vals = {}

                record = {**result, "timestamp": time.time(), "shap_vals": shap_vals}
                insert(record)

                payload = {
                    "timestamp": float(record["timestamp"]),
                    "is_attack": bool(result["is_attack"]),
                    "probability": float(result["probability"]),
                    "threshold": float(result["threshold"]),
                    "severity": str(result["severity"]),
                    "dataset": str(result["dataset"]),
                    "latency_ms": float(result["latency_ms"]),
                    "shap_vals": shap_vals,
                    "mode": traffic_mode,
                    "pps": int(generator.pps(traffic_mode)),
                }
                await ws.send_text(json.dumps(payload))
            except WebSocketDisconnect:
                raise
            except Exception as e:
                print(f"Stream loop error (continuing): {e}")
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        print("Client disconnected")



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.server:app", host="127.0.0.1", port=8000, reload=True)
