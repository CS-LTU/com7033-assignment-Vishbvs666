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

# tests/test_predict_form_features.py

from __future__ import annotations
from typing import Any, Dict

from app.routes.predict import _features_from_form


class DummyForm(dict):
    """
    Simulates Flask's request.form for testing.
    """

    def get(self, key: str, default: Any | None = None) -> Any:
        return super().get(key, default)


# --------------------------------------------------
# Test 1: Normal, complete form
# --------------------------------------------------

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
        patient_id="ABC123",   # doctor form only
    )

    features = _features_from_form(form_data)

    # direct string values
    assert features["gender"] == "Female"

    # numeric conversions
    assert isinstance(features["age"], float)
    assert features["age"] == 65.0
    assert features["avg_glucose_level"] == 145.5
    assert features["bmi"] == 29.3

    # Yes/No conversions
    assert features["hypertension"] == 1
    assert features["heart_disease"] == 0

    # passthrough values
    assert features["ever_married"] == "Yes"
    assert features["work_type"] == "Private"
    assert features["Residence_type"] == "Urban"
    assert features["smoking_status"] == "formerly smoked"

    # optional field
    assert features.get("patient_id") == "ABC123"


# --------------------------------------------------
# Test 2: Missing / empty values
# --------------------------------------------------

def test_features_from_form_handles_missing_values():
    form_data: Dict[str, Any] = DummyForm(
        gender="Other",
        age="",                      # missing numeric
        hypertension="No",
        heart_disease="No",
        ever_married="",             # missing
        work_type="",                # missing
        residence_type="Rural",
        avg_glucose_level="",        # missing numeric
        bmi="",                      # missing numeric
        smoking_status="never smoked",
        patient_id="",               # missing
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
