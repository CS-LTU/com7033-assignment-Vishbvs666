# app/routes/hcp.py
from __future__ import annotations

from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    abort,
)
from flask_login import login_required, current_user
from bson.objectid import ObjectId

from app.db.mongo import get_patient_collection

bp = Blueprint("hcp", __name__, url_prefix="/hcp")


# --------------------------------------------------------------------
# Helper: only HCPs allowed (RBAC guard)
# --------------------------------------------------------------------
def _ensure_hcp() -> None:
    """Only allow users with role 'hcp' to access these views."""
    if not current_user.is_authenticated or getattr(current_user, "role", "") != "hcp":
        abort(403)


# --------------------------------------------------------------------
# ROOT → redirect to dashboard
# --------------------------------------------------------------------
@bp.route("/")
@login_required
def hcp_root():
    _ensure_hcp()
    return redirect(url_for("hcp.hcp_dashboard"))


# --------------------------------------------------------------------
# HCP DASHBOARD
# --------------------------------------------------------------------
@bp.route("/dashboard")
@login_required
def hcp_dashboard():
    """
    HCP overview dashboard.

    For the assignment we treat all active patients as 'assigned'.
    In a real system we’d also scope to patients linked to this HCP.
    """
    _ensure_hcp()
    coll = get_patient_collection()

    try:
        base_filter: dict = {"system_metadata.is_active": True}

        assigned_patients = coll.count_documents(base_filter)

        high_risk_filter = base_filter | {"risk_assessment._level": "High"}
        high_risk_patients = coll.count_documents(high_risk_filter)
    except Exception:
        assigned_patients = 0
        high_risk_patients = 0

    metrics = {
        "assigned_patients": assigned_patients,
        "high_risk_patients": high_risk_patients,
        "tasks_today": 0,
        "notes_to_review": 0,
    }

    recent_updates: list[dict] = []

    return render_template(
        "hcp/dashboard.html",
        metrics=metrics,
        recent_updates=recent_updates,
    )


# --------------------------------------------------------------------
# ASSIGNED PATIENTS LIST (can view + add + delete)
# --------------------------------------------------------------------
@bp.route("/patients")
@login_required
def hcp_patients():
    """
    HCP patient list.

    • Looks like the doctor patient list.
    • Read-only demographics + risk, but HCP can add/delete records.
    """
    _ensure_hcp()
    coll = get_patient_collection()

    # Search + risk filter (same shape as doctor view)
    search_query = (request.args.get("q") or "").strip()
    risk_filter = request.args.get("risk_filter", "all")

    mongo_filter: dict = {"system_metadata.is_active": True}

    # (In a real system you’d also scope to this HCP’s caseload.)

    # Risk filter mapping – same categories as doctor
    risk_map = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "unknown": "Unknown",
    }
    if risk_filter in risk_map:
        mongo_filter["risk_assessment._level"] = risk_map[risk_filter]

    # Simple text search over name / original_id
    if search_query:
        mongo_filter["$or"] = [
            {"demographics.name": {"$regex": search_query, "$options": "i"}},
            {"original_id": {"$regex": search_query, "$options": "i"}},
        ]

    try:
        docs = (
            coll.find(mongo_filter)
            .sort("original_id", 1)
            .limit(50)
        )
    except Exception:
        docs = []

    patients: list[dict] = []
    for d in docs:
        demo = d.get("demographics", {}) or {}
        risk = d.get("risk_assessment", {}) or {}

        patients.append(
            {
                "id": str(d["_id"]),
                "name": demo.get("name") or f"Patient {d.get('original_id')}",
                "age": demo.get("age"),
                "sex": demo.get("gender"),
                "risk_level": risk.get("_level", "Unknown"),
                # IMPORTANT: use the ML field `_score`, not legacy `score`
                "risk_score": float(risk.get("_score") or 0.0),
            }
        )

    return render_template(
        "hcp/patients.html",
        patients=patients,
        risk_filter=risk_filter,
        search_query=search_query,
        total_count=len(patients),
    )


# --------------------------------------------------------------------
# ADD PATIENT (HCP can create manual records)
# --------------------------------------------------------------------
@bp.route("/patients/new", methods=["GET", "POST"])
@login_required
def hcp_patient_new():
    _ensure_hcp()
    coll = get_patient_collection()

    if request.method == "POST":
        form = request.form

        def _to_float(value: str | None) -> float | None:
            if not value:
                return None
            try:
                return float(value)
            except ValueError:
                return None

        demo = {
            "name": (form.get("name") or "").strip() or None,
            "gender": form.get("gender") or None,
            "age": _to_float(form.get("age")),
            "work_type": form.get("work_type") or None,
            "residence_type": form.get("residence_type") or None,
            "hypertension": (form.get("hypertension") == "yes"),
            "heart_disease": (form.get("heart_disease") == "yes"),
            "avg_glucose_level": _to_float(form.get("avg_glucose_level")),
            "bmi": _to_float(form.get("bmi")),
            "smoking_status": form.get("smoking_status") or None,
            "dataset_stroke_flag": form.get("dataset_stroke_flag") or None,
        }

        now = datetime.utcnow()
        doc = {
            "original_id": None,
            "demographics": demo,
            "risk_assessment": {
                "_level": "Unknown",
                "_score": 0.0,
                "_factors": [],
                "_calculated_at": None,
            },
            "system_metadata": {
                "is_active": True,
                "created_at": now,
                "last_modified_at": now,
                "created_by_role": "hcp",
                "created_by": getattr(current_user, "id", None),
            },
        }

        coll.insert_one(doc)
        return redirect(url_for("hcp.hcp_patients"))

    # GET → show form
    return render_template("hcp/patient_form.html")


# --------------------------------------------------------------------
# DELETE PATIENT (soft delete)
# --------------------------------------------------------------------
@bp.route("/patients/<patient_id>/delete", methods=["POST"])
@login_required
def hcp_patient_delete(patient_id: str):
    _ensure_hcp()
    coll = get_patient_collection()

    try:
        coll.update_one(
            {"_id": ObjectId(patient_id)},
            {
                "$set": {
                    "system_metadata.is_active": False,
                    "system_metadata.last_modified_at": datetime.utcnow(),
                    "system_metadata.deleted_by_role": "hcp",
                    "system_metadata.deleted_by": getattr(current_user, "id", None),
                }
            },
        )
    except Exception:
        # For the assignment we just fail silently and go back to list
        pass

    return redirect(url_for("hcp.hcp_patients"))


# --------------------------------------------------------------------
# PATIENT CARE VIEW
# --------------------------------------------------------------------
@bp.route("/patients/<patient_id>")
@login_required
def hcp_patient_detail(patient_id: str):
    _ensure_hcp()

    coll = get_patient_collection()
    patient = None
    vitals: list[dict] = []
    medications: list[dict] = []
    notes: list[dict] = []
    tasks: list[dict] = [
        {
            "patient_id": "P001",
            "patient_name": "CherryPixels",
            "label": "Morning vitals check",
            "due_time": "09:00",
            "done": False,
        },
        {
            "patient_id": "P067",
            "patient_name": "Patient 67",
            "label": "Medication reminder – Aspirin 75mg",
            "due_time": "12:00",
            "done": False,
        },
        {
            "patient_id": "P084",
            "patient_name": "Patient 84",
            "label": "Record blood glucose",
            "due_time": "15:00",
            "done": True,
        },
    ]

    try:
        d = coll.find_one(
            {"_id": ObjectId(patient_id), "system_metadata.is_active": True}
        )
        if d:
            demo = d.get("demographics", {}) or {}
            risk = d.get("risk_assessment", {}) or {}
            patient = {
                "id": str(d["_id"]),
                "name": demo.get("name") or f"Patient {d.get('original_id')}",
                "age": demo.get("age"),
                "sex": demo.get("gender"),
                "risk_level": risk.get("_level", "Unknown"),
                "risk_score": risk.get("_score", 0.0),
            }
    except Exception:
        patient = None

    return render_template(
        "hcp/patient_detail.html",
        patient=patient,
        vitals=vitals,
        medications=medications,
        notes=notes,
        tasks=tasks,
    )


# --------------------------------------------------------------------
# TODAY'S TASKS VIEW (placeholder)
# --------------------------------------------------------------------
@bp.route("/tasks")
@login_required
def hcp_tasks():
    _ensure_hcp()

    tasks: list[dict] = []
    return render_template("hcp/tasks.html", tasks=tasks)


# --------------------------------------------------------------------
# MONITORING & ALERTS (placeholder lists)
# --------------------------------------------------------------------
@bp.route("/monitoring")
@login_required
def hcp_monitoring():
    _ensure_hcp()

    trend_items: list[dict] = [
        {
            "patient_name": "CherryPixels",
            "summary": "BP trending upward over last 3 days",
        },
        {
            "patient_name": "Patient 84",
            "summary": "Glucose fluctuating – monitor closely",
        },
    ]
    alerts: list[dict] = [
        {
            "severity": "High",
            "message": "Stroke risk score exceeded 0.7 threshold",
            "when": "2025-12-03 09:10",
        },
        {
            "severity": "Medium",
            "message": "Unusual heart rate pattern detected",
            "when": "2025-12-03 11:45",
        },
    ]
    communications: list[dict] = [
        {
            "from": "Dr. Markus",
            "message": "Please schedule a follow-up for CherryPixels tomorrow.",
            "when": "2025-12-02 18:30",
        },
        {
            "from": "Dr. Lina",
            "message": "Ensure Patient 84 receives medication on time.",
            "when": "2025-12-03 08:15",
        },
    ]

    return render_template(
        "hcp/monitoring.html",
        trend_items=trend_items,
        alerts=alerts,
        communications=communications,
    )


# --------------------------------------------------------------------
# VIEW HIGH-RISK PATIENTS
# --------------------------------------------------------------------
@bp.route("/patients/high")
@login_required
def hcp_patients_high():
    _ensure_hcp()

    coll = get_patient_collection()

    mongo_filter = {
        "system_metadata.is_active": True,
        "risk_assessment._level": "High",
    }

    docs = list(
        coll.find(mongo_filter)
        .sort("demographics.age", -1)
        .limit(50)
    )

    patients: list[dict] = []
    for d in docs:
        demo = d.get("demographics", {}) or {}
        risk = d.get("risk_assessment", {}) or {}
        meta = d.get("system_metadata", {}) or {}

        patients.append(
            {
                "id": str(d["_id"]),
                "name": demo.get("name") or f"Patient {d.get('original_id')}",
                "age": demo.get("age"),
                "sex": demo.get("gender"),
                "risk_level": risk.get("_level", "Unknown"),
                "risk_score": risk.get("_score", 0.0),
                "last_update": meta.get("last_modified_at"),
            }
        )

    return render_template("hcp/patients_high.html", patients=patients)
