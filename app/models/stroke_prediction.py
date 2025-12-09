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

# app/models/stroke_prediction.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from app.extensions import db


class StrokePrediction(db.Model):
    __tablename__ = "stroke_predictions"

    id = db.Column(db.Integer, primary_key=True)

    # Link to the logged-in user who triggered the prediction
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    # ML outputs
    probability = db.Column(db.Float, nullable=False)      # e.g. 0.73
    stroke_flag = db.Column(db.Integer, nullable=False)    # 0 or 1
    risk_level = db.Column(db.String(20), nullable=False)  # "Low" / "Medium" / "High"

    # Raw input features we passed into the model (gender, age, etc.)
    raw_features = db.Column(db.JSON, nullable=False)

    # When this prediction was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship back to the user
    user = db.relationship("User", backref="stroke_predictions", lazy=True)

    def to_dict(self) -> Dict[str, Any]:
        """Helper for charts / APIs."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "probability": self.probability,
            "stroke_flag": self.stroke_flag,
            "risk_level": self.risk_level,
            "raw_features": self.raw_features,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
