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

# app/models/__init__.py
from __future__ import annotations

"""
Central place to import and re-export all SQLAlchemy models.

DO NOT define models here – only import them.
"""

from .user import User
from .session import Session
from .stroke_prediction import StrokePrediction
from .password_reset import PasswordResetToken
from .audit_log import AuditLog

__all__ = [
    "User",
    "Session",
    "StrokePrediction",
    "PasswordResetToken",
    "AuditLog",
]
