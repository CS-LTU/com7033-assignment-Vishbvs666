'''
===========================================================
StrokeCare Web Application — Secure Software Development
Author: Vishvapriya Sangvikar

Course: COM7033 – MSc Data Science & Artificial Intelligence
Student ID: 2415083
Institution: Leeds Trinity University
Assessment: Assessment 1 – Software Artefact (70%)
AI Statement: Portions of this file were drafted or refined using
    generative AI for planning and editing only,
    as permitted in the module brief.
===========================================================
'''

# app/ml/predict_service.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder


# ----------------------------------------------------------------------
# Paths & model bundle
# ----------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "instance" / "stroke_model.joblib"

_MODEL: RandomForestClassifier | None = None
_ENCODERS: Dict[str, LabelEncoder] | None = None
_FEATURE_ORDER: list[str] | None = None


# ----------------------------------------------------------------------
# Lazy loader for the new model bundle (model + encoders + feature order)
# ----------------------------------------------------------------------
def _ensure_model_loaded() -> None:
    global _MODEL, _ENCODERS, _FEATURE_ORDER

    if _MODEL is not None:
        return

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")

    bundle = joblib.load(MODEL_PATH)

    _MODEL = bundle["model"]
    _ENCODERS = bundle.get("encoders", {})
    _FEATURE_ORDER = bundle.get(
        "feature_order",
        [
            "gender",
            "age",
            "hypertension",
            "heart_disease",
            "ever_married",
            "work_type",
            "Residence_type",
            "avg_glucose_level",
            "bmi",
            "smoking_status",
        ],
    )


# ----------------------------------------------------------------------
# Build features from MongoDB patient document
# ----------------------------------------------------------------------
def build_features_from_patient_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    demographics = doc.get("demographics", {}) or {}
    medical = doc.get("medical_history", {}) or {}

    # Handle Residence_type variations
    residence_type = (
        demographics.get("residence_type")
        or demographics.get("Residence_type")
        or doc.get("Residence_type")
        or "Urban"
    )

    bmi_val = medical.get("bmi") or doc.get("bmi")
    if bmi_val in (None, "", "N/A"):
        bmi_val = 0.0

    features: Dict[str, Any] = {
        "gender": demographics.get("gender") or doc.get("gender") or "Other",
        "age": float(demographics.get("age") or doc.get("age") or 0),
        "hypertension": int(medical.get("hypertension") or doc.get("hypertension") or 0),
        "heart_disease": int(medical.get("heart_disease") or doc.get("heart_disease") or 0),
        "ever_married": demographics.get("ever_married") or doc.get("ever_married") or "No",
        "work_type": demographics.get("work_type") or doc.get("work_type") or "Private",
        "Residence_type": residence_type,
        "avg_glucose_level": float(
            medical.get("avg_glucose_level") or doc.get("avg_glucose_level") or 0
        ),
        "bmi": float(bmi_val),
        "smoking_status": medical.get("smoking_status")
        or doc.get("smoking_status")
        or "never smoked",
    }

    return features

# ----------------------------------------------------------------------
# Safe label encoding for unseen categories
# ----------------------------------------------------------------------
def _safe_encode(enc: LabelEncoder, value: str) -> int:
    classes = list(enc.classes_)
    if value in classes:
        return int(enc.transform([value])[0])

    for fallback in ["Unknown", "unknown", "UNK"]:
        if fallback in classes:
            return int(enc.transform([fallback])[0])

    return int(enc.transform([classes[0]])[0])


# ----------------------------------------------------------------------
# Probability → Risk label (UPDATED THRESHOLDS)
# ----------------------------------------------------------------------
def _probability_to_label(p: float) -> str:
    """
    Convert ML probability into a readable risk level.

    NEW REALISTIC THRESHOLDS:
    - High    = p ≥ 0.30
    - Medium  = p ≥ 0.12
    - Low     = below 0.12
    """
    if p >= 0.30:
        return "High"
    if p >= 0.12:
        return "Medium"
    return "Low"


# ----------------------------------------------------------------------
# Core ML prediction logic
# ----------------------------------------------------------------------
def predict_risk(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict stroke probability + risk level using the trained model bundle.
    Returns:
        {
            "probability": float,
            "stroke_flag": 0/1,
            "risk_level": "Low"|"Medium"|"High"
        }
    """
    _ensure_model_loaded()
    assert _MODEL is not None
    assert _ENCODERS is not None
    assert _FEATURE_ORDER is not None

    df = pd.DataFrame([features])

    # Numeric cleanup
    numeric_cols = ["age", "hypertension", "heart_disease", "avg_glucose_level", "bmi"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Apply encoders
    for col, enc in _ENCODERS.items():
        if col in df.columns:
            df[col] = df[col].astype(str).apply(lambda v: _safe_encode(enc, v))

    # Add any missing expected columns
    for col in _FEATURE_ORDER:
        if col not in df.columns:
            df[col] = 0

    df = df[_FEATURE_ORDER]

    # Predict probability
    proba = float(_MODEL.predict_proba(df.to_numpy())[0][1])
    stroke_flag = int(proba >= 0.5)

    risk_level = _probability_to_label(proba)

    return {
        "probability": proba,
        "stroke_flag": stroke_flag,
        "risk_level": risk_level,
    }


# ----------------------------------------------------------------------
# Public API for routes
# ----------------------------------------------------------------------
def run_ml_on_patient_doc(doc: Dict[str, Any]) -> Tuple[float, int, str]:
    """
    Wrapper used everywhere else in the app.
    Returns:
        probability(float), stroke_flag(0/1), risk_level(str)
    """
    features = build_features_from_patient_doc(doc)
    result = predict_risk(features)

    proba = float(result["probability"])
    stroke_flag = int(result["stroke_flag"])
    risk_level = result["risk_level"]

    return proba, stroke_flag, risk_level
