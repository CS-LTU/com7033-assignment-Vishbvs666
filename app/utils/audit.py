from __future__ import annotations
from typing import Optional
from app.models import db, AuditLog

def log_event(user_id: Optional[int], action: str, resource_type: Optional[str] = None,
              resource_id: Optional[str] = None, details: Optional[str] = None) -> None:
    db.session.add(AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details
    ))
    # caller commits (so this can be batched with other writes)
