from __future__ import annotations
from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="patient")  # patient / doctor / hcp / admin

    # --------------------------
    # Password helpers
    # --------------------------
    def set_password(self, raw_password: str | None) -> None:
        self.password = generate_password_hash(raw_password or "")

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password, raw_password)

    def __repr__(self):
        return f"<User {self.email}>"
