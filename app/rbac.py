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

# app/rbac.py
from __future__ import annotations

from functools import wraps
from typing import Callable, Dict, Optional, Set, TypeVar

from flask import abort
from flask_login import current_user

T = TypeVar("T", bound=Callable[..., object])

# Permissions matrix
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "admin": {
        "patient.view_all",
        "patient.view_own",
        "patient.create",
        "patient.edit",
        "patient.delete",
        "ml.run",
        "ml.view",
        "user.manage",
        "audit.view",
        "system.settings",
    },
    "doctor": {
        "patient.view_all",
        "patient.view_own",
        "patient.create",
        "patient.edit",
        "ml.run",
        "ml.view",
    },
    "healthcare": {
        "patient.view_all",
        "patient.view_own",
        "patient.create",
        "patient.edit",
        "ml.run",
        "ml.view",
    },
    "patient": {
        "patient.view_own",
        "ml.view",
    },
}


def _user_role() -> Optional[str]:
    if not current_user.is_authenticated:
        return None
    return getattr(current_user, "role", None)


def has_permission(user, perm: str) -> bool:
    role = getattr(user, "role", None)
    return perm in ROLE_PERMISSIONS.get(role or "", set())


def require_permissions(*perms: str):
    def decorator(view: T) -> T:
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            role = _user_role()
            allowed = ROLE_PERMISSIONS.get(role or "", set())
            if not all(p in allowed for p in perms):
                abort(403)
            return view(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def role_is(*roles: str):
    def decorator(view: T) -> T:
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if _user_role() not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
