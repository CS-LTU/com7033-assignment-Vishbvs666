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
    Extracts and normalises the 10 Kaggle features from the HTML form.
    """

    def _float(name: str) -> float | None:
        val = form.get(name, "").strip()
        if not val:
            return None
        try:
            return float(val)
        except ValueError:
            return None

    features: Dict[str, Any] = {
        "gender": form.get("gender") or None,
        "age": _float("age"),
        "hypertension": 1 if form.get("hypertension") == "Yes" else 0,
        "heart_disease": 1 if form.get("heart_disease") == "Yes" else 0,
        "ever_married": form.get("ever_married") or None,
        "work_type": form.get("work_type") or None,
        "Residence_type": form.get("residence_type") or None,
        "avg_glucose_level": _float("avg_glucose_level"),
        "bmi": _float("bmi"),
        "smoking_status": form.get("smoking_status") or None,
    }

    return features


# ----------------------------------------------------------------------
# /predict/ – show form + handle submission
# ----------------------------------------------------------------------
@bp.route("/", methods=["GET", "POST"])
@login_required
def predict() -> str:
    if request.method == "POST":
        # Optional doctor-only Patient ID
        patient_id = (request.form.get("patient_id") or "").strip() or None

        # 1) Gather features from form
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

        # Attach patient_id only if model supports it
        if patient_id and hasattr(pred, "patient_id"):
            pred.patient_id = patient_id

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
