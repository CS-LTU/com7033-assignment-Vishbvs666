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

"""
Import Kaggle stroke CSV into MongoDB and run the ML model
for each patient row *during* import.

- Reads the standard Kaggle file:
    id, gender, age, hypertension, heart_disease,
    ever_married, work_type, Residence_type,
    avg_glucose_level, bmi, smoking_status, stroke

- Builds a MongoDB document in the same shape as the rest of the app:
    demographics, medical_history, risk_assessment, system_metadata

- Calls app.ml.predict_service.run_ml_on_patient_doc(doc)
  BEFORE inserting, so every new patient has:

    risk_assessment._score   (float 0–1)
    risk_assessment._level   ("Low" / "Medium" / "High")
    risk_assessment._flag    (0/1)
    risk_assessment._calculated_at (UTC datetime)

Usage (from project root, with venv active):

    python -m scripts.import_kaggle_with_ml path/to/healthcare-dataset-stroke-data.csv

If you omit the path, it defaults to:
    data/healthcare-dataset-stroke-data.csv
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

from app import create_app
from app.db.mongo import get_patient_collection
from app.ml.predict_service import run_ml_on_patient_doc  # ML helper


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if not value or value.lower() in {"na", "n/a", "nan"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _build_doc_from_row(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Convert a Kaggle CSV row into a MongoDB patient document
    (without ML fields yet).
    """
    # Kaggle columns (canonical):
    # id, gender, age, hypertension, heart_disease,
    # ever_married, work_type, Residence_type,
    # avg_glucose_level, bmi, smoking_status, stroke

    original_id = _to_int(row.get("id"))

    demographics = {
        "name": None,  # Kaggle data has no names
        "gender": (row.get("gender") or "").strip() or None,
        "age": _to_float(row.get("age")),
        "ever_married": (row.get("ever_married") or "").strip() or None,
        "work_type": (row.get("work_type") or "").strip() or None,
        "residence_type": (row.get("Residence_type") or "").strip() or None,
        "email": None,
    }

    medical_history = {
        "hypertension": _to_int(row.get("hypertension")),
        "heart_disease": _to_int(row.get("heart_disease")),
        "avg_glucose_level": _to_float(row.get("avg_glucose_level")),
        "bmi": _to_float(row.get("bmi")),
        "smoking_status": (row.get("smoking_status") or "").strip() or None,
        "stroke": _to_int(row.get("stroke")),
    }

    now = datetime.utcnow()

    # Placeholder; will be overwritten after ML call
    risk_assessment = {
        "_score": 0.0,
        "_level": "Unknown",
        "_flag": 0,
        "_factors": [],
        "_calculated_at": None,
    }

    system_metadata = {
        "is_active": True,
        "created_at": now,
        "last_modified_at": now,
        "created_by_role": "script",
        "created_by": None,
        "import_source": "kaggle_csv",
    }

    doc: Dict[str, Any] = {
        "original_id": original_id,
        "demographics": demographics,
        "medical_history": medical_history,
        "risk_assessment": risk_assessment,
        "system_metadata": system_metadata,
    }
    return doc


def _apply_ml_to_doc(doc: Dict[str, Any]) -> Tuple[float, int, str]:
    """
    Run the trained ML model on the patient document
    using the shared predict_service helper.
    """
    # This returns: probability (0–1), stroke_flag (0/1), risk_level ("Low"/"Medium"/"High")
    proba, stroke_flag, risk_level = run_ml_on_patient_doc(doc)
    now = datetime.utcnow()

    doc.setdefault("risk_assessment", {})
    doc["risk_assessment"].update(
        {
            "_score": proba,
            "_level": risk_level,
            "_flag": stroke_flag,
            "_calculated_at": now,
        }
    )

    # Update last_modified_at as well
    meta = doc.setdefault("system_metadata", {})
    meta["last_modified_at"] = now

    return proba, stroke_flag, risk_level


# ----------------------------------------------------------------------
# Main import routine
# ----------------------------------------------------------------------
def import_kaggle_with_ml(csv_path: Path) -> None:
    coll = get_patient_collection()

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    print(f"📄 Loading Kaggle stroke CSV from: {csv_path}")

    inserted = 0
    skipped = 0

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, start=1):
            try:
                doc = _build_doc_from_row(row)

                # Skip obviously bad rows (no age + no glucose + no BMI)
                demo = doc.get("demographics", {})
                med = doc.get("medical_history", {})
                if (
                    demo.get("age") is None
                    and med.get("avg_glucose_level") is None
                    and med.get("bmi") is None
                ):
                    skipped += 1
                    print(f"  · Skipping row {idx}: insufficient data")
                    continue

                # Run ML scoring BEFORE insert
                proba, stroke_flag, risk_level = _apply_ml_to_doc(doc)

                coll.insert_one(doc)
                inserted += 1

                if inserted % 500 == 0:
                    print(
                        f"  ✔ Imported {inserted} patients so far "
                        f"(last: score={proba:.2f}, level={risk_level})"
                    )

            except Exception as exc:
                skipped += 1
                print(f"  ! Error on row {idx}: {exc!r} — row skipped")

    print("\nImport complete.")
    print(f"   Inserted: {inserted} patients")
    print(f"   Skipped : {skipped} rows")


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    # Decide CSV path: from argv or default
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1]).expanduser().resolve()
    else:
        csv_path = Path("data") / "healthcare-dataset-stroke-data.csv"

    app = create_app()
    with app.app_context():
        import_kaggle_with_ml(csv_path)


if __name__ == "__main__":
    main()
