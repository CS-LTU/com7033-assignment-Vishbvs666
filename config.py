# config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Secret key for sessions / CSRF
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")

    # Main SQLite DB in instance/strokecare.db
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(basedir, "instance", "strokecare.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session timeout (minutes)
    SECURITY_SESSION_MINUTES = int(os.environ.get("SECURITY_SESSION_MINUTES", 60))

    # Optional: simple default rate limit
    RATELIMIT_DEFAULT = "60 per minute"
