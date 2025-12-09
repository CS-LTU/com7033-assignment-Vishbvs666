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

# tests/test_predict_service.py

from __future__ import annotations

from typing import Any, Dict

from app.ml.predict_service import (
    build_features_from_patient_doc,
    run_ml_on_patient_doc,
)


# --------------------------------------------------
# Test 1: feature-building from MongoDB doc
# --------------------------------------------------

def test_build_features_from_patient_doc_defaults():
    """
    If some fields are missing in the MongoDB document, the helper should
    still return a complete feature dict with sensible defaults.
    """
    # Very minimal patient doc
    doc: Dict[str, Any] = {
        "demographics": {
            "gender": "Female",
            "age": 60,
        },
        "medical_history": {
            # hypertension / heart_disease missing
            "bmi": "N/A",  # should be normalised to 0.0
        },
    }

    features = build_features_from_patient_doc(doc)

    expected_keys = {
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
    }

    # All keys present
    assert expected_keys.issubset(features.keys())

    # Defaults correctly applied
    assert features["gender"] == "Female"
    assert isinstance(features["age"], float)
    assert features["age"] == 60.0

    # Missing hypertension/heart_disease → 0
    assert features["hypertension"] == 0
    assert features["heart_disease"] == 0

    # Residence_type default should be a valid string
    assert features["Residence_type"] in ("Urban", "Rural")

    # "N/A" BMI becomes 0.0
    assert features["bmi"] == 0.0

    # Other defaults
    assert features["ever_married"] in ("Yes", "No")
    assert features["work_type"] in ("Private", "Self-employed", "Govt_job", "children", "Never_worked", "Other")
    assert features["avg_glucose_level"] == 0.0
    assert features["smoking_status"] in ("never smoked", "formerly smoked", "smokes", "Unknown", "unknown", "UNK")


# --------------------------------------------------
# Test 2: run_ml_on_patient_doc delegates to predict_risk
# --------------------------------------------------

def test_run_ml_on_patient_doc_uses_predict_risk(monkeypatch):
    """
    run_ml_on_patient_doc should call predict_risk and map its output to
    (probability, stroke_flag, risk_level). We stub predict_risk so the
    test does not depend on the real ML model.
    """

    doc: Dict[str, Any] = {
        "demographics": {
            "gender": "Male",
            "age": 75,
        },
        "medical_history": {
            "hypertension": 1,
            "heart_disease": 1,
            "avg_glucose_level": 180.0,
            "bmi": 30.0,
            "smoking_status": "smokes",
        },
    }

    # Fake model behaviour
    def fake_predict_risk(features: Dict[str, Any]) -> Dict[str, Any]:
        # Make sure the pipeline passes correct features
        assert features["gender"] == "Male"
        assert features["age"] == 75.0
        assert features["hypertension"] == 1
        assert features["heart_disease"] == 1

        # Return a canned result
        return {
            "probability": 0.8,
            "stroke_flag": 1,
            "risk_level": "High",
        }

    # Patch predict_risk inside the predict_service module
    monkeypatch.setattr(
        "app.ml.predict_service.predict_risk",
        fake_predict_risk,
        raising=True,
    )

    proba, flag, level = run_ml_on_patient_doc(doc)

    assert proba == 0.8
    assert flag == 1
    assert level == "High"
