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

# app/utils/metrics.py
from __future__ import annotations

from sqlalchemy import func

from app.extensions import db
from app.models import User, StrokePrediction  # type: ignore[import]

def compute_dashboard_metrics() -> dict:
    """
    Return simple counts for dashboards.
    Uses SQLAlchemy only; no PII.
    """
    users_total = db.session.scalar(db.select(func.count(User.id))) or 0
    predictions_total = (
        db.session.scalar(db.select(func.count(StrokePrediction.id))) or 0
    )

    # For now, mirror predictions as a fake "patients" count.
    patients_total = predictions_total

    return {
        "users_total": int(users_total),
        "patients_total": int(patients_total),
        "predictions_total": int(predictions_total),
    }


__all__ = ["compute_dashboard_metrics"]
