import os
from dotenv import load_dotenv

def load_config(app):
    load_dotenv()
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev"),
        JSON_SORT_KEYS=False,
        SQLALCHEMY_DATABASE_URI=os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///instance/strokecare.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MONGO_URI=os.getenv("MONGO_URI", ""),
        PERMANENT_SESSION_LIFETIME=60*60*72,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,               # True in prod (HTTPS)
        RATELIMIT_STORAGE_URI=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    )
