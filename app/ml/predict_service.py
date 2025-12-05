# app/ml/predict_service.py
from __future__ import annotations

from typing import Any, Dict, Tuple

from app.ml.model import predict_risk


def build_features_from_patient_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a feature dict from a MongoDB patient document that matches
    the expected input for app.ml.model.predict_risk().

    We assume the document follows the structure created by the
    CSV import script: top-level + demographics + medical_history.
    """
    demographics = doc.get("demographics", {}) or {}
    medical = doc.get("medical_history", {}) or {}

    # Handle Residence_type vs residence_type gracefully
    residence_type = (
        demographics.get("residence_type")
        or doc.get("Residence_type")
        or demographics.get("Residence_type")
        or "Urban"
    )

    bmi_val = medical.get("bmi")
    if bmi_val in (None, "", "N/A"):
        bmi_val = 0.0

    features: Dict[str, Any] = {
        "gender": demographics.get("gender") or doc.get("gender") or "Other",
        "age": float(demographics.get("age") or doc.get("age") or 0),
        "hypertension": int(medical.get("hypertension") or doc.get("hypertension") or 0),
        "heart_disease": int(medical.get("heart_disease") or 0),
        "ever_married": demographics.get("ever_married") or doc.get("ever_married") or "No",
        "work_type": demographics.get("work_type") or doc.get("work_type") or "Private",
        "Residence_type": residence_type,
        "avg_glucose_level": float(
            medical.get("avg_glucose_level") or doc.get("avg_glucose_level") or 0
        ),
        "bmi": float(bmi_val),
        "smoking_status": medical.get("smoking_status") or doc.get("smoking_status") or "never smoked",
    }

    return features


def run_ml_on_patient_doc(doc: Dict[str, Any]) -> Tuple[float, int, str]:
    """
    Run the trained ML model on a single patient document.

    Returns:
        probability (0–1),
        stroke_flag (0/1),
        risk_level ("Low"/"Medium"/"High")
    """
    features = build_features_from_patient_doc(doc)
    result = predict_risk(features)

    # model returns a dict like {"probability": ..., "stroke_flag": ..., "risk_level": ...}
    proba = float(result.get("probability", 0.0))
    stroke_flag = int(result.get("stroke_flag", 1 if proba >= 0.5 else 0))

    #  IMPORTANT: always compute risk_level ourselves based on probability
    # so doctor view, recompute script, and HCP view all share the SAME thresholds.
    #
    # High    = 0.70+
    # Medium  = 0.12–0.69
    # Low     = < 0.12
    if proba >= 0.70:
        risk_level = "High"
    elif proba >= 0.12:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return proba, stroke_flag, risk_level
