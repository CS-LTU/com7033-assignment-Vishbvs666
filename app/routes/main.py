from __future__ import annotations
from datetime import datetime, timezone
from flask import Blueprint, render_template, make_response, redirect, url_for, flash, request
from app.utils.metrics import get_demo_patients, compute_dashboard_metrics
from app.utils.auth import login_required  # <- add this

bp = Blueprint("main", __name__, url_prefix="")

def _nocache(resp):
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

@bp.get("/")
def root():
    return redirect(url_for("main.dashboard"))

@bp.get("/dashboard")
@login_required
def dashboard():
    rows = get_demo_patients(limit=10)
    metrics = compute_dashboard_metrics(rows)
    resp = make_response(render_template(
        "dashboard/index.html",
        metrics=metrics,
        rows=rows,
        now=datetime.now(timezone.utc),
    ))
    return _nocache(resp)

@bp.get("/patients")
@login_required
def patients():
    rows = get_demo_patients(limit=25)
    return render_template("patients/list.html", rows=rows)

@bp.get("/import")
@login_required
def import_data():
    flash("CSV import wizard coming soon.", "success")
    # After flashing, bounce back to where the user came from, else dashboard
    next_url = request.args.get("next") or url_for("main.dashboard")
    return redirect(next_url)

# leave health check open (no auth)
@bp.get("/healthz")
def healthz():
    return {"status": "ok"}, 200
