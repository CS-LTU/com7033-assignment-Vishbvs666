from __future__ import annotations
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from app.forms import LoginForm, RegisterForm
from app.models import db, User, Session as UserSession
from app.utils.audit import log_event

# Code for the token helpers for password reset
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf import FlaskForm
from app.utils.password_reset import make_reset_token, load_reset_email

bp = Blueprint("auth", __name__, url_prefix="")

# ------------------------
# Login / Register / Logout
# ------------------------

@bp.get("/login")
def login_get():
    return render_template("auth/login.html", form=LoginForm())

@bp.post("/login")
def login_post():
    form = LoginForm()
    if form.validate_on_submit():
        email = (form.email.data or "").lower().strip()
        password = (form.password.data or "").strip()
        role = (form.role.data or "").strip()

        user = User.query.filter_by(email=email).first()
        if not user or not password or not user.check_password(password):
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html", form=form), 400
        if role != user.role:
            flash("Selected role doesn’t match this account.", "error")
            return render_template("auth/login.html", form=form), 400
        if not user.is_active:
            flash("Your account is inactive. Contact admin.", "error")
            return render_template("auth/login.html", form=form), 403

        # update last_login
        user.last_login = datetime.utcnow()

        # create DB session row
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        s = UserSession.create_for(user_id=user.id, ip=ip, ttl_hours=8)
        db.session.flush()

        # audit
        log_event(user.id, "login", resource_type="user", resource_id=str(user.id), details=f"ip={ip}")
        db.session.commit()

        # browser session
        session.clear()
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["role"] = user.role
        session["db_session_token"] = s.session_token

        flash(f"Signed in as {user.role.title()}.", "success")
        nxt = request.args.get("next") or url_for("main.dashboard")
        return redirect(nxt)

    flash("Please fix the errors and try again.", "error")
    return render_template("auth/login.html", form=form), 400

@bp.get("/register")
def register_get():
    return render_template("auth/register.html", form=RegisterForm())

@bp.post("/register")
def register_post():
    form = RegisterForm()
    if form.validate_on_submit():
        email = (form.email.data or "").lower().strip()
        name  = (form.name.data or "").strip() or "User"
        role  = (form.role.data or "").strip()
        pwd   = (form.password.data or "").strip()

        if not pwd or len(pwd) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("auth/register.html", form=form), 400

        if User.query.filter_by(email=email).first():
            flash("That email is already registered.", "error")
            return render_template("auth/register.html", form=form), 400

        user = User(
            name=name,
            email=email,
            role=role,
            username=(email.split("@", 1)[0])[:40],
        )
        user.set_password(pwd)
        db.session.add(user)
        db.session.flush()

        # create session row for new user
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        s = UserSession.create_for(user_id=user.id, ip=ip, ttl_hours=8)
        log_event(user.id, "register", resource_type="user", resource_id=str(user.id), details=f"ip={ip}")
        db.session.commit()

        session.clear()
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["role"] = user.role
        session["db_session_token"] = s.session_token

        flash("Account created.", "success")
        return redirect(url_for("main.dashboard"))

    flash("Please fix the errors and try again.", "error")
    return render_template("auth/register.html", form=form), 400

@bp.get("/logout")
def logout_get():
    token = session.get("db_session_token")
    uid = session.get("user_id")
    if token:
        s = UserSession.query.filter_by(session_token=token).first()
        if s:
            db.session.delete(s)
            log_event(uid, "logout", resource_type="user", resource_id=str(uid))
            db.session.commit()
    session.clear()
    flash("Signed out successfully.", "success")
    return redirect(url_for("auth.login_get"))

@bp.post("/logout")
def logout_post():
    return logout_get()

@bp.get("/demo")
def demo_login():
    # TIP: point this to one of your seeded users if you like
    user = User.query.filter_by(email="doctor@example.com").first()
    if not user:
        flash("Demo users not seeded yet.", "error")
        return redirect(url_for("auth.login_get"))
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    s = UserSession.create_for(user_id=user.id, ip=ip, ttl_hours=8)
    log_event(user.id, "login", resource_type="user", resource_id=str(user.id), details="demo")
    db.session.commit()
    session.clear()
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["role"] = user.role
    session["db_session_token"] = s.session_token
    flash("You're in! (demo user)", "success")
    nxt = request.args.get("next") or url_for("main.dashboard")
    return redirect(nxt)

# ------------------------
# Forgot / Reset password
# ------------------------

class ForgotForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send reset link")

class ResetForm(FlaskForm):
    password = PasswordField("New password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Set new password")

@bp.get("/forgot")
def forgot_get():
    return render_template("auth/forgot.html", form=ForgotForm())

@bp.post("/forgot")
def forgot_post():
    form = ForgotForm()
    if not form.validate_on_submit():
        flash("Please fix the errors and try again.", "error")
        return render_template("auth/forgot.html", form=form), 400

    email = (form.email.data or "").lower().strip()
    user = User.query.filter_by(email=email).first()

    # Do not reveal whether the email exists
    if user:
        token = make_reset_token(user.email)
        reset_url = url_for("auth.reset_get", token=token, _external=True)
        current_app.logger.info("Password reset link for %s: %s", user.email, reset_url)

    flash("If that email exists, a reset link was generated (check server logs).", "success")
    return redirect(url_for("auth.login_get"))

@bp.get("/reset/<token>")
def reset_get(token):
    email = load_reset_email(token)
    if not email:
        flash("Reset link is invalid or expired.", "error")
        return redirect(url_for("auth.forgot_get"))
    return render_template("auth/reset.html", form=ResetForm(), token=token)

@bp.post("/reset/<token>")
def reset_post(token):
    email = load_reset_email(token)
    if not email:
        flash("Reset link is invalid or expired.", "error")
        return redirect(url_for("auth.forgot_get"))

    form = ResetForm()
    if not form.validate_on_submit():
        return render_template("auth/reset.html", form=form, token=token), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Account not found.", "error")
        return redirect(url_for("auth.forgot_get"))

    user.set_password(form.password.data)
    db.session.commit()
    flash("Your password was updated. Please sign in.", "success")
    return redirect(url_for("auth.login_get"))
