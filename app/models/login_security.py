from __future__ import annotations

from datetime import datetime, timedelta

from app.extensions import db


class LoginThrottle(db.Model):
    __tablename__ = "login_throttle"

    id = db.Column(db.Integer, primary_key=True)

    # track by IP + email (email can be empty for unknown)
    ip = db.Column(db.String(64), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False, index=True)

    failed_count = db.Column(db.Integer, nullable=False, default=0)
    first_failed_at = db.Column(db.DateTime, nullable=True)
    last_failed_at = db.Column(db.DateTime, nullable=True)

    locked_until = db.Column(db.DateTime, nullable=True)

    def is_locked(self) -> bool:
        return self.locked_until is not None and self.locked_until > datetime.utcnow()

    def reset(self) -> None:
        self.failed_count = 0
        self.first_failed_at = None
        self.last_failed_at = None
        self.locked_until = None

    def register_failure(self, window_minutes: int, lock_after: int, lock_minutes: int) -> None:
        now = datetime.utcnow()
        window = timedelta(minutes=window_minutes)

        if self.first_failed_at is None or (now - self.first_failed_at) > window:
            # start a new window
            self.first_failed_at = now
            self.failed_count = 0

        self.failed_count += 1
        self.last_failed_at = now

        if self.failed_count >= lock_after:
            self.locked_until = now + timedelta(minutes=lock_minutes)
