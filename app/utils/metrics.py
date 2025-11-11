from __future__ import annotations
from statistics import mean

def get_demo_patients(limit: int = 10):
    data = [
        {"id":"demo-001","age":67,"gender":"F","hypertension":1,"smoking":"never","risk":"Medium","glucose":108,"bmi":28.4},
        {"id":"demo-002","age":45,"gender":"M","hypertension":0,"smoking":"smokes","risk":"Low","glucose":95,"bmi":24.7},
        {"id":"demo-003","age":73,"gender":"F","hypertension":1,"smoking":"never","risk":"High","glucose":105,"bmi":29.9},
    ]
    for r in data:
        r["hypertension"] = bool(r["hypertension"])
    return data[:limit]

def compute_dashboard_metrics(rows):
    total = len(rows)
    high = sum(1 for r in rows if str(r["risk"]).lower() == "high")
    gvals = [r.get("glucose") for r in rows if r.get("glucose") is not None]
    bvals = [r.get("bmi") for r in rows if r.get("bmi") is not None]
    return {
        "total_patients": total,
        "high_risk_pct": round((high/total)*100, 1) if total else 0.0,
        "avg_glucose": round(mean(gvals), 1) if gvals else None,
        "avg_bmi": round(mean(bvals), 1) if bvals else None,
    }
