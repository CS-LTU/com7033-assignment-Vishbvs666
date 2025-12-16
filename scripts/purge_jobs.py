"""
Maintenance script for cleaning old logs and temporary prediction records.
Run manually or schedule with cron.

python scripts/purge_jobs.py
"""

from __future__ import annotations

from datetime import datetime, timedelta

import click

from app import create_app
from app.extensions import db
from app.models import StrokePrediction, AuditLog
from app.db.mongo import get_patient_collection

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------
DAYS_TO_KEEP = 30  # delete all records older than this


# ---------------------------------------------------------------------
# CLEAN SQL TABLES
# ---------------------------------------------------------------------
def purge_sql_logs(cutoff: datetime) -> tuple[int, int]:
    # Delete old predictions
    deleted_pred = (
        StrokePrediction.query.filter(StrokePrediction.created_at < cutoff)
        .delete(synchronize_session=False)
    )

    # Delete old audit logs
    deleted_audit = (
        AuditLog.query.filter(AuditLog.timestamp < cutoff)
        .delete(synchronize_session=False)
    )

    db.session.commit()
    return int(deleted_pred), int(deleted_audit)


# ---------------------------------------------------------------------
# CLEAN MONGO COLLECTIONS (optional)
# ---------------------------------------------------------------------
def purge_mongo_stale(cutoff: datetime) -> int:
    """
    You currently don't store temporary Mongo documents.
    This is kept for future safety.
    """
    coll = get_patient_collection()

    # Example: if you later add soft-deleted docs and want to purge them after N days,
    # you can implement it here.
    # For now, we remove nothing:
    return 0


# ---------------------------------------------------------------------
# CLI ENTRYPOINT
# ---------------------------------------------------------------------
@click.command()
@click.option("--days", default=DAYS_TO_KEEP, show_default=True, type=int, help="Days of data to keep")
def main(days: int) -> None:
    app = create_app()

    with app.app_context():
        cutoff = datetime.utcnow() - timedelta(days=days)

        print(f"\n Purging logs older than {days} days (cutoff: {cutoff.isoformat()} UTC)…")

        pred_count, audit_count = purge_sql_logs(cutoff)
        mongo_count = purge_mongo_stale(cutoff)

        print(f"✔ Deleted {pred_count} old predictions")
        print(f"✔ Deleted {audit_count} old audit log entries")

        if mongo_count > 0:
            print(f"✔ Deleted {mongo_count} stale Mongo records")

        print("\n Purge completed successfully.\n")


if __name__ == "__main__":
    main()
