import json
import os
import sqlite3
import time
from pathlib import Path

DB_PATH = Path("backend") / "data" / "alerts.db"


def _get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the alerts table if it doesn't exist."""
    conn = _get_conn()
    try:
        conn.execute(
            """
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
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def insert(record: dict):
    """Insert one detection record."""
    conn = _get_conn()
    try:
        conn.execute(
            """
            INSERT INTO alerts (
                ts, is_attack, probability, severity, threshold,
                dataset, latency_ms, shap_vals
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                float(record.get("timestamp", time.time())),
                int(record.get("is_attack", 0)),
                float(record.get("probability", 0.0)),
                str(record.get("severity", "")),
                float(record.get("threshold", 0.0)),
                str(record.get("dataset", "")),
                float(record.get("latency_ms", 0.0)),
                json.dumps(record.get("shap_vals", {})),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def recent_alerts(limit: int = 50) -> list:
    """Return the last N alerts ordered by ts DESC."""
    conn = _get_conn()
    try:
        cursor = conn.execute(
            "SELECT * FROM alerts ORDER BY ts DESC LIMIT ?",
            (int(limit),),
        )
        rows = cursor.fetchall()
        out = []
        for row in rows:
            item = dict(row)
            item["shap_vals"] = json.loads(item.get("shap_vals", "{}") or "{}")
            out.append(item)
        return out
    finally:
        conn.close()


def stats() -> dict:
    """Return aggregated stats about the alerts."""
    conn = _get_conn()
    try:
        now = time.time()
        cutoff = now - 60

        total_analyzed = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        total_attacks = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE is_attack=1"
        ).fetchone()[0]
        attacks_per_min = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE is_attack=1 AND ts > ?", (cutoff,)
        ).fetchone()[0]

        avg_latency = conn.execute("SELECT AVG(latency_ms) FROM alerts").fetchone()[0] or 0.0

        detection_rate = (total_attacks / total_analyzed * 100.0) if total_analyzed > 0 else 0.0

        return {
            "total_analyzed": int(total_analyzed),
            "total_attacks": int(total_attacks),
            "attacks_per_min": int(attacks_per_min),
            "avg_latency_ms": float(avg_latency),
            "detection_rate": float(detection_rate),
        }
    finally:
        conn.close()
