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

CSV_PATH = Path("data/healthcare-dataset-stroke-data.csv")

# Set True only if you intentionally want a clean slate.
CLEAR_FIRST = False


def _compute_rule_based_risk(row: dict) -> tuple[float, str]:
    score = 0.0

    age = float(row.get("age", 0) or 0)
    hypertension = int(row.get("hypertension", 0) or 0)
    heart_disease = int(row.get("heart_disease", 0) or 0)
    avg_glucose = float(row.get("avg_glucose_level", 0) or 0)
    bmi_raw = (row.get("bmi") or "").strip()
    smoking_status = (row.get("smoking_status") or "").lower()
    stroke_flag = int(row.get("stroke", 0) or 0)

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
            pass
    else:
        score += 0.5

    if smoking_status in {"formerly smoked", "smokes"}:
        score += 1

    if stroke_flag == 1:
        score += 2

    if score <= 2:
        level = "Low"
    elif score <= 4:
        level = "Medium"
    else:
        level = "High"

    return score, level


def row_to_patient_doc(row: dict) -> dict:
    rule_score, rule_level = _compute_rule_based_risk(row)

    bmi_raw = (row.get("bmi") or "").strip()
    bmi_val = None
    if bmi_raw:
        try:
            bmi_val = float(bmi_raw)
        except ValueError:
            bmi_val = None

    now = datetime.utcnow()

    original_id = int(row["id"])
    gender = row.get("gender")
    age = float(row.get("age", 0) or 0)

    doc = {
        "original_id": original_id,
        "demographics": {
            "name": None,
            "gender": gender,
            "age": age,
            "ever_married": row.get("ever_married"),
            "work_type": row.get("work_type"),
            "residence_type": row.get("Residence_type"),
            "email": None,
        },
        "medical_history": {
            "hypertension": int(row.get("hypertension", 0) or 0),
            "heart_disease": int(row.get("heart_disease", 0) or 0),
            "avg_glucose_level": float(row.get("avg_glucose_level", 0) or 0),
            "bmi": bmi_val,
            "smoking_status": row.get("smoking_status"),
            "stroke": int(row.get("stroke", 0) or 0),
        },
        "risk_assessment": {
            "score": float(rule_score),
            "level": rule_level,
            "flag": 0,
            "factors": [],
            "calculated_at": None,
        },
        "system_metadata": {
            "created_at": now,
            "created_by": None,
            "created_by_role": "script",
            "last_modified_at": now,
            "last_modified_by": None,
            "is_active": True,
            "import_source": "kaggle_csv",
        },
    }

    return doc


def main() -> None:
    app = create_app()

    with app.app_context():
        coll = get_patient_collection()

        if CLEAR_FIRST:
            deleted = coll.delete_many({})
            print(f"Cleared {deleted.deleted_count} existing patient docs from MongoDB.")

        if not CSV_PATH.exists():
            raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")

        with CSV_PATH.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            upserted = 0
            skipped = 0

            for idx, row in enumerate(reader, start=1):
                try:
                    doc = row_to_patient_doc(row)

                    # ML prediction
                    proba, flag, level = run_ml_on_patient_doc(doc)
                    now = datetime.utcnow()

                    doc["risk_assessment"]["score"] = float(proba)
                    doc["risk_assessment"]["level"] = level
                    doc["risk_assessment"]["flag"] = int(flag)
                    doc["risk_assessment"]["calculated_at"] = now
                    doc["system_metadata"]["last_modified_at"] = now

                    # UPSERT by original_id
                    res = coll.update_one(
                        {"original_id": doc["original_id"]},
                        {"$set": doc},
                        upsert=True,
                    )

                    if res.upserted_id is not None or res.modified_count > 0:
                        upserted += 1

                except Exception as exc:
                    skipped += 1
                    print(f"[WARN] Row {idx} import failed (id={row.get('id')}): {exc}")

            print(f"Upserted {upserted} patient records into MongoDB.")
            if skipped:
                print(f"Skipped {skipped} rows.")


if __name__ == "__main__":
    main()
