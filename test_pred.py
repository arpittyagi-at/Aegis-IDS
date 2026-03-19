import sys
from backend.ml.predictor import Predictor
from backend.ml.generator import TrafficGenerator

try:
    p = Predictor("ciciot")
    g = TrafficGenerator()
    
    # generate a normal sample
    n_sample = g.next_sample("normal")
    n_pred = p.predict(n_sample)
    
    # generate a ddos sample
    d_sample = g.next_sample("ddos")
    d_pred = p.predict(d_sample)
    
    import numpy as np
    z = np.zeros((1, 20))
    print("Zeros scaled proba:", p.model.predict_proba(z))
    
    o = np.ones((1, 20))
    print("Ones scaled proba:", p.model.predict_proba(o))
except Exception as e:
    print(f"Error: {e}")
