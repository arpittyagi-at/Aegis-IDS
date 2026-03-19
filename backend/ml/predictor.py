import json
import time
from collections import deque
from pathlib import Path

import joblib
import numpy as np


# full feature list used during training (must match backend/ml/train.py FEATURES)
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


class Predictor:
    def __init__(self, dataset: str):
        self.dataset = dataset.lower()
        artifact_dir = Path("backend") / "artifacts"

        # Load metadata
        with open(artifact_dir / f"{self.dataset}_meta.json", "r", encoding="utf-8") as f:
            self.meta = json.load(f)

        # order matters: must match training selector
        self.feature_names = list(self.meta.get("selected_features", []))
        self.all_feature_names = FEATURES

        # load artifacts
        self.model = joblib.load(artifact_dir / f"{self.dataset}_model.pkl")
        self.scaler = joblib.load(artifact_dir / f"{self.dataset}_scaler.pkl")
        self.selector = joblib.load(artifact_dir / f"{self.dataset}_selector.pkl")

        # adaptive CUSUM window
        self._prob_history = deque(maxlen=100)
        self._base_threshold = 0.45

    def _threshold(self) -> float:
        """Return the current adaptive threshold."""
        return self._get_threshold()

    @property
    def _window(self) -> deque:
        """Expose the internal probability history window."""
        return self._prob_history

    def _get_threshold(self) -> float:
        if len(self._prob_history) < 20:
            return self._base_threshold
        arr = np.array(self._prob_history)
        mean = float(np.mean(arr))
        std = float(np.std(arr))
        thr = min(0.88, max(self._base_threshold, mean + 1.5 * std))
        return thr

    def get_metrics(self):
        return self.meta.get("metrics", [])

    def predict(self, feature_dict: dict) -> dict:
        start = time.perf_counter()
        import warnings
        import pandas as pd

        # Build full feature vector in the same order as training
        vec = {f: float(feature_dict.get(f, 0.0) or 0.0) for f in self.all_feature_names}
        arr_df = pd.DataFrame([vec], columns=self.all_feature_names)

        # sanitize
        arr_df = arr_df.replace([float("inf"), float("-inf")], 0.0).fillna(0.0)

        # select then scale (same order as training)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            selected = self.selector.transform(arr_df)
            scaled = self.scaler.transform(selected)

        prob = float(self.model.predict_proba(scaled)[0][1])
        self._prob_history.append(prob)

        threshold = self._get_threshold()
        is_attack = prob >= threshold

        if prob >= 0.95:
            severity = "CRITICAL"
        elif prob >= 0.85:
            severity = "HIGH"
        elif prob >= 0.70:
            severity = "MEDIUM"
        elif prob >= threshold:
            severity = "LOW"
        else:
            severity = "NONE"

        latency_ms = (time.perf_counter() - start) * 1000.0

        return {
            "is_attack": bool(is_attack),
            "probability": round(prob, 4),
            "threshold": round(threshold, 4),
            "severity": severity,
            "latency_ms": float(latency_ms),
            "dataset": self.dataset,
        }
