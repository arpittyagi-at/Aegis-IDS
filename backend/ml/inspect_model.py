import json
import numpy as np
import joblib
import pandas as pd

from backend.ml.generator import FEATURES, TrafficGenerator
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

print('running inspect_model')
print('generating demo dataset...')
generator = TrafficGenerator(seed=42)
normal = [generator.next_sample("normal") | {"label": 0} for _ in range(500)]
attack = [generator.next_sample("ddos") | {"label": 1} for _ in range(500)]
df = pd.DataFrame(normal + attack, columns=[*FEATURES, "label"])
print('dataset generated')

# Use saved artifacts to avoid expensive mutual_info selection computations
artifact_dir = 'backend/artifacts'
with open(f"{artifact_dir}/ciciot_meta.json") as f:
    meta = json.load(f)

selected_features = meta['selected_features']

# Use all original features for selector input
X = df.drop(columns=['label'])
y = df['label']

scaler = joblib.load(f"{artifact_dir}/ciciot_scaler.pkl")
selector = joblib.load(f"{artifact_dir}/ciciot_selector.pkl")
model = joblib.load(f"{artifact_dir}/ciciot_model.pkl")

X_sel = selector.transform(X)
X_scaled = scaler.transform(X_sel)

from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

print('y_test dist', np.bincount(y_test))

model.fit(X_train, y_train)

preds = model.predict(X_test)
probs = model.predict_proba(X_test)[:, 1]

print('acc', accuracy_score(y_test, preds))
print('f1', f1_score(y_test, preds))
print('precision', precision_score(y_test, preds))
print('recall', recall_score(y_test, preds))
print('mean prob', np.mean(probs))
print('sample probs', probs[:10])
