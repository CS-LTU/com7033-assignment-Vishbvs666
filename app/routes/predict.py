from __future__ import annotations

from flask import Blueprint

bp = Blueprint("predict", __name__)


@bp.route("/")
def predict_home():
    return "Predict dashboard (placeholder)"
