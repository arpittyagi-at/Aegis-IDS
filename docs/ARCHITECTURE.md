# AEGIS Architecture

AEGIS is a deployable intrusion detection system that combines a FastAPI inference service, a React SOC dashboard, Random Forest based detection, SHAP explanations, adaptive thresholding, SQLite audit logging, and Docker Compose orchestration.

## System Overview

```text
Network Flow / Demo Generator
          |
          v
Feature Vector -> Selector -> Scaler -> ML Model -> Adaptive Threshold
          |                                      |
          |                                      v
          |                              SHAP Explanation
          |                                      |
          v                                      v
      FastAPI REST API <------------------ Alert Record
          |
          +--> SQLite alerts.db
          |
          +--> WebSocket /stream
                    |
                    v
              React SOC Dashboard
```

## Layer Descriptions

### Data Layer

The data layer supports four benchmark families:

- NSL-KDD
- CICIoT2023
- UNSW-NB15
- CIC-IDS2017

Files are read from `datasets/`. If real datasets are unavailable, the training and demo flow can use generated traffic distributions for normal, DDoS, port scan, and mixed traffic.

### Model Layer

The model layer contains:

- `backend/ml/train.py` for training and artifact generation
- `backend/ml/predictor.py` for inference and adaptive thresholds
- `backend/ml/explainer.py` for SHAP attribution
- `backend/ml/generator.py` for synthetic traffic generation
- `backend/ml/dataset_reader.py` for dataset replay

The core training pattern is SelectKBest feature selection, StandardScaler normalization, and tree-based classification. Runtime artifacts live in `backend/artifacts/` as model, scaler, selector, and metadata files per dataset.

### Backend Layer

`backend/server.py` exposes the FastAPI service. It loads predictors at startup, initializes SQLite, serves REST endpoints, and streams live predictions over WebSocket at roughly 2Hz.

### Frontend Layer

The React dashboard in `frontend/src/` consumes REST metrics and the WebSocket stream. It displays live traffic, alert severity, model metrics, selected dataset, current threshold, and SHAP feature attribution.

## Data Flow Walkthrough

1. A user starts AEGIS with `docker-compose up --build` or runs the backend and frontend manually.
2. FastAPI startup initializes `backend/data/alerts.db`.
3. Predictors for `ciciot`, `nslkdd`, `unswnb15`, and `cicids2017` are loaded from `backend/artifacts/`.
4. The dashboard connects to `ws://localhost:8000/stream`.
5. The backend selects a sample from either `TrafficGenerator` or `DatasetReader`.
6. `Predictor.predict()` builds a full feature vector, applies selector and scaler, and computes attack probability.
7. The adaptive threshold converts probability into `is_attack` and severity.
8. If the sample is an attack, `explain_prediction()` returns top SHAP feature contributions.
9. The detection record is inserted into SQLite.
10. The WebSocket payload is sent to the dashboard.
11. The dashboard updates live charts, alert feed, and SHAP panel.

## API Endpoint Documentation

### `GET /`

Returns service status.

```json
{
  "status": "AEGIS IDS Online",
  "datasets": ["ciciot", "nslkdd", "unswnb15", "cicids2017"],
  "mode": "normal",
  "docs": "/docs"
}
```

### `GET /stats`

Returns aggregate alert statistics.

```json
{
  "total_analyzed": 1200,
  "total_attacks": 86,
  "attacks_per_min": 12,
  "avg_latency_ms": 1.7,
  "detection_rate": 7.16
}
```

### `GET /alerts?limit=50`

Returns recent alert records ordered newest first.

```json
[
  {
    "id": 47,
    "ts": 1710937123.42,
    "is_attack": 1,
    "probability": 0.96,
    "severity": "CRITICAL",
    "threshold": 0.71,
    "dataset": "ciciot",
    "latency_ms": 1.4,
    "shap_vals": {
      "syn_flag_count": {
        "value": 47,
        "shap": 0.162,
        "direction": "attack"
      }
    }
  }
]
```

### `GET /metrics?dataset=ciciot`

Returns model metrics and selected features for a dataset.

```json
{
  "dataset": "ciciot",
  "metrics": [
    {
      "model": "random_forest",
      "accuracy": 99.48,
      "f1": 99.14,
      "auc": 99.81,
      "fpr": 0.91
    }
  ],
  "selected_features": ["flow_duration", "flow_pkts_per_sec", "syn_flag_count"]
}
```

### `GET /threshold`

Returns the active adaptive threshold.

```json
{
  "current": 0.712,
  "dataset": "ciciot",
  "window_size": 100
}
```

### `GET /status`

Returns current mode, dataset, and loaded predictors.

```json
{
  "mode": "ddos",
  "dataset": "ciciot",
  "datasets_loaded": ["ciciot", "nslkdd", "unswnb15", "cicids2017"],
  "ws_clients": "active"
}
```

### `POST /predict`

Runs inference on one feature dictionary.

Request:

```json
{
  "dataset": "ciciot",
  "features": {
    "flow_pkts_per_sec": 9500,
    "syn_flag_count": 47
  }
}
```

Response:

```json
{
  "is_attack": true,
  "probability": 0.96,
  "threshold": 0.712,
  "severity": "CRITICAL",
  "latency_ms": 1.4,
  "dataset": "ciciot",
  "shap_vals": {
    "syn_flag_count": {
      "value": 47,
      "shap": 0.162,
      "direction": "attack"
    }
  }
}
```

### `POST /mode`

Sets generated traffic mode and active dataset.

Request:

```json
{
  "mode": "ddos",
  "dataset": "ciciot"
}
```

Response:

```json
{
  "mode": "ddos",
  "dataset": "ciciot"
}
```

### `GET /data-source` and `POST /data-source`

Switches between generated traffic and real dataset replay.

```json
{
  "source": "real"
}
```

Valid values are `generated` and `real`.

### `GET /docs`

FastAPI Swagger UI.

## WebSocket Message Format

Endpoint: `WS /stream`

The backend sends a JSON payload every 0.5 seconds.

```json
{
  "timestamp": 1710937123420,
  "is_attack": true,
  "probability": 0.96,
  "threshold": 0.712,
  "severity": "CRITICAL",
  "dataset": "ciciot",
  "latency_ms": 1.4,
  "shap_vals": {
    "syn_flag_count": {
      "value": 47,
      "shap": 0.162,
      "direction": "attack"
    },
    "idle_min": {
      "value": 200,
      "shap": 0.123,
      "direction": "attack"
    }
  },
  "mode": "ddos",
  "data_source": "generated",
  "pps": 9500
}
```

## Database Schema

SQLite database path: `backend/data/alerts.db`

```sql
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL,
    is_attack INTEGER,
    probability REAL,
    severity TEXT,
    threshold REAL,
    dataset TEXT,
    latency_ms REAL,
    shap_vals TEXT
);
```

Column meanings:

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Auto-incremented alert id |
| `ts` | REAL | Unix timestamp in seconds |
| `is_attack` | INTEGER | `1` for attack, `0` for normal |
| `probability` | REAL | Model attack probability |
| `severity` | TEXT | `NONE`, `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` |
| `threshold` | REAL | Adaptive threshold used for the decision |
| `dataset` | TEXT | Active dataset key |
| `latency_ms` | REAL | Inference latency in milliseconds |
| `shap_vals` | TEXT | JSON string containing feature attributions |

## Adaptive Threshold Algorithm

AEGIS tracks recent attack probabilities in a rolling window of 100 samples. The base threshold is `0.45`. Until the window has at least 20 samples, the system uses that base threshold.

After warmup:

```text
tau = min(0.88, max(0.45, mean(window) + 1.5 * std(window)))
```

Step by step:

1. Append the newest attack probability to the rolling window.
2. Compute the window mean `mu`.
3. Compute the window standard deviation `sigma`.
4. Set threshold to `mu + 1.5 * sigma`.
5. Clamp the threshold between `0.45` and `0.88`.
6. Mark the event as attack when `probability >= tau`.
7. Assign severity by confidence: `CRITICAL >= 0.95`, `HIGH >= 0.85`, `MEDIUM >= 0.70`, `LOW >= threshold`.

This raises strictness during noisy attack floods and prevents low-confidence alert storms from overwhelming the dashboard.

## SHAP Pipeline

1. Build a full feature vector in the same order used during training.
2. Replace missing, infinite, or invalid values with `0.0`.
3. Apply the trained feature selector.
4. Apply the trained scaler.
5. Load or reuse a cached `shap.TreeExplainer` for the active model.
6. Compute class-1 attack SHAP values.
7. Sort features by absolute attribution magnitude.
8. Return the top five features with raw value, SHAP value, and direction.
9. If SHAP fails, use model feature importances as a fallback attribution path.

Output shape:

```json
{
  "feature_name": {
    "value": 47,
    "shap": 0.162,
    "direction": "attack"
  }
}
```

## Docker Networking

`docker-compose.yml` starts two services:

- `backend`: builds from `backend/Dockerfile`, exposes container port `8000` as host port `8000`, and mounts `backend/artifacts` plus `backend/data`.
- `frontend`: builds from `frontend/Dockerfile`, serves the React production build through Nginx, exposes container port `80` as host port `3000`, and depends on the backend service.

Local URLs:

- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Dashboard: `http://localhost:3000`

## Extending the System

### Add a New Dataset

1. Create `datasets/<dataset-key>/`.
2. Add a loader path in `backend/ml/dataset_reader.py`.
3. Normalize raw columns into the training feature schema.
4. Update `backend/ml/train.py` to include the dataset key.
5. Train artifacts:

```bash
python -m backend.ml.train
```

6. Confirm these files exist:

```text
backend/artifacts/<dataset-key>_model.pkl
backend/artifacts/<dataset-key>_scaler.pkl
backend/artifacts/<dataset-key>_selector.pkl
backend/artifacts/<dataset-key>_meta.json
```

7. Add the key to the startup dataset list in `backend/server.py`.
8. Add a frontend dropdown option if the UI does not discover it dynamically.

### Add a New Model

1. Add the estimator to the model candidates in `backend/ml/train.py`.
2. Ensure it supports `predict_proba()` or add probability calibration.
3. Record metrics in the generated metadata.
4. Save artifacts through Joblib.
5. Update `Predictor` if the preprocessing or probability interface changes.
6. Verify `/metrics`, `/predict`, `/stream`, and SHAP/fallback explanations.
