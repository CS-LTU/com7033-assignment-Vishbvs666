# app/routes/main.py
from __future__ import annotations

from flask import Blueprint, redirect, url_for, render_template
from flask_login import current_user

bp = Blueprint("main", __name__)


def _route_for_role():
    """Return a redirect to the correct dashboard based on user.role."""
    role = getattr(current_user, "role", None)

    if role == "admin":
        return redirect(url_for("admin.admin_dashboard"))
    if role == "doctor":
        return redirect(url_for("doctor.doctor_dashboard"))
    if role == "hcp":
        return redirect(url_for("hcp.hcp_dashboard"))
    if role == "patient":
        return redirect(url_for("patient.patient_dashboard"))

    # Unknown role – fall back to a simple page
    return render_template("main/coming_soon.html", role=role)


@bp.route("/")
def index():
    """
    Entry point for 127.0.0.1:5000

    - If NOT logged in  -> go to login page
    - If logged in      -> route based on role
    """
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))

    return _route_for_role()
from app.db.mongo import get_patient_collection  # add near the top


@bp.route("/debug/mongo")
def debug_mongo():
    coll = get_patient_collection()
    count = coll.count_documents({})
    return f"MongoDB OK — patients collection has {count} document(s)."
