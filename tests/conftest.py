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

# tests/conftest.py
from __future__ import annotations

from typing import Generator, Callable

import pytest

from app import create_app
from app.extensions import db
from config import Config


# -----------------------------
# Test configuration
# -----------------------------
class TestConfig(Config):
    """Config used only for pytest."""

    TESTING = True
    WTF_CSRF_ENABLED = False          # disable CSRF checks for tests
    RATELIMIT_DEFAULT = "1000 per minute"

    # use an in-memory SQLite DB for isolation
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# -----------------------------
# App + client fixtures
# -----------------------------
@pytest.fixture
def app() -> Generator:
    """Create a fresh app + empty DB for each test session."""
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        try:
            yield app
        finally:
            db.session.remove()
            db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client bound to our test app."""
    return app.test_client()


# -----------------------------
# Helper fixtures to create users
# -----------------------------
@pytest.fixture
def create_user(app) -> Callable:
    """
    Factory fixture that creates a normal (non-admin) user.

    Usage in tests:
        user = create_user(email="someone@test", role="doctor")
    """
    from app.models import User  # import here so app is already initialised

    def _create_user(
        email: str = "user@stroke.test",
        password: str = "Password123!",
        role: str = "patient",
        **extra,
    ) -> User:
        # NOTE: do NOT pass is_active here – property has no setter
        u = User(
            email=email.lower(),
            username=email.split("@")[0],
            role=role,
            **extra,
        )
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        return u

    return _create_user


@pytest.fixture
def create_admin_user(create_user) -> Callable:
    """
    Factory fixture that creates an admin user.

    Usage:
        admin = create_admin_user(email="admin@stroke.test")
    """

    def _create_admin_user(
        email: str = "admin@stroke.test",
        password: str = "AdminPass123!",
        **extra,
    ):
        return create_user(email=email, password=password, role="admin", **extra)

    return _create_admin_user
