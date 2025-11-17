from __future__ import annotations

from flask import Blueprint

bp = Blueprint("privacy", __name__)


@bp.route("/")
def privacy_page():
    return "Privacy page (placeholder)"
