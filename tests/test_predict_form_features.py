# tests/test_predict_form_features.py

from __future__ import annotations

from typing import Any, Dict

from app.routes.predict import _features_from_form


class DummyForm(dict):
    """
    Behaves like Flask's request.form for testing:
    supports .get(key, default) and stores string values.
    """

    def get(self, key: str, default: Any | None = None) -> Any:
        return super().get(key, default)


def test_features_from_form_basic_mapping():
    form_data: Dict[str, Any] = DummyForm(
        gender="Female",
        age="65",
        hypertension="Yes",
        heart_disease="No",
        ever_married="Yes",
        work_type="Private",
        residence_type="Urban",
        avg_glucose_level="145.5",
        bmi="29.3",
        smoking_status="formerly smoked",
        patient_id="ABC123",
    )

    features = _features_from_form(form_data)

    assert features["gender"] == "Female"
    assert isinstance(features["age"], float)
    assert features["age"] == 65.0

    # Yes/No → 1/0
    assert features["hypertension"] == 1
    assert features["heart_disease"] == 0

    assert features["ever_married"] == "Yes"
    assert features["work_type"] == "Private"
    assert features["Residence_type"] == "Urban"
    assert features["avg_glucose_level"] == 145.5
    assert features["bmi"] == 29.3
    assert features["smoking_status"] == "formerly smoked"

    # extra field we added for doctor view
    assert features.get("patient_id") == "ABC123"


def test_features_from_form_handles_missing_values():
    """
    Missing or empty fields should become None rather than raising errors.
    """
    form_data: Dict[str, Any] = DummyForm(
        gender="Other",
        age="",  # missing
        hypertension="No",
        heart_disease="No",
        ever_married="",
        work_type="",
        residence_type="Rural",
        avg_glucose_level="",
        bmi="",
        smoking_status="never smoked",
        patient_id="",
    )

    features = _features_from_form(form_data)

    assert features["gender"] == "Other"
    assert features["age"] is None
    assert features["hypertension"] == 0
    assert features["heart_disease"] == 0
    assert features["ever_married"] is None
    assert features["work_type"] is None
    assert features["Residence_type"] == "Rural"
    assert features["avg_glucose_level"] is None
    assert features["bmi"] is None
    assert features["smoking_status"] == "never smoked"
    assert features.get("patient_id") is None
