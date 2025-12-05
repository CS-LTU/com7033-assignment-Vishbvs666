from datetime import datetime
from app.extensions import db

class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True,
    )
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4/IPv6 text

    user = db.relationship("User", backref="sessions", lazy=True)

    def __repr__(self) -> str:  # just for debugging
        return f"<Session {self.id} user={self.user_id}>"
