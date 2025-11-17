from __future__ import annotations

from flask import Blueprint

bp = Blueprint("patients", __name__)


@bp.route("/")
def patients_home():
    return "Patients dashboard (placeholder)"
