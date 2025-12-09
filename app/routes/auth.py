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

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.routing import BuildError

from app.extensions import db
from app.forms import LoginForm, RegistrationForm, ResetPasswordForm
from app.models.user import User
from app.utils.audit import audit


bp = Blueprint("auth", __name__, url_prefix="/auth")


def _dashboard_url() -> str:
    """
    Decide where to send the user after login / if already logged in.

    1. Try main.index (it will route by role, e.g. admin -> admin dashboard)
    2. Fallback to auth.login so we never crash.
    """
    try:
        return url_for("main.index")
    except BuildError:
        return url_for("auth.login")


# -----------------------------
# LOGIN
# -----------------------------
@bp.route("/login", methods=["GET", "POST"])
def login():
    # already logged in → go to dashboard
    if current_user.is_authenticated:
        return redirect(_dashboard_url())

    form = LoginForm()

    # NOTE: reCAPTCHA is validated automatically here because
    # LoginForm includes `recaptcha = RecaptchaField()`.
    if form.validate_on_submit():
        email = (form.email.data or "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)

            # Audit successful login
            audit(
                user_id=user.id,
                action="user_login",
                resource_type="auth",
                resource_id=user.id,
                details="User logged in via email/password",
            )

            flash("Welcome back!", "success")
            return redirect(_dashboard_url())

        # Optional: audit failed login attempts (no lockout logic, just logging)
        audit(
            user_id=user.id if user else None,
            action="user_login_failed",
            resource_type="auth",
            resource_id=user.id if user else None,
            details=f"Failed login attempt for email={email}",
        )

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


# -----------------------------
# LOGOUT
# -----------------------------
@bp.route("/logout")
@login_required
def logout():
    # Audit logout BEFORE clearing current_user
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
    # if already logged in, no need to see register page
    if current_user.is_authenticated:
        return redirect(_dashboard_url())

    form = RegistrationForm()

    if form.validate_on_submit():
        email = (form.email.data or "").strip().lower()

        # If account already exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("An account with this email already exists.", "warning")
            return render_template("auth/register.html", form=form)

        # Create user
        user = User()
        user.email = email
        user.username = email.split("@")[0] if "@" in email else email
        user.role = form.role.data
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully — please sign in.", "success")
        return redirect(url_for("auth.login"))

    # POST happened but form didn't validate (CSRF, password mismatch, captcha, etc.)
    if request.method == "POST":
        flash("Please check the form for errors and try again.", "danger")

    return render_template("auth/register.html", form=form)


# -----------------------------
# FORGOT PASSWORD (optional)
# -----------------------------
@bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    form = ResetPasswordForm()
    # later: send reset email here
    return render_template("auth/forgot.html", form=form)


# -----------------------------
# RESET PASSWORD (optional)
# -----------------------------
@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # later: look up user by token and set new password
        flash("Password reset successful.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset.html", form=form)
