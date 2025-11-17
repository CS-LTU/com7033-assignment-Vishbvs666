# app/utils/audit.py
from __future__ import annotations

from typing import Any

from flask import request
from app.extensions import db
from app.models import AuditLog


def audit(
    user_id: int | None,
    action: str,
    resource_type: str | None = None,
    resource_id: Any | None = None,
    details: str | None = None,
    ip: str | None = None,
) -> None:
    """
    Light-weight audit helper.

    We only write into the columns that exist on AuditLog:
    - user_id
    - action
    - ip_address

    The optional resource_type / resource_id / details are folded into
    the action text so we don't need extra DB columns right now.
    """

    # Figure out IP if not explicitly passed
    if ip is None:
        try:
            ip = request.remote_addr
        except RuntimeError:
            # Outside request context (e.g. CLI) – leave as None
            ip = None

    # Build a descriptive action string with metadata
    meta_parts: list[str] = []
    if resource_type:
        meta_parts.append(f"resource_type={resource_type}")
    if resource_id is not None:
        meta_parts.append(f"resource_id={resource_id}")
    if details:
        meta_parts.append(f"details={details}")

    if meta_parts:
        full_action = f"{action} | " + "; ".join(meta_parts)
    else:
        full_action = action

    entry = AuditLog()
    entry.user_id = user_id
    entry.action = full_action
    entry.ip_address = ip

    db.session.add(entry)
    db.session.commit()
