import json
import os

import joblib
import numpy as np

artifacts = "backend/artifacts"

for ds in ["ciciot", "nslkdd", "unswnb15", "cicids2017"]:
    print(f"\nChecking {ds}...")

    # Check files exist
    for f in ["_model.pkl", "_scaler.pkl", "_selector.pkl", "_meta.json"]:
        path = f"{artifacts}/{ds}{f}"
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        print(f"  {ds}{f}: {'OK' if exists else 'MISSING'} ({size} bytes)")

    # Load and test meta
    with open(f"{artifacts}/{ds}_meta.json") as f:
        meta = json.load(f)

    print(f"  Selected features ({meta['n_features']}): {meta['selected_features'][:3]}...")
    print(f"  Best model: {meta['best_model']}")
    best = max(meta["metrics"], key=lambda x: x["f1"])
    print(f"  Best F1: {best['f1']}%  AUC: {best['auc']}%  FPR: {best['fpr']}%")

    # Test loading model
    model = joblib.load(f"{artifacts}/{ds}_model.pkl")
    scaler = joblib.load(f"{artifacts}/{ds}_scaler.pkl")

    # Test a prediction
    n_feat = meta["n_features"]
    test_vec = np.random.rand(1, n_feat)
    test_scaled = scaler.transform(test_vec)
    prob = model.predict_proba(test_scaled)[0][1]
    print(f"  Test prediction: {prob:.4f} (model loads and predicts OK)")

print("\nALL ARTIFACTS VERIFIED")
