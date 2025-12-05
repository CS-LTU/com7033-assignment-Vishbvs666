from __future__ import annotations
from app.extensions import db
from datetime import datetime


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<PasswordResetToken {self.id} user={self.user_id}>"
