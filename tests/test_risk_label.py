# tests/test_risk_label.py

from __future__ import annotations

from scripts.compute_ml_for_existing_docs import risk_label


def test_risk_label_low():
    assert risk_label(0.00) == "Low"
    assert risk_label(0.29) == "Low"


def test_risk_label_medium():
    assert risk_label(0.30) == "Medium"
    assert risk_label(0.69) == "Medium"


def test_risk_label_high():
    assert risk_label(0.70) == "High"
    assert risk_label(0.95) == "High"
