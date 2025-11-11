from __future__ import annotations
from flask import Blueprint, render_template, redirect, url_for, jsonify
from app.db.mongo import get_db, close_mongo

bp = Blueprint("main", __name__)

@bp.get("/")
def root():
    return redirect(url_for("main.dashboard"))

@bp.get("/healthz")
def healthz():
    return "ok", 200

@bp.get("/dashboard")
def dashboard():
    from app.data.stroke_data import metrics, charts_data
    return render_template(
        "dashboard/index.html",
        metrics=metrics(),
        charts=charts_data(),    # dict of arrays ready for SVG
    )

# temporary patients list route to satisfy url_for in template
@bp.get("/patients")
def patients():
    return render_template("patients/list.html", rows=[])

@bp.get("/mongo-test")
def mongo_test():
    db = get_db()
    db._smoketest.insert_one({"ok": True})
    doc = db._smoketest.find_one(sort=[("_id", -1)]) or {}
    ok_flag = bool(doc["ok"]) if isinstance(doc, dict) and "ok" in doc else False
    return jsonify({"connected": True, "db": db.name, "last_doc": {"ok": ok_flag}}), 200

@bp.teardown_app_request
def _teardown(exc):
    close_mongo()
