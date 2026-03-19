import json
import os
from functools import partial
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


FEATURES = [
    "flow_duration",
    "total_fwd_packets",
    "total_bwd_packets",
    "total_length_fwd_pkts",
    "total_length_bwd_pkts",
    "fwd_pkt_len_max",
    "fwd_pkt_len_min",
    "fwd_pkt_len_mean",
    "fwd_pkt_len_std",
    "bwd_pkt_len_max",
    "bwd_pkt_len_min",
    "bwd_pkt_len_mean",
    "bwd_pkt_len_std",
    "flow_bytes_per_sec",
    "flow_pkts_per_sec",
    "flow_iat_mean",
    "flow_iat_std",
    "flow_iat_max",
    "flow_iat_min",
    "fwd_iat_total",
    "fwd_iat_mean",
    "fwd_iat_std",
    "fwd_iat_max",
    "fwd_iat_min",
    "bwd_iat_total",
    "bwd_iat_mean",
    "bwd_iat_std",
    "bwd_iat_max",
    "fwd_psh_flags",
    "bwd_psh_flags",
    "fwd_urg_flags",
    "bwd_urg_flags",
    "fwd_header_length",
    "bwd_header_length",
    "fwd_packets_per_sec",
    "bwd_packets_per_sec",
    "min_packet_length",
    "max_packet_length",
    "packet_length_mean",
    "packet_length_std",
    "packet_length_variance",
    "fin_flag_count",
    "syn_flag_count",
    "rst_flag_count",
    "psh_flag_count",
    "ack_flag_count",
    "urg_flag_count",
    "down_up_ratio",
    "average_packet_size",
    "avg_fwd_segment_size",
    "avg_bwd_segment_size",
    "init_win_bytes_forward",
    "init_win_bytes_backward",
    "act_data_pkt_fwd",
    "min_seg_size_forward",
    "active_mean",
    "active_std",
    "active_max",
    "active_min",
    "idle_mean",
    "idle_std",
    "idle_max",
    "idle_min",
]


def _clip_int(arr, min_v=None, max_v=None):
    if min_v is not None:
        arr = np.maximum(arr, min_v)
    if max_v is not None:
        arr = np.minimum(arr, max_v)
    return np.rint(arr).astype(int)


def _norm(  # noqa: PLR0913
    rng,
    size,
    mean,
    std,
    min_val: float = 0.0,
    max_val: float | None = None,
    as_int: bool = False,
    clip_min: float | None = None,
    clip_max: float | None = None,
):
    out = rng.normal(loc=mean, scale=std, size=size)
    if as_int:
        out = np.rint(out)
    if clip_min is not None:
        out = np.maximum(out, clip_min)
    if clip_max is not None:
        out = np.minimum(out, clip_max)
    # ensure positive where it makes sense
    if min_val is not None:
        out = np.maximum(out, min_val)
    return out


def generate_synthetic_dataset(name: str, random_state: int = 42) -> pd.DataFrame:
    """Generate synthetic dataset with FIXED feature set and labels."""

    rng = np.random.default_rng(random_state)
    n_normal = 40000
    n_attack = 20000
    # attack split
    n_ddos = 10000
    n_portscan = 10000

    # --------- distributions ---------
    normal_dist = {
        "flow_duration": (50000, 20000),
        "total_fwd_packets": (8, 4),
        "total_bwd_packets": (6, 3),
        "flow_bytes_per_sec": (15000, 5000),
        "flow_pkts_per_sec": (120, 50),
        "flow_iat_mean": (5000, 2000),
        "fwd_iat_total": (40000, 15000),
        "bwd_iat_total": (35000, 12000),
        "syn_flag_count": (1, 0.3),
        "max_packet_length": (1400, 200),
        "init_win_bytes_forward": (65535, 15000),
        "idle_mean": (200000, 80000),
        "idle_std": (50000, 20000),
        "idle_max": (400000, 100000),
        "idle_min": (50000, 20000),
        "active_mean": (50000, 20000),
        "active_max": (90000, 25000),
    }

    ddos_dist = {
        "flow_duration": (3000, 1500),
        "total_fwd_packets": (250, 100),
        "total_bwd_packets": (3, 2),
        "flow_bytes_per_sec": (950000, 200000),
        "flow_pkts_per_sec": (9500, 3000),
        "flow_iat_mean": (60, 25),
        "fwd_iat_total": (800, 300),
        "bwd_iat_total": (300, 120),
        "syn_flag_count": (47, 15),
        "max_packet_length": (80, 15),
        "init_win_bytes_forward": (512, 100),
        "idle_mean": (1000, 400),
        "idle_std": (300, 120),
        "idle_max": (2000, 800),
        "idle_min": (200, 80),
        "active_mean": (2000, 800),
        "active_max": (4000, 1500),
    }

    portscan_dist = {
        "flow_pkts_per_sec": (600, 200),
        "flow_bytes_per_sec": (3000, 1000),
        "total_fwd_packets": (2, 1),
        "total_bwd_packets": (1, 0.5),
        "syn_flag_count": (12, 5),
        "rst_flag_count": (8, 3),
        "init_win_bytes_backward": (0, 1),
    }

    def _make_block(n, dist, label):
        data = {feat: np.zeros(n, dtype=float) for feat in FEATURES}

        # Fill common features with fallback normal distributions
        for feat in FEATURES:
            if feat in dist:
                mean, std = dist[feat]
            else:
                # default values per traffic type
                if label == 0:
                    mean, std = 1000.0, 400.0
                else:
                    # for attacks -> shorter, bursty
                    mean, std = 500.0, 300.0

            # special handling for some features
            if feat == "total_fwd_packets":
                arr = _norm(
                    rng,
                    n,
                    mean,
                    std,
                    as_int=True,
                    clip_min=1,
                    min_val=1,
                )
                # allow smaller for port scan and normal
                if label == 1 and name == "nslkdd":
                    arr = _clip_int(arr, 1)
                data[feat] = arr
                continue

            if feat == "total_bwd_packets":
                clip_min = 0
                clip_max = 2 if label == 1 and dist is portscan_dist else None
                arr = _norm(
                    rng,
                    n,
                    mean,
                    std,
                    as_int=True,
                    clip_min=clip_min,
                    clip_max=clip_max,
                    min_val=0,
                )
                data[feat] = arr
                continue

            if feat in ("syn_flag_count", "rst_flag_count", "fin_flag_count", "psh_flag_count", "ack_flag_count", "urg_flag_count"):
                # flags are counts, small integers
                if feat in dist:
                    fmean, fstd = dist[feat]
                else:
                    # heuristics
                    if label == 0:
                        fmean, fstd = 0.4, 0.2
                    else:
                        fmean, fstd = 5.0, 3.0
                arr = _norm(
                    rng,
                    n,
                    fmean,
                    fstd,
                    as_int=True,
                    clip_min=0,
                )
                data[feat] = arr
                continue

            if feat in ("fwd_psh_flags", "bwd_psh_flags", "fwd_urg_flags", "bwd_urg_flags"):
                # binary-ish, but can be counts
                mean, std = dist.get(feat, (0.2 if label == 0 else 0.6, 0.1))
                arr = _norm(
                    rng,
                    n,
                    mean,
                    std,
                    as_int=True,
                    clip_min=0,
                )
                data[feat] = arr
                continue

            if feat in ("fwd_header_length", "bwd_header_length"):
                mean_val = dist.get(feat, (60, 10))[0]
                std_val = dist.get(feat, (10, 5))[1]
                arr = _norm(rng, n, mean_val, std_val, min_val=20)
                data[feat] = arr
                continue

            if feat == "flow_iat_std" or feat == "fwd_iat_std" or feat == "bwd_iat_std":
                # variability of inter-arrival times
                mean_val = dist.get(feat, (1000, 500))[0]
                std_val = dist.get(feat, (1000, 500))[1]
                data[feat] = _norm(rng, n, mean_val, std_val, min_val=0)
                continue

            if feat == "flow_iat_max" or feat == "flow_iat_min" or feat == "fwd_iat_max" or feat == "fwd_iat_min" or feat == "bwd_iat_max" or feat == "bwd_iat_min":
                # boundaries for IAT
                data[feat] = _norm(rng, n, mean * 1.1, std * 0.5, min_val=0)
                continue

            if feat == "total_length_fwd_pkts":
                # relate to packet counts and max length
                mean_val = dist.get(feat, (mean * 1000, std * 400))[0]
                std_val = dist.get(feat, (mean * 1000, std * 400))[1]
                data[feat] = _norm(rng, n, mean_val, std_val, min_val=0)
                continue

            if feat == "total_length_bwd_pkts":
                mean_val = dist.get(feat, (mean * 800, std * 300))[0]
                std_val = dist.get(feat, (mean * 800, std * 300))[1]
                data[feat] = _norm(rng, n, mean_val, std_val, min_val=0)
                continue

            if feat == "fwd_pkt_len_max" or feat == "bwd_pkt_len_max":
                mean_val = dist.get(feat, (mean * 0.8, std * 0.8))[0]
                std_val = dist.get(feat, (mean * 0.25, std * 0.25))[1]
                data[feat] = _norm(rng, n, mean_val, std_val, min_val=20)
                continue

            if feat == "fwd_pkt_len_min" or feat == "bwd_pkt_len_min":
                mean_val = dist.get(feat, (mean * 0.2, std * 0.2))[0]
                std_val = dist.get(feat, (std * 0.1, std * 0.1))[1]
                data[feat] = _norm(rng, n, mean_val, std_val, min_val=10)
                continue

            if feat == "fwd_pkt_len_mean" or feat == "bwd_pkt_len_mean":
                mean_val = dist.get(feat, (mean * 0.5, std * 0.3))[0]
                std_val = dist.get(feat, (std * 0.2, std * 0.2))[1]
                data[feat] = _norm(rng, n, mean_val, std_val, min_val=10)
                continue

            if feat == "fwd_pkt_len_std" or feat == "bwd_pkt_len_std":
                mean_val = dist.get(feat, (std * 0.5, std * 0.3))[0]
                std_val = dist.get(feat, (std * 0.2, std * 0.2))[1]
                data[feat] = _norm(rng, n, mean_val, std_val, min_val=0)
                continue

            if feat == "fwd_packets_per_sec" or feat == "bwd_packets_per_sec":
                # relate to flow_pkts_per_sec
                base = dist.get("flow_pkts_per_sec", (100, 50))[0]
                data[feat] = _norm(rng, n, base * 0.8, base * 0.25, min_val=0)
                continue

            if feat in ("min_packet_length", "packet_length_mean"):  # keep correlated with max
                base = dist.get("max_packet_length", (1500, 300))[0] * 0.4
                data[feat] = _norm(rng, n, base, base * 0.3, min_val=10)
                continue

            if feat == "packet_length_std":
                data[feat] = _norm(rng, n, 200, 80, min_val=0)
                continue

            if feat == "packet_length_variance":
                arr = data.get("packet_length_std", np.zeros(n))
                data[feat] = np.square(arr)
                continue

            if feat == "down_up_ratio":
                data[feat] = _norm(rng, n, 1.0 if label == 0 else 5.0, 1.0, min_val=0.01)
                continue

            if feat == "average_packet_size":
                data[feat] = _norm(rng, n, 500, 200, min_val=20)
                continue

            if feat == "avg_fwd_segment_size" or feat == "avg_bwd_segment_size":
                data[feat] = _norm(rng, n, 1000, 400, min_val=20)
                continue

            if feat == "init_win_bytes_backward":
                mean_val = dist.get(feat, (1000, 500))[0]
                std_val = dist.get(feat, (500, 200))[1]
                data[feat] = _norm(rng, n, mean_val, std_val, min_val=0)
                continue

            if feat == "act_data_pkt_fwd":
                data[feat] = _norm(rng, n, 200, 80, min_val=0)
                continue

            if feat == "min_seg_size_forward":
                data[feat] = _norm(rng, n, 200, 60, min_val=0)
                continue

            # fallback for any remaining feature
            data[feat] = _norm(rng, n, mean, std, min_val=0)

        df = pd.DataFrame(data)
        df["label"] = label
        return df

    normal_df = _make_block(n_normal, normal_dist, label=0)
    ddos_df = _make_block(n_ddos, ddos_dist, label=1)
    portscan_df = _make_block(n_portscan, portscan_dist, label=1)

    df = pd.concat([normal_df, ddos_df, portscan_df], ignore_index=True)
    df = df.sample(frac=1, random_state=random_state).reset_index(drop=True)
    return df


def run_pipeline(dataset_name: str):
    artifact_dir = Path("backend") / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    df = generate_synthetic_dataset(dataset_name, random_state=42)
    X = df[FEATURES].copy()
    y = df["label"].copy()

    # sanitize
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median())

    mi_func = partial(
        mutual_info_classif,
        n_neighbors=3,
        random_state=42,
        n_jobs=1,
    )
    selector = SelectKBest(mi_func, k=20)

    # Fit selector on a sample to keep computation tractable while still using mutual_info
    rng = np.random.default_rng(42)
    sample_n = min(20000, len(X))
    sample_idx = rng.choice(len(X), size=sample_n, replace=False)
    X_sample = X.iloc[sample_idx]
    y_sample = y.iloc[sample_idx]

    selector.fit(X_sample, y_sample)
    X_sel = selector.transform(X)
    selected_features = [FEATURES[i] for i in selector.get_support(indices=True)]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_sel)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    models = {
        "random_forest": RandomForestClassifier(
            n_estimators=100, max_depth=15, n_jobs=-1, random_state=42
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42
        ),
        "decision_tree": DecisionTreeClassifier(max_depth=12, random_state=42),
    }

    results = []
    best_model_name = None
    best_f1 = -1.0
    best_model = None

    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

        acc = accuracy_score(y_test, preds) * 100.0
        f1 = f1_score(y_test, preds) * 100.0
        prec = precision_score(y_test, preds) * 100.0
        rec = recall_score(y_test, preds) * 100.0
        auc = roc_auc_score(y_test, probs) * 100.0 if probs is not None else 0.0
        tn, fp, fn, tp = confusion_matrix(y_test, preds).ravel()
        fpr = (fp / (fp + tn)) * 100.0 if (fp + tn) > 0 else 0.0

        results.append(
            {
                "model": name,
                "accuracy": round(acc, 2),
                "f1": round(f1, 2),
                "precision": round(prec, 2),
                "recall": round(rec, 2),
                "auc": round(auc, 2),
                "fpr": round(fpr, 2),
            }
        )

        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model = model

    # save artifacts
    meta = {
        "dataset": dataset_name,
        "selected_features": selected_features,
        "n_features": len(selected_features),
        "best_model": best_model_name,
        "metrics": results,
    }

    prefix = dataset_name.lower()
    joblib.dump(best_model, artifact_dir / f"{prefix}_model.pkl")
    joblib.dump(scaler, artifact_dir / f"{prefix}_scaler.pkl")
    joblib.dump(selector, artifact_dir / f"{prefix}_selector.pkl")

    with open(artifact_dir / f"{prefix}_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


if __name__ == "__main__":
    for ds in ["ciciot", "nslkdd"]:
        print(f"\nTraining {ds}...")
        try:
            run_pipeline(ds)
        except Exception as e:
            print(f"Error during training {ds}: {e}")
            raise
    print("\nTraining complete. Artifacts in backend/artifacts/")
