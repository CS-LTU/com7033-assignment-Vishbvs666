"""
ML package for StrokeCare.

Provides:
- load_model()  → load the trained stroke model from instance/stroke_model.joblib
- predict_risk(features) → run a prediction and return probability + risk level
"""

from .model import load_model, predict_risk  # noqa: F401
