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
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier


# -- REAL DATASET LOADERS ---------------------------------------------------

NSL_KDD_COLS = [
    "duration",
    "protocol_type",
    "service",
    "flag",
    "src_bytes",
    "dst_bytes",
    "land",
    "wrong_fragment",
    "urgent",
    "hot",
    "num_failed_logins",
    "logged_in",
    "num_compromised",
    "root_shell",
    "su_attempted",
    "num_root",
    "num_file_creations",
    "num_shells",
    "num_access_files",
    "num_outbound_cmds",
    "is_host_login",
    "is_guest_login",
    "count",
    "srv_count",
    "serror_rate",
    "srv_serror_rate",
    "rerror_rate",
    "srv_rerror_rate",
    "same_srv_rate",
    "diff_srv_rate",
    "srv_diff_host_rate",
    "dst_host_count",
    "dst_host_srv_count",
    "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate",
    "dst_host_srv_serror_rate",
    "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate",
    "label",
    "difficulty",
]


def load_nslkdd(path="datasets/nslkdd"):
    print("  Loading NSL-KDD...")
    train = pd.read_csv(f"{path}/KDDTrain+.txt", names=NSL_KDD_COLS)
    test = pd.read_csv(f"{path}/KDDTest+.txt", names=NSL_KDD_COLS)
    df = pd.concat([train, test], ignore_index=True)
    df = df.drop(columns=["difficulty"], errors="ignore")

    for col in ["protocol_type", "service", "flag"]:
        df[col] = LabelEncoder().fit_transform(df[col].astype(str))

    df["label"] = (df["label"] != "normal").astype(int)
    print(f"    Shape: {df.shape}, Attack rate: {df['label'].mean():.1%}")
    return df


def load_ciciot(path="datasets/ciciot/CICIoT2023.csv"):
    print("  Loading CICIoT2023...")
    df = pd.read_csv(path, low_memory=False)

    label_col = [c for c in df.columns if "label" in c.lower() or "class" in c.lower()][-1]
    df["label"] = (df[label_col] != "BenignTraffic").astype(int)
    df = df.drop(columns=[label_col], errors="ignore")

    drop = [c for c in df.columns if any(x in c.lower() for x in ["ip", "mac", "time", "id"])]
    df = df.drop(columns=drop, errors="ignore")

    if len(df) > 80_000:
        df = df.sample(80_000, random_state=42)
        print("    Sampled to 80k rows")

    print(f"    Shape: {df.shape}, Attack rate: {df['label'].mean():.1%}")
    return df


def load_unswnb15(path="datasets/unswnb15"):
    print("  Loading UNSW-NB15...")
    import glob

    # Prefer canonical split files to avoid mixing alternate schemas.
    data_files = [
        f
        for f in sorted(glob.glob(f"{path}/UNSW-NB15_*.csv"))
        if "list_events" not in os.path.basename(f).lower()
    ]
    if not data_files:
        files = glob.glob(f"{path}/*.csv")
        data_files = [
            f
            for f in files
            if "features" not in f.lower() and "gt" not in f.lower() and "list" not in f.lower()
        ]

    dfs = []
    target_rows = 20_000
    per_file = max(1, target_rows // max(1, len(data_files)))

    for f in sorted(data_files):
        try:
            loaded_for_file = 0
            for chunk in pd.read_csv(f, low_memory=False, header=None, chunksize=100_000):
                remaining = per_file - loaded_for_file
                if remaining <= 0:
                    break

                if len(chunk) > remaining:
                    chunk = chunk.sample(remaining, random_state=42)

                loaded_for_file += len(chunk)
                dfs.append(chunk)

                if loaded_for_file >= per_file:
                    break

            print(f"    Loaded {f}: {loaded_for_file} sampled rows")
        except Exception as e:
            print(f"    Skipping {f}: {e}")

    if not dfs:
        raise ValueError("No usable UNSW-NB15 CSV files were loaded")

    df = pd.concat(dfs, ignore_index=True)

    df.columns = [f"f{i}" for i in range(df.shape[1] - 1)] + ["label"]
    df["label"] = pd.to_numeric(df["label"], errors="coerce").fillna(0).astype(int)

    for col in df.select_dtypes(include="object").columns:
        if col != "label":
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))

    if len(df) > 80_000:
        df = df.sample(80_000, random_state=42)

    print(f"    Shape: {df.shape}, Attack rate: {df['label'].mean():.1%}")
    return df


def load_cicids2017(path="datasets/cicids2017"):
    print("  Loading CIC-IDS2017...")
    import glob

    files = glob.glob(f"{path}/*.csv")

    dfs = []
    target_rows = 20_000
    per_file = max(1, target_rows // max(1, len(files)))

    for f in sorted(files):
        try:
            attacks_needed = max(1, per_file // 3)
            benign_needed = per_file - attacks_needed
            sampled_parts = []

            for chunk in pd.read_csv(f, low_memory=False, chunksize=50_000):
                label_candidates = [c for c in chunk.columns if "label" in c.lower()]
                if not label_candidates:
                    continue

                label_col = label_candidates[0]
                labels = chunk[label_col].astype(str).str.strip().str.upper()

                if attacks_needed > 0:
                    atk = chunk[labels != "BENIGN"]
                    if not atk.empty:
                        take = min(attacks_needed, len(atk))
                        sampled_parts.append(atk.sample(take, random_state=42))
                        attacks_needed -= take

                if benign_needed > 0:
                    ben = chunk[labels == "BENIGN"]
                    if not ben.empty:
                        take = min(benign_needed, len(ben))
                        sampled_parts.append(ben.sample(take, random_state=42))
                        benign_needed -= take

                if attacks_needed <= 0 and benign_needed <= 0:
                    break

            if not sampled_parts:
                print(f"    Skipping {f}: no usable rows")
                continue

            chunk = pd.concat(sampled_parts, ignore_index=True)
            label_col = [c for c in chunk.columns if "label" in c.lower()][0]
            chunk["label"] = (chunk[label_col].astype(str).str.strip().str.upper() != "BENIGN").astype(int)
            chunk = chunk.drop(columns=[label_col])

            chunk.columns = chunk.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")

            for col in chunk.select_dtypes(include="object").columns:
                chunk[col] = LabelEncoder().fit_transform(chunk[col].astype(str))

            dfs.append(chunk)
            print(f"    Loaded {f}: {len(chunk)} sampled rows")
        except Exception as e:
            print(f"    Skipping {f}: {e}")

    if not dfs:
        raise ValueError("No usable CIC-IDS2017 CSV files were loaded")

    df = pd.concat(dfs, ignore_index=True)

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(thresh=len(df) * 0.5, axis=1)

    if len(df) > 80_000:
        df = df.sample(80_000, random_state=42)

    print(f"    Shape: {df.shape}, Attack rate: {df['label'].mean():.1%}")
    return df


def run_pipeline(dataset_name: str, df: pd.DataFrame):
    artifact_dir = Path("backend") / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    if "label" not in df.columns:
        raise ValueError("Dataset must contain a label column")

    X = df.drop(columns=["label"]).copy()
    y = pd.to_numeric(df["label"], errors="coerce").fillna(0).astype(int)

    if len(X) < 10:
        raise ValueError(f"Not enough rows to train: {len(X)}")
    if y.nunique() < 2:
        raise ValueError("Training labels contain only one class")

    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    # sanitize
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median())

    # Sample max 15k rows for MI computation to avoid hanging
    mi_sample = min(15000, len(X))
    idx = np.random.choice(len(X), mi_sample, replace=False)
    selector = SelectKBest(mutual_info_classif, k=min(20, X.shape[1]))
    selector.fit(X[idx].to_numpy(), y.iloc[idx].to_numpy())
    X_sel = selector.transform(X.to_numpy())
    selected_features = [X.columns[i] for i in selector.get_support(indices=True)]

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
        # "gradient_boosting": GradientBoostingClassifier(
        #     n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42
        # ),
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
    DATASETS = {
        "nslkdd": ("datasets/nslkdd", load_nslkdd),
        "ciciot": ("datasets/ciciot/CICIoT2023.csv", load_ciciot),
        "unswnb15": ("datasets/unswnb15", load_unswnb15),
        "cicids2017": ("datasets/cicids2017", load_cicids2017),
    }

    for name, (path, loader) in DATASETS.items():
        if not os.path.exists(path):
            print(f"\nSkipping {name} - path not found: {path}")
            print(f"  Download and place files at: {path}")
            continue

        print(f"\n{'=' * 50}")
        print(f"Training: {name.upper()}")
        print(f"{'=' * 50}")
        try:
            df = loader(path)
            run_pipeline(name, df)
        except Exception as e:
            print(f"  ERROR on {name}: {e}")
            import traceback

            traceback.print_exc()

    print("\n=== ALL TRAINING COMPLETE ===")
    print("Artifacts in backend/artifacts/")
    print("\nLoaded datasets:")
    for f in os.listdir("backend/artifacts"):
        if f.endswith("_meta.json"):
            print(f"  [ok] {f.replace('_meta.json', '')}")
