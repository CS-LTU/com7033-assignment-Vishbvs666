# config.py
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Flask security
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")

    # -------------------------
    # SQLAlchemy (SQLite)
    # -------------------------
    # This points to instance/strokecare.db because your app
    # was created with instance_relative_config=True
    DB_PATH = os.path.join(BASE_DIR, "instance", "strokecare.db")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -------------------------
    # MongoDB (local)
    # -------------------------
    # Uses your local Mongo service we just started
    # mongosh connects to mongodb://127.0.0.1:27017 by default
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017")
    MONGO_DBNAME = os.environ.get("MONGO_DBNAME", "strokecare")

    # -------------------------
    # Security / rate limiting
    # -------------------------
    # Session lifetime in minutes
    SECURITY_SESSION_MINUTES = int(
        os.environ.get("SECURITY_SESSION_MINUTES", 60)
    )

    # Global rate-limit string (flask-limiter compatible)
    # e.g. "60 per minute" = max 60 requests / minute / IP
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "60 per minute")
