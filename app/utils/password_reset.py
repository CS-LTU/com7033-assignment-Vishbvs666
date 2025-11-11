from __future__ import annotations
from typing import Optional
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app

def _serializer() -> URLSafeTimedSerializer:
    secret = current_app.config["SECRET_KEY"]
    return URLSafeTimedSerializer(secret_key=secret, salt=current_app.config.get("SECURITY_PASSWORD_SALT", "pw-reset"))

def make_reset_token(email: str) -> str:
    return _serializer().dumps({"email": email})

def load_reset_email(token: str, max_age: int = 3600) -> Optional[str]:
    try:
        data = _serializer().loads(token, max_age=max_age)
        return (data or {}).get("email")
    except (BadSignature, SignatureExpired):
        return None
