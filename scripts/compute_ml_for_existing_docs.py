"""
Recompute ML stroke-risk predictions for **all active patients** in MongoDB.

This script:
 - Uses app.ml.predict_service.run_ml_on_patient_doc()
   (the SAME helper the doctor view uses)
 - Writes risk_assessment = {
       _score, _level, _flag, _calculated_at
   }

It is also imported by tests/test_risk_label.py for the risk_label()
helper below.
"""

from __future__ import annotations

from datetime import datetime

from app import create_app
from app.db.mongo import get_patient_collection
from app.ml.predict_service import run_ml_on_patient_doc  # reuse doctor logic


# ----------------------------------------------------------------------
# Helper used both by this script and pytest (test_risk_label.py)
# ----------------------------------------------------------------------
def risk_label(score: float | None) -> str:
    """
    Map a probability score (0–1) into a human-readable risk label.

    Thresholds (matching the unit tests):
      Low    : < 0.30
      Medium : 0.30 – 0.69
      High   : ≥ 0.70
    """
    if score is None:
        return "Unknown"

    try:
        s = float(score)
    except (TypeError, ValueError):
        return "Unknown"

    if s < 0.30:
        return "Low"
    elif s < 0.70:
        return "Medium"
    else:
        return "High"


# ----------------------------------------------------------------------
# Main recompute routine
# ----------------------------------------------------------------------
def run_recompute() -> None:
    coll = get_patient_collection()

    print(" Fetching active patients from MongoDB…")
    docs = list(coll.find({"system_metadata.is_active": True}))
    print(f"Found {len(docs)} patients. Computing ML predictions…")

    for d in docs:
        oid = d["_id"]

        try:
            # probability (0–1), stroke_flag (0/1), risk_level ("Low"/"Medium"/"High")
            proba, stroke_flag, risk_level = run_ml_on_patient_doc(d)
        except Exception as e:
            print(f" Skipped patient {oid}: model error → {e}")
            continue

        now = datetime.utcnow()

        coll.update_one(
            {"_id": oid},
            {
                "$set": {
                    "risk_assessment._score": proba,
                    "risk_assessment._level": risk_level,
                    "risk_assessment._flag": stroke_flag,
                    "risk_assessment._calculated_at": now,
                    "system_metadata.last_modified_at": now,
                }
            },
        )

        print(
            f"✔ Updated {oid}: "
            f"score={proba:.2f}, level={risk_level}, flag={stroke_flag}"
        )

    print(" DONE! All patient risk scores recalculated.")


def main() -> None:
    app = create_app()
    with app.app_context():
        run_recompute()


if __name__ == "__main__":
    main()
