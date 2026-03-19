import random


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


class TrafficGenerator:
    def __init__(self, seed: int | None = None):
        self._rnd = random.Random(seed)

        # distributions from train.py
        self._normal_params = {
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

        self._ddos_params = {
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

        self._portscan_params = {
            "flow_pkts_per_sec": (600, 200),
            "flow_bytes_per_sec": (3000, 1000),
            "total_fwd_packets": (2, 1),
            "total_bwd_packets": (1, 0.5),
            "syn_flag_count": (12, 5),
            "rst_flag_count": (8, 3),
            "init_win_bytes_backward": (0, 1),
        }

        self._mode_weights = {
            "normal": {"normal": 1.0, "ddos": 0.0, "portscan": 0.0},
            "ddos": {"normal": 0.05, "ddos": 0.95, "portscan": 0.0},
            "portscan": {"normal": 0.10, "ddos": 0.0, "portscan": 0.90},
            "mixed": {"normal": 0.55, "ddos": 0.30, "portscan": 0.15},
        }

    def _gauss(self, mean: float, std: float, min_val: float = 0.0) -> float:
        v = self._rnd.gauss(mean, std)
        return max(min_val, v)

    def _clip_int(self, value: float, min_val: int = 0, max_val: int | None = None) -> int:
        v = int(round(value))
        v = max(min_val, v)
        if max_val is not None:
            v = min(v, max_val)
        return v

    def _gen_feature(self, name: str, typ: str) -> float:
        # Use distribution parameters by type
        params = None
        if typ == "normal":
            params = self._normal_params
        elif typ == "ddos":
            params = self._ddos_params
        elif typ == "portscan":
            params = self._portscan_params

        if name in params:
            mean, std = params[name]
            if name in ("total_fwd_packets", "total_bwd_packets", "syn_flag_count", "rst_flag_count", "fin_flag_count", "psh_flag_count", "ack_flag_count", "urg_flag_count"):
                # integer counts
                if name == "total_fwd_packets":
                    return float(self._clip_int(self._gauss(mean, std), 1))
                if name == "total_bwd_packets":
                    return float(self._clip_int(self._gauss(mean, std), 0, 2 if typ == "portscan" else None))
                return float(self._clip_int(self._gauss(mean, std), 0))

            if name in ("fwd_psh_flags", "bwd_psh_flags", "fwd_urg_flags", "bwd_urg_flags"):
                return float(self._clip_int(self._gauss(mean, std), 0))

            if name in ("init_win_bytes_backward",):
                return float(self._clip_int(self._gauss(mean, std), 0))

            return float(self._gauss(mean, std))

        # fallback heuristics for remaining features
        if name in ("flow_iat_std", "fwd_iat_std", "bwd_iat_std"):
            return float(self._gauss(1000, 500))
        if name in ("flow_iat_max", "flow_iat_min", "fwd_iat_max", "fwd_iat_min", "bwd_iat_max", "bwd_iat_min"):
            return float(self._gauss(1000, 400))
        if name in ("total_length_fwd_pkts", "total_length_bwd_pkts"):
            return float(self._gauss(100000, 50000))
        if name in ("fwd_pkt_len_max", "bwd_pkt_len_max"):
            return float(self._gauss(1200, 400))
        if name in ("fwd_pkt_len_min", "bwd_pkt_len_min"):
            return float(self._gauss(60, 30))
        if name in ("fwd_pkt_len_mean", "bwd_pkt_len_mean"):
            return float(self._gauss(600, 250))
        if name in ("fwd_pkt_len_std", "bwd_pkt_len_std"):
            return float(self._gauss(200, 80))
        if name in ("fwd_packets_per_sec", "bwd_packets_per_sec"):
            return float(self._gauss(100, 40))
        if name in ("min_packet_length", "packet_length_mean"):
            return float(self._gauss(200, 80))
        if name == "packet_length_std":
            return float(self._gauss(100, 60))
        if name == "packet_length_variance":
            return float(self._gauss(20000, 12000))
        if name == "down_up_ratio":
            return float(self._gauss(1.0, 0.5))
        if name == "average_packet_size":
            return float(self._gauss(500, 200))
        if name in ("avg_fwd_segment_size", "avg_bwd_segment_size"):
            return float(self._gauss(900, 300))
        if name == "act_data_pkt_fwd":
            return float(self._gauss(200, 80))
        if name == "min_seg_size_forward":
            return float(self._gauss(200, 60))
        if name in ("active_std",):
            return float(self._gauss(20000, 8000))

        # final fallback
        return float(self._gauss(1000, 500))

    def next_sample(self, mode: str = "normal") -> dict:
        mode = mode.lower()
        weights = self._mode_weights.get(mode, self._mode_weights["normal"])
        choice = self._rnd.choices(
            population=["normal", "ddos", "portscan"],
            weights=[weights["normal"], weights["ddos"], weights["portscan"]],
            k=1,
        )[0]

        sample = {}
        for feat in FEATURES:
            val = self._gen_feature(feat, choice)
            sample[feat] = max(0.0, val)

        return sample

    def pps(self, mode: str = "normal") -> int:
        mode = mode.lower()
        base = {
            "normal": 120,
            "ddos": 9500,
            "portscan": 700,
            "mixed": 400,
        }.get(mode, 120)

        noisy = self._rnd.gauss(base, base * 0.08)
        return max(0, int(round(noisy)))
