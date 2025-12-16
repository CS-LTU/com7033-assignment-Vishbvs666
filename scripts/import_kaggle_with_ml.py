from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

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
    Convert a Kaggle CSV row into a MongoDB patient document (base schema).
    """
    original_id = _to_int(row.get("id"))
    now = datetime.utcnow()

    doc: Dict[str, Any] = {
        "original_id": original_id,
        "demographics": {
            "name": None,  # Kaggle has no names
            "gender": (row.get("gender") or "").strip() or None,
            "age": _to_float(row.get("age")),
            "ever_married": (row.get("ever_married") or "").strip() or None,
            "work_type": (row.get("work_type") or "").strip() or None,
            "residence_type": (row.get("Residence_type") or "").strip() or None,
            "email": None,
        },
        "medical_history": {
            "hypertension": _to_int(row.get("hypertension")),
            "heart_disease": _to_int(row.get("heart_disease")),
            "avg_glucose_level": _to_float(row.get("avg_glucose_level")),
            "bmi": _to_float(row.get("bmi")),
            "smoking_status": (row.get("smoking_status") or "").strip() or None,
            "stroke": _to_int(row.get("stroke")),
        },
        "risk_assessment": {
            "score": 0.0,
            "level": "Unknown",
            "flag": 0,
            "factors": [],
            "calculated_at": None,
        },
        "system_metadata": {
            "is_active": True,
            "created_at": now,
            "last_modified_at": now,
            "created_by_role": "script",
            "created_by": None,
            "import_source": "kaggle_csv",
        },
    }
    return doc


def _apply_ml_to_doc(doc: Dict[str, Any]) -> None:
    """
    Run ML model and update risk_assessment fields in-place.
    """
    proba, stroke_flag, risk_level = run_ml_on_patient_doc(doc)
    now = datetime.utcnow()

    doc.setdefault("risk_assessment", {})
    doc["risk_assessment"].update(
        {
            "score": float(proba),
            "level": risk_level,
            "flag": int(stroke_flag),
            "calculated_at": now,
        }
    )

    meta = doc.setdefault("system_metadata", {})
    meta["last_modified_at"] = now


# ----------------------------------------------------------------------
# Main import routine (UPSERT)
# ----------------------------------------------------------------------
def import_kaggle_with_ml(csv_path: Path) -> None:
    coll = get_patient_collection()

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    print(f"📄 Loading Kaggle stroke CSV from: {csv_path}")

    upserted = 0
    skipped = 0

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, start=1):
            try:
                doc = _build_doc_from_row(row)

                # must have a valid original_id for upsert
                if doc.get("original_id") is None:
                    skipped += 1
                    print(f"  · Skipping row {idx}: missing id")
                    continue

                # Skip obviously bad rows (no age + no glucose + no BMI)
                demo = doc.get("demographics", {}) or {}
                med = doc.get("medical_history", {}) or {}
                if (
                    demo.get("age") is None
                    and med.get("avg_glucose_level") is None
                    and med.get("bmi") is None
                ):
                    skipped += 1
                    continue

                # Run ML scoring before write
                _apply_ml_to_doc(doc)

                # UPSERT by original_id (prevents duplicates)
                res = coll.update_one(
                    {"original_id": doc["original_id"]},
                    {"$set": doc},
                    upsert=True,
                )

                if res.upserted_id is not None or res.modified_count > 0:
                    upserted += 1

                if upserted % 500 == 0:
                    ra = doc.get("risk_assessment", {}) or {}
                    print(
                        f"  ✔ Upserted {upserted} patients so far "
                        f"(last: score={ra.get('score', 0):.2f}, level={ra.get('level')})"
                    )

            except Exception as exc:
                skipped += 1
                print(f"  ! Error on row {idx}: {exc!r} — row skipped")

    print("\nImport complete.")
    print(f"   Upserted: {upserted} patients")
    print(f"   Skipped : {skipped} rows")


def main() -> None:
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1]).expanduser().resolve()
    else:
        csv_path = Path("data") / "healthcare-dataset-stroke-data.csv"

    app = create_app()
    with app.app_context():
        import_kaggle_with_ml(csv_path)


if __name__ == "__main__":
    main()
