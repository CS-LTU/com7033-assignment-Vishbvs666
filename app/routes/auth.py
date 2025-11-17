from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.forms import LoginForm, RegistrationForm, ResetPasswordForm
from app.models.user import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


# -----------------------------
# LOGIN
# -----------------------------
@bp.route("/login", methods=["GET", "POST"])
def login():
    # already logged in → go to main dashboard
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()

    if form.validate_on_submit():
        email = (form.email.data or "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash("Welcome back!", "success")
            return redirect(url_for("main.index"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


# -----------------------------
# LOGOUT
# -----------------------------
@bp.route("/logout")
@login_required
def logout():
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
        return redirect(url_for("main.index"))

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

    # POST happened but form didn't validate (CSRF, password mismatch, etc.)
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
