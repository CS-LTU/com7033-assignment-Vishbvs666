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

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # -------------------------
    # Flask core security
    # -------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")

    # -------------------------
    # SQLAlchemy (SQLite)
    # -------------------------
    DB_PATH = os.path.join(BASE_DIR, "instance", "strokecare.db")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -------------------------
    # MongoDB
    # -------------------------
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017")
    MONGO_DBNAME = os.environ.get("MONGO_DBNAME", "strokecare")

    # -------------------------
    # Session Security settings
    # -------------------------
    SECURITY_SESSION_MINUTES = int(os.environ.get("SECURITY_SESSION_MINUTES", 60))

    # -------------------------
    # Global Rate Limiting 
    # -------------------------
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "60 per minute")

    # -------------------------
    # Auth: login rate-limit + CAPTCHA escalation
    # -------------------------
    AUTH_RATE_WINDOW_SECONDS = int(os.environ.get("AUTH_RATE_WINDOW_SECONDS", 900))  # 15 min
    AUTH_CAPTCHA_AFTER = int(os.environ.get("AUTH_CAPTCHA_AFTER", 3))               # captcha after 3 fails
    AUTH_MAX_ATTEMPTS = int(os.environ.get("AUTH_MAX_ATTEMPTS", 6))                 # lock after 6 fails
    AUTH_LOCKOUT_SECONDS = int(os.environ.get("AUTH_LOCKOUT_SECONDS", 600))         # 10 min lockout

    # -------------------------
    # reCAPTCHA (Flask-WTF)
    # -------------------------
    # Google OFFICIAL TEST KEYS (work on localhost / dev)
    RECAPTCHA_PUBLIC_KEY = os.environ.get(
        "RECAPTCHA_PUBLIC_KEY",
        "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
    )
    RECAPTCHA_PRIVATE_KEY = os.environ.get(
        "RECAPTCHA_PRIVATE_KEY",
        "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe",
    )

    # UI options
    RECAPTCHA_OPTIONS = {"theme": "light", "size": "normal"}

    # If TRUE → captcha must validate always
    RECAPTCHA_STRICT = os.environ.get("RECAPTCHA_STRICT", "0") == "1"
