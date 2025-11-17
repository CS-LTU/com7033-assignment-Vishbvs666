# app/ml/predict.py
from __future__ import annotations


def run_stroke_model(features: dict) -> dict:
    """
    Very simple heuristic model for demo.
    No external dependencies, no PHI logging.
    """
    age = features.get("age") or 0
    hypertension = int(features.get("hypertension") or 0)
    heart = int(features.get("heart_disease") or 0)
    glucose = float(features.get("avg_glucose_level") or 0.0)
    bmi = float(features.get("bmi") or 0.0)

    score = 0.0
    score += age / 120.0
    score += 0.3 * hypertension
    score += 0.3 * heart
    score += min(glucose / 300.0, 1.0) * 0.5
    score += min(bmi / 50.0, 1.0) * 0.3

    score = max(0.0, min(score, 3.0))
    level = "Low"
    if score > 1.4:
        level = "Medium"
    if score > 2.1:
        level = "High"

    factors: list[str] = []
    if age > 55:
        factors.append("Older age")
    if hypertension:
        factors.append("Hypertension")
    if heart:
        factors.append("Heart disease")
    if glucose > 140:
        factors.append("High glucose level")
    if bmi > 30:
        factors.append("High BMI")

    return {
        "level": level,
        "score": round(score, 2),
        "factors": factors,
        "model_version": "heuristic-v1",
    }


# Backwards compatible name some old code might still import
def compute_risk(features: dict) -> dict:
    return run_stroke_model(features)
