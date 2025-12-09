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

# app/ml/model.py
from __future__ import annotations

from typing import Any, Dict

# We now keep all the real model loading + encoding logic
# in app.ml.predict_service. This module is just a thin
# backwards-compatible wrapper so existing routes that import
# `predict_risk` from here still work.
from app.ml.predict_service import predict_risk as _predict_risk_impl


def predict_risk(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Backwards-compatible stroke risk prediction function.

    Existing Flask routes still do:

        from app.ml.model import predict_risk

    This wrapper simply delegates to `app.ml.predict_service.predict_risk`,
    which knows how to load the new `stroke_model.joblib` bundle
    (model + encoders + feature_order) and returns:

        {
            "probability": float,        # 0–1
            "stroke_flag": int,          # 0 or 1
            "risk_level": "Low"|"Medium"|"High"
        }
    """
    return _predict_risk_impl(features)
