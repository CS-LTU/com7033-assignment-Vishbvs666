from __future__ import annotations

from typing import Any, Dict

from app.ml.predict_service import (
    build_features_from_patient_doc,
    run_ml_on_patient_doc,
)


def test_build_features_from_patient_doc_defaults():
    """
    If some fields are missing in the MongoDB document, the helper should
    still return a complete feature dict with sensible defaults.
    """
    # very minimal patient doc
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
    assert features["hypertension"] == 0
    assert features["heart_disease"] == 0
    assert features["Residence_type"] in ("Urban", "Rural")
    # "N/A" BMI becomes 0.0
    assert features["bmi"] == 0.0


def test_run_ml_on_patient_doc_uses_predict_risk(monkeypatch):
    """
    run_ml_on_patient_doc should call predict_risk and map its output to
    (probability, stroke_flag, risk_level). We stub predict_risk so the
    test does not depend on the real ML model.
    """

    doc: Dict[str, Any] = {
        "demographics": {"gender": "Male", "age": 75},
        "medical_history": {
            "hypertension": 1,
            "heart_disease": 1,
            "avg_glucose_level": 180.0,
            "bmi": 30.0,
            "smoking_status": "smokes",
        },
    }

    # fake model
    def fake_predict_risk(features: Dict[str, Any]) -> Dict[str, Any]:
        # make sure the pipeline passes correct features
        assert features["gender"] == "Male"
        assert features["age"] == 75.0
        return {
            "probability": 0.8,
            "stroke_flag": 1,
            "risk_level": "High",
        }

    # patch the function inside predict_service module
    monkeypatch.setattr(
        "app.ml.predict_service.predict_risk",
        fake_predict_risk,
        raising=True,
    )

    proba, flag, level = run_ml_on_patient_doc(doc)

    assert proba == 0.8
    assert flag == 1
    assert level == "High"
