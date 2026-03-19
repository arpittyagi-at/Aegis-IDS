from backend.ml.predictor import Predictor
from backend.ml.generator import TrafficGenerator

p = Predictor("ciciot")
g = TrafficGenerator()

for t in ["normal", "ddos", "portscan"]:
    s = g.next_sample(t)
    result = p.predict(s)
    print(t, "prob:", result["probability"], "threshold:", result["threshold"], "is_attack:", result["is_attack"])
