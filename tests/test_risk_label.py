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

# tests/test_risk_label.py
from __future__ import annotations

"""
Tests for the probability → risk label helper.

These are aligned with the NEW thresholds in app/ml/predict_service.py:

- High   = p ≥ 0.30
- Medium = 0.12 ≤ p < 0.30
- Low    = p < 0.12
"""

from app.ml.predict_service import _probability_to_label


def test_risk_label_low():
    # Below 0.12 should always be Low
    assert _probability_to_label(0.00) == "Low"
    assert _probability_to_label(0.05) == "Low"
    assert _probability_to_label(0.119) == "Low"


def test_risk_label_medium():
    # 0.12–0.299... should be Medium
    assert _probability_to_label(0.12) == "Medium"
    assert _probability_to_label(0.20) == "Medium"
    assert _probability_to_label(0.299) == "Medium"


def test_risk_label_high():
    # ≥ 0.30 should be High
    assert _probability_to_label(0.30) == "High"
    assert _probability_to_label(0.44) == "High"
    assert _probability_to_label(0.80) == "High"
