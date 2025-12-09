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

# app/utils/audit.py
from __future__ import annotations

from typing import Any

from flask import request
from flask_login import current_user

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
    Lightweight audit helper.

    Writes a single row into audit_logs with:
      - user_id
      - action (plus optional metadata)
      - ip_address

    The optional resource_type / resource_id / details are folded into
    the action text, so we don't need extra DB columns.
    """

    # Fallback to current_user if user_id not explicitly passed
    if user_id is None:
        try:
            user_id = getattr(current_user, "id", None)
        except Exception:
            user_id = None

    # Figure out IP if not explicitly passed
    if ip is None:
        try:
            ip = request.remote_addr
        except RuntimeError:
            # Outside request context (e.g. CLI) – leave as None
            ip = None

    # Build descriptive action string with metadata
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

    # Match your model/DB column name
    if hasattr(entry, "ip_address"):
        entry.ip_address = ip

    db.session.add(entry)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
