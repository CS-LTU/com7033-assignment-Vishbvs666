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

# tests/test_security.py
from __future__ import annotations

from flask_login import current_user

from app.forms import LoginForm


def test_csrf_disabled_in_test_config(app):
    """
    In TestConfig we intentionally disable CSRF so that we can post forms
    in pytest without having to generate tokens. (In production it is ON.)
    """
    assert app.config.get("WTF_CSRF_ENABLED") is False


def test_login_required_redirects(client):
    """
    Hitting a protected route like /patient/dashboard without being logged in
    should redirect to the login page (302/303).
    """
    resp = client.get("/patient/dashboard")
    assert resp.status_code in (302, 303)
    assert "/auth/login" in resp.headers.get("Location", "")


def test_login_success_sets_secure_session(app, client, monkeypatch, create_user):
    """
    After a successful login we expect the user to be authenticated and
    the app config to enforce HttpOnly on the session cookie. We don't
    rely on Set-Cookie headers from the final redirect response.
    """
    user = create_user(email="secure@stroke.test", password="Password123!")

    def always_valid(self: LoginForm) -> bool:  # type: ignore[override]
        return True

    monkeypatch.setattr(LoginForm, "validate_on_submit", always_valid, raising=True)

    with client:
        resp = client.post(
            "/auth/login",
            data={"email": user.email, "password": "Password123!"},
            follow_redirects=True,
        )

        assert resp.status_code == 200
        assert current_user.is_authenticated

    # Flask sets this True by default; your security config keeps it that way.
    assert app.config.get("SESSION_COOKIE_HTTPONLY", True) is True


def test_login_invalid_credentials(client, monkeypatch, create_user):
    """
    Invalid password should NOT log the user in and should show the login
    form again. We keep this high-level and do not depend on a specific
    flash message text.
    """
    user = create_user(email="badlogin@stroke.test", password="Correct123!")

    def always_valid(self: LoginForm) -> bool:  # type: ignore[override]
        return True

    monkeypatch.setattr(LoginForm, "validate_on_submit", always_valid, raising=True)

    with client:
        resp = client.post(
            "/auth/login",
            data={"email": user.email, "password": "WrongPass!"},
            follow_redirects=True,
        )

        assert resp.status_code == 200
        assert b"Sign in with email" in resp.data
        assert b"Logout" not in resp.data


def test_rbac_non_admin_forbidden(client, monkeypatch, create_user):
    """
    A non-admin user should NOT be able to access /admin/dashboard.
    Expect a redirect back to login or a 403.
    """
    user = create_user(
        email="normal@stroke.test", password="Password123!", role="patient"
    )

    def always_valid(self: LoginForm) -> bool:  # type: ignore[override]
        return True

    monkeypatch.setattr(LoginForm, "validate_on_submit", always_valid, raising=True)

    # Log in as normal (non-admin) user
    with client:
        login_resp = client.post(
            "/auth/login",
            data={"email": user.email, "password": "Password123!"},
            follow_redirects=True,
        )
        assert login_resp.status_code == 200
        assert current_user.is_authenticated
        assert current_user.role == "patient"

        # Now try to hit admin dashboard
        resp = client.get("/admin/dashboard")
        assert resp.status_code in (302, 403)


def test_rbac_admin_access(client, monkeypatch, create_admin_user):
    """
    An admin user should be able to reach /admin/dashboard with HTTP 200.
    """
    admin = create_admin_user()

    def always_valid(self: LoginForm) -> bool:  # type: ignore[override]
        return True

    monkeypatch.setattr(LoginForm, "validate_on_submit", always_valid, raising=True)

    with client:
        # Log in as admin
        login_resp = client.post(
            "/auth/login",
            data={"email": admin.email, "password": "AdminPass123!"},
            follow_redirects=True,
        )
        assert login_resp.status_code == 200
        assert current_user.is_authenticated
        assert current_user.role == "admin"

        # Access admin dashboard
        resp = client.get("/admin/dashboard")
        assert resp.status_code == 200


def test_logout_clears_session(client, monkeypatch, create_user):
    """
    After logout, the user should no longer be authenticated, and a
    protected page should redirect back to login.
    """
    user = create_user(email="logout@stroke.test", password="Password123!")

    def always_valid(self: LoginForm) -> bool:  # type: ignore[override]
        return True

    monkeypatch.setattr(LoginForm, "validate_on_submit", always_valid, raising=True)

    with client:
        # Log in
        client.post(
            "/auth/login",
            data={"email": user.email, "password": "Password123!"},
            follow_redirects=True,
        )
        assert current_user.is_authenticated

        # Logout
        resp = client.get("/auth/logout", follow_redirects=True)
        assert resp.status_code == 200
        assert not current_user.is_authenticated

        # Protected page should now redirect
        resp2 = client.get("/patient/dashboard")
        assert resp2.status_code in (302, 303)


def test_basic_rate_limit_smoke(app):
    """
    Just verify that a RATELIMIT_DEFAULT config value exists – detailed
    rate-limit testing would require spinning up the real limiter.
    """
    assert "RATELIMIT_DEFAULT" in app.config
    assert isinstance(app.config["RATELIMIT_DEFAULT"], str)
    assert app.config["RATELIMIT_DEFAULT"]
