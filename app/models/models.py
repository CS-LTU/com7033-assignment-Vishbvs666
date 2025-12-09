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

# app/models/models.py
from __future__ import annotations

"""
Central export file for ORM models.

IMPORTANT:
Do NOT define any db.Model subclasses here with their own __tablename__.
Actual model classes live in separate modules (user.py, session.py,
stroke_prediction.py, etc.). This avoids accidentally defining the same
table twice and triggering SQLAlchemy 'table is already defined' errors.
"""

from app.extensions import db  # noqa: F401

from .user import User          # noqa: F401
from .session import Session    # noqa: F401
from .stroke_prediction import StrokePrediction  # noqa: F401

__all__ = ["User", "Session", "StrokePrediction"]
