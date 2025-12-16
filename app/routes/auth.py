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

# app/routes/auth.py
from __future__ import annotations

import time
from dataclasses import dataclass

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    g,
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.routing import BuildError

from app.extensions import db
from app.forms import LoginCaptchaForm, RegistrationForm, ResetPasswordForm
from app.models.user import User
from app.utils.audit import audit


bp = Blueprint("auth", __name__, url_prefix="/auth")


# -------------------------------------------------------------------
# Simple in-memory rate limiting / lockout tracker (demo-friendly)
# NOTE: In production, store this in Redis/DB so it survives restarts.
# -------------------------------------------------------------------
@dataclass
class AttemptState:
    count: int = 0
    first_ts: float = 0.0
    locked_until: float = 0.0


_LOGIN_ATTEMPTS: dict[str, AttemptState] = {}


def _dashboard_url() -> str:
    try:
        return url_for("main.index")
    except BuildError:
        return url_for("auth.login")


def _client_ip() -> str:
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _now() -> float:
    return time.time()


def _cfg_int(key: str, default: int) -> int:
    try:
        return int(current_app.config.get(key, default))
    except Exception:
        return default


def _get_state(bucket_key: str) -> AttemptState:
    return _LOGIN_ATTEMPTS.setdefault(bucket_key, AttemptState())


def _reset_state(bucket_key: str) -> None:
    _LOGIN_ATTEMPTS.pop(bucket_key, None)


def _register_failure(state: AttemptState, window_seconds: int) -> None:
    now = _now()
    if state.first_ts == 0.0 or (now - state.first_ts) > window_seconds:
        state.first_ts = now
        state.count = 1
        return
    state.count += 1


def _should_lock(state: AttemptState, window_seconds: int, max_attempts: int) -> bool:
    if state.count < max_attempts:
        return False
    if state.first_ts == 0.0:
        return False
    return (_now() - state.first_ts) <= window_seconds


def _is_locked(state: AttemptState) -> bool:
    return state.locked_until > _now()


def _lock(state: AttemptState, lockout_seconds: int) -> None:
    state.locked_until = _now() + lockout_seconds


def _captcha_required(state: AttemptState, captcha_after: int) -> bool:
    if captcha_after <= 0:
        return False
    return state.count >= captcha_after


# -----------------------------
# LOGIN (rate-limit + captcha escalation)
# -----------------------------
@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_dashboard_url())

    # Config knobs
    window_seconds = _cfg_int("AUTH_RATE_WINDOW_SECONDS", 15 * 60)  # 15 minutes
    captcha_after = _cfg_int("AUTH_CAPTCHA_AFTER", 3)               # require after 3 fails
    max_attempts = _cfg_int("AUTH_MAX_ATTEMPTS", 6)                 # lock after 6 fails
    lockout_seconds = _cfg_int("AUTH_LOCKOUT_SECONDS", 10 * 60)     # 10 mins

    ip = _client_ip()

    # For GET: no email yet → use "unknown" bucket
    raw_email = (request.form.get("email") or "").strip().lower()
    email_bucket = raw_email if raw_email else "unknown"
    bucket_key = f"login:{ip}:{email_bucket}"
    state = _get_state(bucket_key)

    # Set escalation flag for forms.validate()
    g.captcha_required = _captcha_required(state, captcha_after)

    # ALWAYS use captcha form so the widget is visible on the page
    form = LoginCaptchaForm()

    # If locked → block immediately
    if _is_locked(state):
        audit(
            user_id=None,
            action="user_login_blocked",
            resource_type="auth",
            resource_id=None,
            details=f"Login blocked due to lockout. ip={ip} email={email_bucket}",
        )
        flash("Too many failed attempts. Please try again later.", "danger")
        return render_template("auth/login.html", form=form, captcha_required=True)

    if form.validate_on_submit():
        email = (form.email.data or "").strip().lower()
        user = User.query.filter_by(email=email).first()

        # Now that we have validated email, use accurate bucket
        bucket_key = f"login:{ip}:{email}"
        state = _get_state(bucket_key)

        # Update escalation flag for this request
        g.captcha_required = _captcha_required(state, captcha_after)

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)

            _reset_state(bucket_key)

            audit(
                user_id=user.id,
                action="user_login",
                resource_type="auth",
                resource_id=user.id,
                details=f"User logged in via email/password. ip={ip}",
            )

            flash("Welcome back!", "success")
            return redirect(_dashboard_url())

        # Failed login
        _register_failure(state, window_seconds)

        # If exceeded attempts → lock
        if _should_lock(state, window_seconds, max_attempts):
            _lock(state, lockout_seconds)

            audit(
                user_id=user.id if user else None,
                action="user_login_lockout",
                resource_type="auth",
                resource_id=user.id if user else None,
                details=f"User locked out after failures. ip={ip} email={email} failures={state.count}",
            )

            flash("Too many failed attempts. Please try again later.", "danger")
            g.captcha_required = True
            return render_template("auth/login.html", form=form, captcha_required=True)

        audit(
            user_id=user.id if user else None,
            action="user_login_failed",
            resource_type="auth",
            resource_id=user.id if user else None,
            details=f"Failed login attempt. ip={ip} email={email} failures={state.count}",
        )

        flash("Invalid email or password.", "danger")
        g.captcha_required = _captcha_required(state, captcha_after)

    return render_template(
        "auth/login.html",
        form=form,
        captcha_required=bool(getattr(g, "captcha_required", False)),
    )


# -----------------------------
# LOGOUT
# -----------------------------
@bp.route("/logout")
@login_required
def logout():
    audit(
        user_id=getattr(current_user, "id", None),
        action="user_logout",
        resource_type="auth",
        resource_id=getattr(current_user, "id", None),
        details="User logged out",
    )

    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))


# -----------------------------
# REGISTER
# -----------------------------
@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(_dashboard_url())

    form = RegistrationForm()

    if form.validate_on_submit():
        email = (form.email.data or "").strip().lower()

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("An account with this email already exists.", "warning")
            return render_template("auth/register.html", form=form)

        user = User()
        user.email = email
        user.username = email.split("@")[0] if "@" in email else email
        user.role = form.role.data
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        audit(
            user_id=user.id,
            action="user_registered",
            resource_type="auth",
            resource_id=user.id,
            details=f"New user registered. role={user.role}",
        )

        flash("Account created successfully — please sign in.", "success")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        flash("Please check the form for errors and try again.", "danger")

    return render_template("auth/register.html", form=form)


# -----------------------------
# FORGOT PASSWORD (optional)
# -----------------------------
@bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    form = ResetPasswordForm()
    return render_template("auth/forgot.html", form=form)


# -----------------------------
# RESET PASSWORD (optional)
# -----------------------------
@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    form = ResetPasswordForm()
    if form.validate_on_submit():
        flash("Password reset successful.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset.html", form=form)
