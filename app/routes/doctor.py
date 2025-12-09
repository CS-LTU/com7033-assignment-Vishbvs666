'''
===========================================================
StrokeCare Web Application — Secure Software Development
Author: Vishvapriya Sangvikar

Course: COM7033 – MSc Data Science & Artificial Intelligence
Student ID: 2415083
Institution: Leeds Trinity University
Assessment: Assessment 1 – Software Artefact (70%)
AI Statement: Portions of this file were drafted or refined using
    generative AI for planning and editing only,
    as permitted in the module brief.
===========================================================
'''

# app/routes/doctor.py
from __future__ import annotations

from datetime import datetime
from io import StringIO
import csv
import json  # NEW: for parsing JSON payloads if needed

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    abort,
    flash,
    Response,
)
from flask_login import login_required, current_user

from bson.objectid import ObjectId

from app.extensions import db
from app.models import StrokePrediction
from app.db.mongo import get_patient_collection

bp = Blueprint("doctor", __name__, url_prefix="/doctor")


# --------------------------------------------------------------------
# Helper: only doctors allowed (RBAC guard)
# --------------------------------------------------------------------
def _ensure_doctor() -> None:
    # allow both doctor *and* admin into this blueprint
    if (
        not current_user.is_authenticated
        or getattr(current_user, "role", "") not in ("doctor", "admin")
    ):
        abort(403)


# --------------------------------------------------------------------
# ROOT → redirect to dashboard
# --------------------------------------------------------------------
@bp.route("/")
@login_required
def doctor_root():
    _ensure_doctor()
    return redirect(url_for("doctor.doctor_dashboard"))


# --------------------------------------------------------------------
# DOCTOR DASHBOARD
# --------------------------------------------------------------------
@bp.route("/dashboard")
@login_required
def doctor_dashboard():
    _ensure_doctor()

    coll = get_patient_collection()

    # ---------------------------
    # Patient + risk KPIs (Mongo)
    # ---------------------------
    try:
        base_filter: dict = {"system_metadata.is_active": True}

        # total active patients
        my_patients_count = coll.count_documents(base_filter)

        # count high-risk patients (supports both level and _level)
        high_risk_filter = {
            "$and": [
                base_filter,
                {
                    "$or": [
                        {"risk_assessment._level": "High"},
                        {"risk_assessment.level": "High"},
                    ]
                },
            ]
        }
        high_risk_count = coll.count_documents(high_risk_filter)
    except Exception:
        my_patients_count = 0
        high_risk_count = 0

    # ---------------------------
    # Prediction KPIs (SQLite)
    # ---------------------------
    total_predictions = 0
    todays_predictions = 0
    recent_predictions_raw: list[StrokePrediction] = []

    try:
        if hasattr(StrokePrediction, "user_id"):
            q = StrokePrediction.query.filter_by(user_id=current_user.id)

            total_predictions = q.count()

            today_start = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            todays_predictions = (
                q.filter(StrokePrediction.created_at >= today_start).count()
            )

            recent_predictions_raw = (
                q.order_by(StrokePrediction.created_at.desc())
                .limit(5)
                .all()
            )
        else:
            total_predictions = StrokePrediction.query.count()
            recent_predictions_raw = (
                StrokePrediction.query
                .order_by(StrokePrediction.created_at.desc())
                .limit(5)
                .all()
            )
    except Exception:
        total_predictions = 0
        todays_predictions = 0
        recent_predictions_raw = []

    # ---------------------------
    # Build simple rows for the template
    # ---------------------------
    recent_predictions: list[dict] = []

    for p in recent_predictions_raw:
        # raw_features is a JSON dict – may or may not contain patient_id
        try:
            features = p.raw_features or {}
        except Exception:
            features = {}

        patient_id = None
        if isinstance(features, dict):
            # try a few sensible keys
            patient_id = (
                features.get("patient_id")
                or features.get("original_id")
                or features.get("id")
            )

        recent_predictions.append(
            {
                "patient_id": patient_id,
                "risk_level": getattr(p, "risk_level", None),
                "created_at": getattr(p, "created_at", None),
            }
        )

    metrics = {
        "my_patients": my_patients_count,
        "high_risk_patients": high_risk_count,
        "total_predictions": total_predictions,
        "todays_predictions": todays_predictions,
    }

    return render_template(
        "doctor/dashboard.html",
        metrics=metrics,
        recent_predictions=recent_predictions,
    )

# --------------------------------------------------------------------
# Helper to build Mongo filter from querystring (re-used by list + CSV)
# --------------------------------------------------------------------
def _build_patient_filter(
    risk_filter: str,
    search_query: str,
) -> dict:
    mongo_filter: dict = {"system_metadata.is_active": True}

    # Risk filter mapping – support both "level" and "_level"
    if risk_filter in ("high", "medium", "low"):
        label = risk_filter.capitalize()  # "High" / "Medium" / "Low"
        mongo_filter["$or"] = [
            {"risk_assessment.level": label},
            {"risk_assessment._level": label},
        ]

    # Text search (append to existing conditions if present)
    if search_query:
        text_condition = {
            "$or": [
                {"demographics.name": {"$regex": search_query, "$options": "i"}},
                {"demographics.gender": {"$regex": search_query, "$options": "i"}},
                {
                    "medical_history.smoking_status": {
                        "$regex": search_query,
                        "$options": "i",
                    }
                },
            ]
        }

        if "$or" in mongo_filter:
            # already have an $or from risk; combine with $and
            mongo_filter = {
                "$and": [
                    {"system_metadata.is_active": True},
                    {"$or": mongo_filter["$or"]},
                    text_condition,
                ]
            }
        else:
            mongo_filter["$or"] = text_condition["$or"]

    return mongo_filter


# --------------------------------------------------------------------
# PATIENT LIST (READ)
# --------------------------------------------------------------------
@bp.route("/patients", methods=["GET"])
@login_required
def doctor_patients():
    _ensure_doctor()

    coll = get_patient_collection()

    risk_filter = request.args.get("filter", "all")
    search_query = (request.args.get("q") or "").strip()

    mongo_filter = _build_patient_filter(risk_filter, search_query)

    docs = list(
        coll.find(mongo_filter)
        .sort("demographics.age", -1)
        .limit(50)
    )

    patients: list[dict] = []
    for d in docs:
        demo = d.get("demographics", {}) or {}
        risk = d.get("risk_assessment", {}) or {}

        # use "level" / "score", fall back to underscored keys if present
        level = risk.get("level")
        if level is None:
            level = risk.get("_level", "Unknown")

        score = risk.get("score")
        if score is None:
            score = risk.get("_score", 0.0)

        patients.append(
            {
                "id": str(d["_id"]),
                "name": demo.get("name") or f"Patient {d.get('original_id')}",
                "gender": demo.get("gender"),
                "age": demo.get("age"),
                "risk_level": level or "Unknown",
                "risk_score": float(score or 0.0),
            }
        )

    return render_template(
        "doctor/patients.html",
        patients=patients,
        risk_filter=risk_filter,
        search_query=search_query,
    )


# --------------------------------------------------------------------
# EXPORT (scoped CSV, HIPAA-friendly: only current filter/view)
# --------------------------------------------------------------------
@bp.route("/patients/export", methods=["GET"])
@login_required
def doctor_export_patients():
    _ensure_doctor()

    coll = get_patient_collection()

    risk_filter = request.args.get("filter", "all")
    search_query = (request.args.get("q") or "").strip()

    mongo_filter = _build_patient_filter(risk_filter, search_query)

    docs = coll.find(mongo_filter)

    # Build CSV in memory
    output = StringIO()
    writer = csv.writer(output)

    # header
    writer.writerow(
        [
            "patient_id",
            "name",
            "gender",
            "age",
            "work_type",
            "residence_type",
            "hypertension",
            "heart_disease",
            "avg_glucose_level",
            "bmi",
            "smoking_status",
            "dataset_stroke_flag",
            "risk_level",
            "risk_score",
        ]
    )

    for d in docs:
        demo = d.get("demographics", {}) or {}
        med = d.get("medical_history", {}) or {}
        risk = d.get("risk_assessment", {}) or {}

        level = risk.get("level")
        if level is None:
            level = risk.get("_level")

        score = risk.get("score")
        if score is None:
            score = risk.get("_score")

        writer.writerow(
            [
                str(d.get("_id")),
                demo.get("name") or f"Patient {d.get('original_id')}",
                demo.get("gender"),
                demo.get("age"),
                demo.get("work_type"),
                demo.get("residence_type"),
                med.get("hypertension"),
                med.get("heart_disease"),
                med.get("avg_glucose_level"),
                med.get("bmi"),
                med.get("smoking_status"),
                med.get("stroke"),
                level,
                score,
            ]
        )

    csv_data = output.getvalue()
    output.close()

    filename = "stroke_patients_scoped_export.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# --------------------------------------------------------------------
# NEW PATIENT FORM (GET)
# --------------------------------------------------------------------
@bp.route("/patients/new", methods=["GET"])
@login_required
def doctor_new_patient():
    _ensure_doctor()
    return render_template("doctor/patient_new.html")


# --------------------------------------------------------------------
# CREATE (C in CRUD) – add a manual patient (POST)
# --------------------------------------------------------------------
@bp.route("/patients/add", methods=["POST"])
@login_required
def doctor_add_patient():
    _ensure_doctor()

    name = (request.form.get("name") or "").strip()
    gender = (request.form.get("gender") or "").strip() or None
    age_raw = (request.form.get("age") or "").strip()
    work_type = (request.form.get("work_type") or "").strip() or None
    residence_type = (request.form.get("residence_type") or "").strip() or None
    smoking_status = (request.form.get("smoking_status") or "").strip() or None

    # booleans from select
    def _yn_to_int(value: str | None) -> int | None:
        if not value:
            return None
        value = value.lower()
        if value == "yes":
            return 1
        if value == "no":
            return 0
        return None

    hypertension = _yn_to_int(request.form.get("hypertension"))
    heart_disease = _yn_to_int(request.form.get("heart_disease"))
    stroke_flag = _yn_to_int(request.form.get("stroke_flag"))

    # numeric fields
    def _to_float(value: str | None) -> float | None:
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    age = _to_float(age_raw)
    avg_glucose = _to_float(request.form.get("avg_glucose_level"))
    bmi = _to_float(request.form.get("bmi"))

    if not name:
        flash("Patient name is required.", "warning")
        return redirect(url_for("doctor.doctor_new_patient"))

    coll = get_patient_collection()
    now = datetime.utcnow()

    # Manual patient as per your schema
    doc = {
        "original_id": None,  # manual entry, not from Kaggle CSV
        "demographics": {
            "name": name,
            "gender": gender,
            "age": age,
            "ever_married": None,
            "work_type": work_type,
            "residence_type": residence_type,
            "email": None,
        },
        "medical_history": {
            "hypertension": hypertension,
            "heart_disease": heart_disease,
            "avg_glucose_level": avg_glucose,
            "bmi": bmi,
            "smoking_status": smoking_status,
            "stroke": stroke_flag,
        },
        "risk_assessment": {
            # use "score" / "level" to match imported docs
            "score": 0.0,
            "level": "Unknown",   # later: populated by your ML model
            "factors": [],
            "calculated_at": None,
        },
        "system_metadata": {
            "created_by": getattr(current_user, "id", None),
            "created_at": now,
            "last_modified_by": getattr(current_user, "id", None),
            "last_modified_at": now,
            "is_active": True,
        },
    }

    result = coll.insert_one(doc)
    flash("Patient added successfully.", "success")
    return redirect(
        url_for("doctor.doctor_patient_detail", patient_id=str(result.inserted_id))
    )


# --------------------------------------------------------------------
# UPDATE (U in CRUD) – change risk label + (optional) score
# --------------------------------------------------------------------
@bp.route("/patients/<patient_id>/risk", methods=["POST"])
@login_required
def doctor_update_patient_risk(patient_id: str):
    _ensure_doctor()

    new_label = (request.form.get("risk_label") or "Unknown").strip()
    score_raw = (request.form.get("risk_score") or "").strip()

    try:
        new_score = float(score_raw) if score_raw else 0.0
    except ValueError:
        new_score = 0.0

    coll = get_patient_collection()

    try:
        oid = ObjectId(patient_id)
    except Exception:
        abort(404)

    now = datetime.utcnow()

    coll.update_one(
        {"_id": oid, "system_metadata.is_active": True},
        {
            "$set": {
                "risk_assessment.level": new_label,
                "risk_assessment.score": new_score,
                "risk_assessment.calculated_at": now,
                "system_metadata.last_modified_by": getattr(current_user, "id", None),
                "system_metadata.last_modified_at": now,
            }
        },
    )

    flash("Risk level updated.", "success")
    return redirect(url_for("doctor.doctor_patient_detail", patient_id=patient_id))


# --------------------------------------------------------------------
# DELETE (D in CRUD) – soft delete via system_metadata.is_active
# --------------------------------------------------------------------
@bp.route("/patients/<patient_id>/delete", methods=["POST"])
@login_required
def doctor_soft_delete_patient(patient_id: str):
    _ensure_doctor()

    coll = get_patient_collection()

    try:
        oid = ObjectId(patient_id)
    except Exception:
        abort(404)

    now = datetime.utcnow()

    coll.update_one(
        {"_id": oid},
        {
            "$set": {
                "system_metadata.is_active": False,
                "system_metadata.last_modified_by": getattr(current_user, "id", None),
                "system_metadata.last_modified_at": now,
            }
        },
    )

    flash("Patient archived.", "info")
    return redirect(url_for("doctor.doctor_patients"))


# --------------------------------------------------------------------
# PATIENT DETAIL (READ one document)
# --------------------------------------------------------------------
@bp.route("/patients/<patient_id>")
@login_required
def doctor_patient_detail(patient_id: str):
    _ensure_doctor()

    coll = get_patient_collection()
    try:
        oid = ObjectId(patient_id)
    except Exception:
        abort(404)

    doc = coll.find_one(
        {"_id": oid, "system_metadata.is_active": True}
    )
    if not doc:
        abort(404)

    demo = doc.get("demographics", {}) or {}
    med = doc.get("medical_history", {}) or {}
    risk = doc.get("risk_assessment", {}) or {}

    level = risk.get("level")
    if level is None:
        level = risk.get("_level", "Unknown")

    score = risk.get("score")
    if score is None:
        score = risk.get("_score", 0.0)

    patient = {
        "id": str(doc["_id"]),
        "name": demo.get("name") or f"Patient {doc.get('original_id')}",
        "gender": demo.get("gender"),
        "age": demo.get("age"),
        "work_type": demo.get("work_type"),
        "residence_type": demo.get("residence_type"),
        "hypertension": med.get("hypertension"),
        "heart_disease": med.get("heart_disease"),
        "avg_glucose_level": med.get("avg_glucose_level"),
        "bmi": med.get("bmi"),
        "smoking_status": med.get("smoking_status"),
        "stroke_flag": med.get("stroke"),
        "risk_level": level,
        "risk_score": float(score or 0.0),
    }

    prediction_history: list[dict] = []  # later: join with SQLite predictions

    return render_template(
        "doctor/patient_detail.html",
        patient=patient,
        prediction_history=prediction_history,
    )


# --------------------------------------------------------------------
# DOCTOR ANALYTICS (unchanged)
# --------------------------------------------------------------------
@bp.route("/analytics")
@login_required
def doctor_analytics():
    _ensure_doctor()

    total_predictions = 0
    high_risk_predictions = 0
    patients_with_predictions = 0
    recent_predictions: list[StrokePrediction] = []

    try:
        if hasattr(StrokePrediction, "user_id"):
            base_q = StrokePrediction.query.filter_by(user_id=current_user.id)

            total_predictions = base_q.count()
            # if/when you add risk_score, compute high_risk_predictions here

            recent_predictions = (
                base_q.order_by(StrokePrediction.created_at.desc())
                .limit(10)
                .all()
            )
        else:
            total_predictions = StrokePrediction.query.count()
            recent_predictions = (
                StrokePrediction.query
                .order_by(StrokePrediction.created_at.desc())
                .limit(10)
                .all()
            )
    except Exception:
        total_predictions = 0
        high_risk_predictions = 0
        recent_predictions = []

    metrics = {
        "total_predictions": total_predictions,
        "high_risk_predictions": high_risk_predictions,
        "patients_with_predictions": patients_with_predictions,
    }

    return render_template(
        "doctor/analytics.html",
        metrics=metrics,
        recent_predictions=recent_predictions,
    )


# --------------------------------------------------------------------
# DELETE PATIENT RECORD (hard delete) – Admin only
# NOTE: this shares the same URL path as doctor_soft_delete_patient,
# but is referenced by a different endpoint name in templates if used.
# --------------------------------------------------------------------
@bp.route("/patients/<patient_id>/delete", methods=["POST"])
@login_required
def patient_delete(patient_id: str):
    """Soft-delete a patient record – Admin only (see RBAC matrix)."""
    _ensure_doctor()

    # enforce “Admin only” for delete
    if getattr(current_user, "role", "") != "admin":
        abort(403)

    coll = get_patient_collection()

    try:
        coll.update_one(
            {"_id": ObjectId(patient_id)},
            {
                "$set": {
                    "system_metadata.is_active": False,
                    "system_metadata.deleted_at": datetime.utcnow(),
                }
            },
        )
        flash("Patient was archived (soft-deleted) successfully.", "success")
    except Exception:
        flash("Failed to delete patient record.", "danger")

    return redirect(url_for("doctor.doctor_patients"))
