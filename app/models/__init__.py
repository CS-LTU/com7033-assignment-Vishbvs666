from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

db = SQLAlchemy()

# ---------- MODELS ----------

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, index=True, nullable=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False)  # admin, doctor, healthcare, patient
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    sessions = db.relationship("Session", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    logs = db.relationship("AuditLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    # helpers
    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)


class Session(db.Model):
    __tablename__ = "sessions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    session_token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expired_at = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4/IPv6

    @staticmethod
    def new_token() -> str:
        return secrets.token_urlsafe(32)

    @classmethod
    def create_for(cls, user_id: int, ip: Optional[str], ttl_hours: int = 8) -> "Session":
        token = cls.new_token()
        s = cls(
            user_id=user_id,
            session_token=token,
            created_at=datetime.utcnow(),
            expired_at=datetime.utcnow() + timedelta(hours=ttl_hours),
            ip_address=(ip or "")[:45],
        )
        db.session.add(s)
        return s


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(50), nullable=False)         # e.g. login, logout, create_patient
    resource_type = db.Column(db.String(50), nullable=True)   # e.g. user, patient
    resource_id = db.Column(db.String(64), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    details = db.Column(db.Text, nullable=True)

# ---------- SEED ----------
def seed_demo_data():
    if User.query.count() == 0:
        demo_users = [
            User(name="Niki Sangvikar", email="niki@strokecare.com", role="admin"),
            User(name="Dr. Antony Starr", email="antony@strokecare.com", role="doctor"),
            User(name="Nurse Moira Rose", email="moira@strokecare.com", role="healthcare"),
            User(name="Ben Tennison", email="ben@strokecare.com", role="patient")
        ]
        for u in demo_users:
            u.set_password("pass12345")
            db.session.add(u)
        db.session.commit()
