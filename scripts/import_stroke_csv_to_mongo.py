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

# scripts/import_stroke_csv_to_mongo.py
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from app import create_app
from app.db.mongo import get_patient_collection
from app.ml.predict_service import run_ml_on_patient_doc

# Path to the Kaggle CSV (relative to project root)
CSV_PATH = Path("data/healthcare-dataset-stroke-data.csv")


def _compute_rule_based_risk(row: dict) -> tuple[float, str]:
    """
    Very simple rule-based risk score just so your demo
    still has a fallback if ML fails for some row.
    """
    score = 0.0

    age = float(row.get("age", 0) or 0)
    hypertension = int(row.get("hypertension", 0) or 0)
    heart_disease = int(row.get("heart_disease", 0) or 0)
    avg_glucose = float(row.get("avg_glucose_level", 0) or 0)
    bmi_raw = (row.get("bmi") or "").strip()
    smoking_status = (row.get("smoking_status") or "").lower()
    stroke_flag = int(row.get("stroke", 0) or 0)

    # Basic additive risk rules
    if age >= 65:
        score += 3
    if hypertension == 1:
        score += 2
    if heart_disease == 1:
        score += 2
    if avg_glucose > 200:
        score += 2

    if bmi_raw:
        try:
            bmi_val = float(bmi_raw)
            if bmi_val >= 30:
                score += 1
        except ValueError:
            # ignore weird BMI values
            pass
    else:
        # Missing BMI → slight uncertainty bump
        score += 0.5

    if smoking_status in {"formerly smoked", "smokes"}:
        score += 1

    # If stroke already occurred in dataset, bump risk
    if stroke_flag == 1:
        score += 2

    # Classification thresholds
    if score <= 2:
        level = "Low"
    elif score <= 4:
        level = "Medium"
    else:
        level = "High"

    return score, level


def row_to_patient_doc(row: dict) -> dict:
    """
    Map one CSV row from Kaggle into the MongoDB patient
    document schema (with both flat and nested fields).
    """
    rule_score, rule_level = _compute_rule_based_risk(row)

    bmi_raw = (row.get("bmi") or "").strip()
    bmi_val = None
    if bmi_raw:
        try:
            bmi_val = float(bmi_raw)
        except ValueError:
            bmi_val = None

    original_id = int(row["id"])
    gender = row.get("gender")
    age = float(row.get("age", 0) or 0)
    hypertension = int(row.get("hypertension", 0) or 0)
    stroke_flag = int(row.get("stroke", 0) or 0)

    doc = {
        # --- top-level convenience fields for UI & filters ---
        "original_id": original_id,
        "name": None,                   # CSV has no name → show "-" or blank in UI
        "gender": gender,
        "age": age,
        "hypertension": hypertension,
        "stroke_flag": stroke_flag,
        "ever_married": row.get("ever_married"),
        "work_type": row.get("work_type"),
        "Residence_type": row.get("Residence_type"),
        "avg_glucose_level": float(row.get("avg_glucose_level", 0) or 0),
        "bmi": bmi_val,
        "smoking_status": row.get("smoking_status"),

        # --- nested structure for richer queries / future features ---
        "demographics": {
            "gender": gender,
            "age": age,
            "ever_married": row.get("ever_married"),
            "work_type": row.get("work_type"),
            "residence_type": row.get("Residence_type"),
        },
        "medical_history": {
            "hypertension": hypertension,
            "heart_disease": int(row.get("heart_disease", 0) or 0),
            "avg_glucose_level": float(row.get("avg_glucose_level", 0) or 0),
            "bmi": bmi_val,
            "smoking_status": row.get("smoking_status"),
            "stroke": stroke_flag,
        },
        "risk_assessment": {
            # will be overridden by ML predictions
            "score": rule_score,
            "level": rule_level,
            "factors": [],
            "last_calculated": None,
        },
        "system_metadata": {
            "created_at": None,     # dataset import → no creator
            "created_by": None,
            "last_modified_at": None,
            "last_modified_by": None,
            "is_active": True,      # soft-delete flag
        },
        # Convenience top-level field for UI filtering
        "risk_label": rule_level,
    }

    return doc


def main() -> None:
    # Use default Config from root/config.py via create_app()
    app = create_app()

    with app.app_context():
        coll = get_patient_collection()

        # Clear existing docs so we don't duplicate
        deleted = coll.delete_many({})
        print(f"Cleared {deleted.deleted_count} existing patient docs from MongoDB.")

        if not CSV_PATH.exists():
            raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")

        with CSV_PATH.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            inserted = 0
            for row in reader:
                # 1) Build base document from CSV
                doc = row_to_patient_doc(row)

                # 2) Run ML model on this patient document
                try:
                    proba, flag, level = run_ml_on_patient_doc(doc)

                    doc["risk_assessment"]["score"] = float(proba)
                    doc["risk_assessment"]["level"] = level
                    doc["risk_assessment"]["last_calculated"] = datetime.utcnow()

                    doc["risk_label"] = level
                    doc["ml_prediction"] = int(flag)
                    doc["ml_prediction_label"] = "Stroke" if flag == 1 else "No stroke"
                except Exception as exc:  # pragma: no cover – demo safety
                    print(f"[WARN] ML prediction failed for row id={row.get('id')}: {exc}")
                    # keep rule-based score/level if ML fails

                # 3) Insert into MongoDB
                coll.insert_one(doc)
                inserted += 1

            print(f"Imported {inserted} patient records into MongoDB.")


if __name__ == "__main__":
    main()
