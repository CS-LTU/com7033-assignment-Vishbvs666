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

# tests/test_auth.py
from __future__ import annotations

from flask_login import current_user
import pytest

from app.forms import LoginForm


def test_login_page_renders(client):
    """GET /auth/login should return 200 and contain the Sign in UI."""
    resp = client.get("/auth/login")
    assert resp.status_code == 200
    assert b"Sign in with email" in resp.data


def test_login_success(client, monkeypatch, create_user):
    """
    Valid credentials should authenticate the user and redirect to dashboard.
    We monkeypatch validate_on_submit() so we don’t have to send a real
    reCAPTCHA token in tests.
    """
    user = create_user(email="login_success@stroke.test", password="Password123!")

    # Always treat form as valid (skip real reCAPTCHA etc.)
    def always_valid(self: LoginForm) -> bool:  # type: ignore[override]
        return True

    monkeypatch.setattr(LoginForm, "validate_on_submit", always_valid, raising=True)

    with client:
        resp = client.post(
            "/auth/login",
            data={"email": user.email, "password": "Password123!"},
            follow_redirects=True,
        )

        # Successful login should end in a 200 after redirects
        assert resp.status_code == 200
        assert current_user.is_authenticated
        assert current_user.email == user.email


def test_login_invalid_credentials(client, monkeypatch, create_user):
    """
    Wrong password should NOT authenticate the user and should re-render
    the login page. We don't depend on a specific flash message text,
    only that we're still on the sign-in screen and not logged in.
    """
    user = create_user(email="wrongpass@stroke.test", password="Correct123!")

    def always_valid(self: LoginForm) -> bool:  # type: ignore[override]
        return True

    monkeypatch.setattr(LoginForm, "validate_on_submit", always_valid, raising=True)

    with client:
        resp = client.post(
            "/auth/login",
            data={"email": user.email, "password": "TotallyWrong123"},
            follow_redirects=True,
        )

        # Page re-rendered
        assert resp.status_code == 200
        # We are still seeing the login UI
        assert b"Sign in with email" in resp.data
        # And we definitely don't see a logged-in navbar
        assert b"Logout" not in resp.data


def test_login_redirects_if_already_authenticated(client, monkeypatch, create_user):
    """
    If an authenticated user hits /auth/login, they should be redirected
    to the main index/dashboard instead of seeing the login form again.
    """
    user = create_user(email="already@stroke.test", password="Password123!")

    def always_valid(self: LoginForm) -> bool:  # type: ignore[override]
        return True

    monkeypatch.setattr(LoginForm, "validate_on_submit", always_valid, raising=True)

    # First, log in
    with client:
        login_resp = client.post(
            "/auth/login",
            data={"email": user.email, "password": "Password123!"},
            follow_redirects=True,
        )
        assert login_resp.status_code == 200
        assert current_user.is_authenticated

        # Now hit /auth/login again – should redirect (302/303)
        resp = client.get("/auth/login")
        assert resp.status_code in (302, 303)
