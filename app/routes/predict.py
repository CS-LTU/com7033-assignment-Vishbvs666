# app/routes/predict.py
# pyright: reportAttributeAccessIssue=false, reportCallIssue=false

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.ml import predict_risk
from app.models.stroke_prediction import StrokePrediction

bp = Blueprint("predict", __name__, url_prefix="/predict")


# ----------------------------------------------------------------------
# Helper: convert form data → feature dict expected by predict_risk()
# ----------------------------------------------------------------------
def _features_from_form(form) -> Dict[str, Any]:
    """
    Extracts and normalises the 10 Kaggle features (+ optional patient_id)
    from the HTML form.

    Used by both the /predict view and tests/test_predict_form_features.py
    """

    def _float(name: str) -> float | None:
        val = (form.get(name, "") or "").strip()
        if not val:
            return None
        try:
            return float(val)
        except ValueError:
            return None

    # Optional patient ID (doctor-facing only, tests expect this key)
    raw_pid = (form.get("patient_id") or "").strip()
    patient_id = raw_pid or None

    features: Dict[str, Any] = {
        "gender": form.get("gender") or None,
        "age": _float("age"),
        # Accept both "Yes"/"No" (tests) and "1"/"0" (HTML select)
        "hypertension": 1
        if form.get("hypertension") in ("Yes", "1", "true", "True")
        else 0,
        "heart_disease": 1
        if form.get("heart_disease") in ("Yes", "1", "true", "True")
        else 0,
        "ever_married": form.get("ever_married") or None,
        "work_type": form.get("work_type") or None,
        # form field is "residence_type"; feature key is "Residence_type"
        "Residence_type": form.get("residence_type")
        or form.get("Residence_type")
        or None,
        "avg_glucose_level": _float("avg_glucose_level"),
        "bmi": _float("bmi"),
        "smoking_status": form.get("smoking_status") or None,
        # extra – used by tests and optionally by doctor UI
        "patient_id": patient_id,
    }

    return features


# ----------------------------------------------------------------------
# /predict/ – show form + handle submission
# ----------------------------------------------------------------------
@bp.route("/", methods=["GET", "POST"])
@login_required
def predict() -> str:
    if request.method == "POST":
        # 1) Gather features from form (includes optional patient_id)
        features = _features_from_form(request.form)

        # 2) Run ML model
        result = predict_risk(features)
        # result looks like:
        # {"probability": 0.73, "stroke_flag": 1, "risk_level": "High"}

        # 3) Save to database
        pred = StrokePrediction(
            user_id=current_user.id if current_user.is_authenticated else None,
            probability=float(result.get("probability", 0.0)),
            stroke_flag=int(result.get("stroke_flag", 0)),
            risk_level=str(result.get("risk_level", "Low")),
            raw_features=features,
            created_at=datetime.utcnow(),
        )

        # If StrokePrediction model has patient_id and we got one, attach it
        if hasattr(pred, "patient_id") and features.get("patient_id"):
            pred.patient_id = features["patient_id"]

        db.session.add(pred)
        db.session.commit()

        flash("Stroke risk prediction generated.", "success")

        # 4) Render the result page
        return render_template(
            "predict/result.html",
            result=result,
            features=features,
            prediction=pred,
        )

    # GET – just show the prediction form
    return render_template("predict/form.html")
