# app/routes/patient.py
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

from app.models import StrokePrediction

bp = Blueprint("patient", __name__, url_prefix="/patient")


# -----------------------------
# Helper: only patients allowed
# -----------------------------
def _ensure_patient() -> None:
    """Only allow users with the 'patient' role."""
    if not current_user.is_authenticated or getattr(current_user, "role", None) != "patient":
        abort(403)


def _get_patient_predictions():
    """
    Helper to fetch predictions for the current patient.

    Primary path: filter by user_id (normal case).
    Fallback: if something is odd with the schema, just return all predictions
    so the page never 500s.
    """
    try:
        if hasattr(StrokePrediction, "user_id"):
            return (
                StrokePrediction.query
                .filter_by(user_id=current_user.id)
                .order_by(StrokePrediction.created_at.desc())
                .all()
            )

        # Very defensive fallback
        return (
            StrokePrediction.query
            .order_by(StrokePrediction.created_at.desc())
            .all()
        )
    except Exception:
        # Fail-safe – never break the dashboard
        return []


# -----------------------------
# PATIENT DASHBOARD
# -----------------------------
@bp.route("/dashboard")
@login_required
def patient_dashboard():
    _ensure_patient()

    predictions = _get_patient_predictions()
    latest = predictions[0] if predictions else None

    # Pull numeric probability if available (0–1)
    last_score = None
    if latest is not None and hasattr(latest, "probability"):
        last_score = getattr(latest, "probability", None)

    # Preferred label: whatever the model stored in risk_level
    last_label = None
    if latest is not None and hasattr(latest, "risk_level"):
        last_label = getattr(latest, "risk_level", None)

    # If for some reason risk_level is missing, fall back to bucketing the score
    def _fallback_bucket(score: float | None) -> str:
        if score is None:
            return "Not assessed"
        try:
            s = float(score)
        except Exception:
            return "Not assessed"
        if s < 0.33:
            return "Low"
        elif s < 0.66:
            return "Medium"
        return "High"

    if not last_label:
        last_label = _fallback_bucket(last_score)

    total_predictions = len(predictions)
    last_time = getattr(latest, "created_at", None) if latest else None

    metrics = {
        "last_bucket": last_label,        # used by dashboard UI
        "last_score": last_score,         # probability (0–1) for % display
        "total_predictions": total_predictions,
        "last_time": last_time,
    }

    return render_template(
        "patient/dashboard.html",
        metrics=metrics,
        last_prediction=latest,
    )


# -----------------------------
# PROFILE / PERSONAL INFO
# -----------------------------
@bp.route("/profile")
@login_required
def patient_profile():
    _ensure_patient()
    # For now, just show data from current_user (SQLite).
    return render_template("patient/profile.html")


# -----------------------------
# STROKE RISK HISTORY
# -----------------------------
@bp.route("/predictions")
@login_required
def patient_predictions():
    _ensure_patient()

    predictions = _get_patient_predictions()

    return render_template(
        "patient/predictions.html",
        predictions=predictions,
    )


# -----------------------------
# HEALTH EDUCATION
# -----------------------------
@bp.route("/education")
@login_required
def patient_education():
    _ensure_patient()
    return render_template("patient/education.html")
