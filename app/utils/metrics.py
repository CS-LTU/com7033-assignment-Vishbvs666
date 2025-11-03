from __future__ import annotations
from typing import List, Dict

# NOTE: this file is intentionally framework-agnostic (pure Python)
# so it is easy to unit-test.

# ---- Demo data -------------------------------------------------------------
_DEMO = [
    {"id": "demo-001", "age": 67, "gender": "F", "hypertension": True,  "smoking": "never",  "bmi": 23.4, "avg_glucose": 92.0,  "risk": "Medium"},
    {"id": "demo-002", "age": 45, "gender": "M", "hypertension": False, "smoking": "smokes", "bmi": 28.1, "avg_glucose": 101.0, "risk": "Low"},
    {"id": "demo-003", "age": 73, "gender": "F", "hypertension": True,  "smoking": "never",  "bmi": 31.3, "avg_glucose": 115.0, "risk": "High"},
]

def get_demo_patients(limit: int = 10) -> List[Dict]:
    return _DEMO[:limit]

# ---- Computation -----------------------------------------------------------
def _mean(values):
    nums = [v for v in values if isinstance(v, (int, float))]
    return round(sum(nums) / len(nums), 1) if nums else None

def compute_dashboard_metrics(rows: List[Dict]) -> Dict:
    total = len(rows)
    high = sum(1 for r in rows if str(r.get("risk", "")).lower() == "high")
    pct_high = round((high / total) * 100, 1) if total else 0.0

    avg_bmi = _mean([r.get("bmi") for r in rows])
    avg_glucose = _mean([r.get("avg_glucose") for r in rows])

    return {
        "total_patients": total,
        "high_risk_pct": pct_high,
        "avg_bmi": avg_bmi,
        "avg_glucose": avg_glucose,
    }
