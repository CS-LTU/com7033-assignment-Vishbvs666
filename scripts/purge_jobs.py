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

# purge_jobs.py
"""
Maintenance script for cleaning old logs and temporary prediction records.
Run manually or schedule with cron.

python app/scripts/purge_jobs.py
"""

from datetime import datetime, timedelta
import click

from app import create_app
from app.extensions import db
from app.models import StrokePrediction, AuditLog
from app.db.mongo import get_mongo_db


# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------
DAYS_TO_KEEP = 30  # delete all records older than this


# ---------------------------------------------------------------------
# CLEAN SQL TABLES
# ---------------------------------------------------------------------
def purge_sql_logs(app):
    with app.app_context():
        cutoff = datetime.utcnow() - timedelta(days=DAYS_TO_KEEP)

        # --- Delete Old Predictions ---
        deleted_pred = (
            StrokePrediction.query.filter(StrokePrediction.created_at < cutoff)
            .delete(synchronize_session=False)
        )

        # --- Delete Old Audit Logs ---
        deleted_audit = (
            AuditLog.query.filter(AuditLog.timestamp < cutoff)
            .delete(synchronize_session=False)
        )

        db.session.commit()

        return deleted_pred, deleted_audit


# ---------------------------------------------------------------------
# CLEAN MONGO COLLECTIONS (optional)
# ---------------------------------------------------------------------
def purge_mongo_stale():
    """
    Your app does not generate temporary Mongo documents,
    but this function is included for future safety.
    """
    db_mongo = get_mongo_db()
    patients = db_mongo.get_collection("patients")

    # If someday you add temporary flags, purge them safely.
    # Right now we simply return 0 as nothing is removed.
    return 0


# ---------------------------------------------------------------------
# CLI ENTRYPOINT
# ---------------------------------------------------------------------
@click.command()
def main():
    app = create_app()

    print(f"\n⚙️ Purging logs older than {DAYS_TO_KEEP} days…")

    pred_count, audit_count = purge_sql_logs(app)
    mongo_count = purge_mongo_stale()

    print(f"✔ Deleted {pred_count} old predictions")
    print(f"✔ Deleted {audit_count} old audit log entries")

    if mongo_count > 0:
        print(f"✔ Deleted {mongo_count} stale Mongo records")

    print("\n✨ Purge completed successfully.\n")


if __name__ == "__main__":
    main()
