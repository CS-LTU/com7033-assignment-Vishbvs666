# app/models/audit_log.py
from __future__ import annotations

from datetime import datetime

from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True, index=True)
    action = db.Column(db.String(255), nullable=False)

    # IMPORTANT: name must match your existing SQLite column.
    # In your DB the column is called "ip_address", so we use that.
    ip_address = db.Column(db.String(64))

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    def __repr__(self) -> str:  # type: ignore[override]
        return f"<AuditLog {self.id} action={self.action}>"
