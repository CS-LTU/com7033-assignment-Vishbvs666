from __future__ import annotations

from flask import Blueprint

bp = Blueprint("admin", __name__)


@bp.route("/")
def admin_home():
    return "Admin dashboard (placeholder)"
