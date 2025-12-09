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

# app/utils/password_reset.py
from __future__ import annotations

from datetime import datetime, timedelta
from secrets import token_urlsafe

from app.extensions import db
from app.models import PasswordResetToken  # type: ignore[import]
from app.models import User  

def create_reset_token(user, minutes: int = 30) -> PasswordResetToken:
    token = token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=minutes)

    prt = PasswordResetToken()
    prt.user_id = user.id
    prt.token = token
    prt.expires_at = expires_at
    prt.used = False

    db.session.add(prt)
    db.session.commit()
    return prt


def validate_reset_token(token: str):

    prt = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not prt:
        return None
    if prt.expires_at < datetime.utcnow():
        return None
    return User.query.get(prt.user_id)

