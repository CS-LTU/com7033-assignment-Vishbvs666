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

# app/config.py
from __future__ import annotations

import os

# Base directory of the project (folder that contains app/, run.py, etc.)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    # Secret key for sessions / CSRF
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me-please")

    # Main SQLite DB – creates strokecare.db in the project root
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "strokecare.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session timeout in minutes
    SECURITY_SESSION_MINUTES = int(os.environ.get("SECURITY_SESSION_MINUTES", 60))

    # Rate limiting (you can tweak later)
    RATELIMIT_DEFAULT = "60 per minute"

    # MongoDB config for patient records
    # You can override these with real values via environment variables if you want.
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/strokecare")
    MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "strokecare")
    MONGO_PATIENTS_COLLECTION = os.environ.get(
        "MONGO_PATIENTS_COLLECTION",
        "patients",
    )
