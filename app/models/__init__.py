# app/models/__init__.py
from __future__ import annotations

from app.extensions import db
from .user import User  # ensure this is imported so user_loader runs


# --- Optional simple models so other imports work without errors --- #
# If you already have these defined elsewhere, keep your versions.
# These are safe, minimal placeholders matching names used in utils.

class StrokePrediction(db.Model):
    __tablename__ = "stroke_predictions"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, nullable=True)
    risk_score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, nullable=False, default=False)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, server_default=db.func.now())


__all__ = ["User", "StrokePrediction", "PasswordResetToken", "AuditLog"]
from .user import User

__all__ = ["User"]
