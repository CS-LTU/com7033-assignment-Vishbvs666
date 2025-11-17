# app/routes/__init__.py
from __future__ import annotations

from .auth import bp as auth_bp
from .admin import bp as admin_bp
from .patients import bp as patients_bp
from .predict import bp as predict_bp
from .privacy import bp as privacy_bp
from .main import bp as main_bp

__all__ = [
    "auth_bp",
    "admin_bp",
    "patients_bp",
    "predict_bp",
    "privacy_bp",
    "main_bp",
]
