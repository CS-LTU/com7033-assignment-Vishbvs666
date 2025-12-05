# app/routes/admin.py
from __future__ import annotations

from datetime import datetime

from bson.objectid import ObjectId
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    current_app,
    request,
    flash,
    abort,
)
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models import User, StrokePrediction, AuditLog, Session
from app.db.mongo import get_patient_collection

bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def _ensure_admin() -> None:
    """Only allow admin users to access admin pages."""
    if not current_user.is_authenticated or current_user.role != "admin":
        abort(403)


def _admin_dashboard_url() -> str:
    return url_for("admin.admin_dashboard")


def _doc_to_patient_row(doc: dict) -> dict:
    """
    Flatten a Mongo patient document into a simple dict for the template.
    Supports BOTH:
      - imported Kaggle docs with nested demographics / medical_history / risk_assessment
      - manually created docs with flat fields (gender, age, hypertension, stroke, etc.)
    """
    demographics = (doc.get("demographics") or {}) if isinstance(doc.get("demographics"), dict) else {}
    medical = (doc.get("medical_history") or {}) if isinstance(doc.get("medical_history"), dict) else {}
    risk = (doc.get("risk_assessment") or {}) if isinstance(doc.get("risk_assessment"), dict) else {}

    # Basic fields with fallback to flat keys
    gender = demographics.get("gender") or doc.get("gender")
    age = demographics.get("age")
    if age is None:
        age = doc.get("age")

    hypertension = medical.get("hypertension")
    if hypertension is None:
        hypertension = doc.get("hypertension")

    stroke_flag = medical.get("stroke")
    if stroke_flag is None:
        stroke_flag = doc.get("stroke")

    # Risk level from ML / rules
    probability = risk.get("probability")
    level = risk.get("level") or doc.get("risk_label")

    # If we only have probability, derive Low / Medium / High
    if level is None and probability is not None:
        try:
            p = float(probability)
        except (TypeError, ValueError):
            p = 0.0

        if p >= 0.66:
            level = "High"
        elif p >= 0.33:
            level = "Medium"
        else:
            level = "Low"

    return {
        "_id": str(doc.get("_id")),
        "name": doc.get("name"),
        "gender": gender,
        "age": age,
        "hypertension": hypertension,
        "stroke": stroke_flag,
        "risk_level": level,  # used by admin/patients.html
    }


# ---------------------------------------------------------
# ROOT → redirect to dashboard
# ---------------------------------------------------------
@bp.route("/")
@login_required
def admin_root():
    _ensure_admin()
    return redirect(_admin_dashboard_url())


# ---------------------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------------------
@bp.route("/dashboard")
@login_required
def admin_dashboard():
    _ensure_admin()

    # Basic user stats
    total_users = User.query.count()
    admin_count = User.query.filter_by(role="admin").count()
    doctor_count = User.query.filter_by(role="doctor").count()
    hcp_count = User.query.filter_by(role="hcp").count()
    patient_user_count = User.query.filter_by(role="patient").count()

    # Stroke prediction stats
    total_predictions = StrokePrediction.query.count()

    today_start = datetime.utcnow().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    predictions_today = (
        StrokePrediction.query
        .filter(StrokePrediction.created_at >= today_start)
        .count()
    )

    active_sessions = Session.query.count()

    # Recent audit log entries
    recent_logs = (
        AuditLog.query
        .order_by(AuditLog.created_at.desc())
        .limit(6)
        .all()
    )

    metrics = {
        "total_users": total_users,
        "admin_count": admin_count,
        "doctor_count": doctor_count,
        "hcp_count": hcp_count,
        "patient_count": patient_user_count,
        "total_predictions": total_predictions,
        "predictions_today": predictions_today,
        "active_sessions": active_sessions,
    }

    has_predict_view = "predict.predict" in current_app.view_functions

    return render_template(
        "admin/dashboard.html",
        metrics=metrics,
        recent_logs=recent_logs,
        has_predict_view=has_predict_view,
    )


# ---------------------------------------------------------
# ANALYTICS / ACTIVITY
# ---------------------------------------------------------
@bp.route("/analytics")
@login_required
def admin_analytics():
    _ensure_admin()

    total_predictions = StrokePrediction.query.count()

    # count distinct prediction records (no user_id needed)
    try:
        users_with_predictions = (
            db.session.query(
                func.count(func.distinct(StrokePrediction.id))
            ).scalar()
            or 0
        )
    except Exception:
        users_with_predictions = 0

    try:
        recent_predictions = (
            StrokePrediction.query
            .order_by(StrokePrediction.created_at.desc())
            .limit(10)
            .all()
        )
    except Exception:
        recent_predictions = StrokePrediction.query.limit(10).all()

    recent_logs = (
        AuditLog.query
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )

    metrics = {
        "total_predictions": total_predictions,
        "users_with_predictions": users_with_predictions,
    }

    has_predict_view = "predict.predict" in current_app.view_functions

    return render_template(
        "admin/analytics.html",
        metrics=metrics,
        recent_predictions=recent_predictions,
        recent_logs=recent_logs,
        has_predict_view=has_predict_view,
    )


# =========================================================
# USER MANAGEMENT – FULL CRUD (SQLAlchemy / SQLite)
# =========================================================

# LIST
@bp.route("/users")
@login_required
def admin_users():
    _ensure_admin()
    users = User.query.order_by(User.id.desc()).all()
    return render_template("admin/users.html", users=users)


# CREATE
@bp.route("/users/create", methods=["GET", "POST"])
@login_required
def admin_create_user():
    _ensure_admin()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        role = request.form.get("role", "doctor")
        active_flag = request.form.get("is_active") == "on"
        password = request.form.get("password", "").strip()

        if not full_name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return redirect(url_for("admin.admin_create_user"))

        # make sure email is unique
        if User.query.filter_by(email=email).first():
            flash("A user with that email already exists.", "danger")
            return redirect(url_for("admin.admin_create_user"))

        # create and assign attributes explicitly
        user = User()
        setattr(user, "full_name", full_name)
        setattr(user, "email", email)
        setattr(user, "role", role)

        # most likely the real column is `active`; is_active is a property
        if hasattr(user, "active"):
            setattr(user, "active", active_flag)

        # use model helper for password hashing
        if hasattr(user, "set_password"):
            user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("User created successfully.", "success")
        return redirect(url_for("admin.admin_users"))

    return render_template("admin/user_form.html", user=None)


# EDIT
@bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_user(user_id: int):
    _ensure_admin()

    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        role = request.form.get("role", "doctor")
        active_flag = request.form.get("is_active") == "on"
        password = request.form.get("password", "").strip()

        if not full_name or not email:
            flash("Name and email are required.", "danger")
            return redirect(url_for("admin.admin_edit_user", user_id=user.id))

        # check unique email (excluding current user)
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            flash("Another user with that email already exists.", "danger")
            return redirect(url_for("admin.admin_edit_user", user_id=user.id))

        setattr(user, "full_name", full_name)
        setattr(user, "email", email)
        setattr(user, "role", role)
        if hasattr(user, "active"):
            setattr(user, "active", active_flag)

        if password and hasattr(user, "set_password"):
            user.set_password(password)

        db.session.commit()
        flash("User updated successfully.", "success")
        return redirect(url_for("admin.admin_users"))

    return render_template("admin/user_form.html", user=user)


# DELETE
@bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def admin_delete_user(user_id: int):
    _ensure_admin()

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot delete your own admin account.", "warning")
        return redirect(url_for("admin.admin_users"))

    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.", "success")
    return redirect(url_for("admin.admin_users"))


# =========================================================
# PATIENT MANAGEMENT – FULL CRUD (MongoDB)
# =========================================================

# LIST
@bp.route("/patients")
@login_required
def admin_patients():
    _ensure_admin()
    coll = get_patient_collection()

    # Fetch all docs and flatten them so template gets risk_level etc.
    docs = coll.find({})
    patients = [_doc_to_patient_row(d) for d in docs]

    return render_template("admin/patients.html", patients=patients)


# CREATE
@bp.route("/patients/create", methods=["GET", "POST"])
@login_required
def admin_create_patient():
    _ensure_admin()
    coll = get_patient_collection()

    if request.method == "POST":
        doc = {
            "patient_id": request.form.get("patient_id", "").strip(),
            "name": request.form.get("name", "").strip(),
            "gender": request.form.get("gender", "").strip(),
            "age": float(request.form.get("age") or 0),
            "hypertension": int(request.form.get("hypertension") or 0),
            "ever_married": request.form.get("ever_married", "").strip(),
            "work_type": request.form.get("work_type", "").strip(),
            "residence_type": request.form.get("residence_type", "").strip(),
            "avg_glucose_level": float(
                request.form.get("avg_glucose_level") or 0
            ),
            "bmi": float(request.form.get("bmi") or 0),
            "smoking_status": request.form.get("smoking_status", "").strip(),
            "stroke": int(request.form.get("stroke") or 0),
            "created_at": datetime.utcnow(),
        }

        coll.insert_one(doc)
        flash("Patient record created.", "success")
        return redirect(url_for("admin.admin_patients"))

    return render_template("admin/patient_form.html", patient=None)


# EDIT
@bp.route("/patients/<string:patient_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_patient(patient_id: str):
    _ensure_admin()
    coll = get_patient_collection()

    try:
        obj_id = ObjectId(patient_id)
    except Exception:
        abort(404)

    patient = coll.find_one({"_id": obj_id})
    if not patient:
        abort(404)

    if request.method == "POST":
        update_doc = {
            "patient_id": request.form.get("patient_id", "").strip(),
            "name": request.form.get("name", "").strip(),
            "gender": request.form.get("gender", "").strip(),
            "age": float(request.form.get("age") or 0),
            "hypertension": int(request.form.get("hypertension") or 0),
            "ever_married": request.form.get("ever_married", "").strip(),
            "work_type": request.form.get("work_type", "").strip(),
            "residence_type": request.form.get("residence_type", "").strip(),
            "avg_glucose_level": float(
                request.form.get("avg_glucose_level") or 0
            ),
            "bmi": float(request.form.get("bmi") or 0),
            "smoking_status": request.form.get("smoking_status", "").strip(),
            "stroke": int(request.form.get("stroke") or 0),
        }

        coll.update_one({"_id": obj_id}, {"$set": update_doc})
        flash("Patient record updated.", "success")
        return redirect(url_for("admin.admin_patients"))

    # convert ObjectId to string so the template can use it in URLs
    patient["_id"] = str(patient["_id"])
    return render_template("admin/patient_form.html", patient=patient)


# DELETE
@bp.route("/patients/<string:patient_id>/delete", methods=["POST"])
@login_required
def admin_delete_patient(patient_id: str):
    _ensure_admin()
    coll = get_patient_collection()

    try:
        obj_id = ObjectId(patient_id)
    except Exception:
        abort(404)

    coll.delete_one({"_id": obj_id})
    flash("Patient record deleted.", "success")
    return redirect(url_for("admin.admin_patients"))
