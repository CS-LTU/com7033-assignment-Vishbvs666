from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

bp = Blueprint("auth", __name__, url_prefix="")

# ---------------------
# Flask-WTF Forms
# ---------------------
class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[
        DataRequired(message="Email is required."),
        Email(message="Enter a valid email address.")
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required."),
        Length(min=8, max=128, message="Password must be between 8–128 characters.")
    ])
    submit = SubmitField("Sign in")


class RegisterForm(FlaskForm):
    name = StringField("Full name", validators=[
        DataRequired(message="Full name is required."),
        Length(min=2, max=80, message="Name must be 2–80 characters.")
    ])
    email = EmailField("Email", validators=[
        DataRequired(message="Email is required."),
        Email(message="Enter a valid email address.")
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required."),
        Length(min=8, max=128, message="Password must be between 8–128 characters.")
    ])
    confirm = PasswordField("Confirm password", validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo("password", message="Passwords must match.")
    ])
    submit = SubmitField("Create account")


# ---------------------
# Routes (UI-only for now)
# ---------------------

@bp.get("/login")
def login_get():
    """Render the login form."""
    form = LoginForm()
    return render_template("auth/login.html", form=form)


@bp.post("/login")
def login_post():
    """Validate login form submission."""
    form = LoginForm()
    if form.validate_on_submit():
        # TODO: Add DB lookup and password check later
        flash("Signed in (demo). We'll wire real authentication soon.", "success")
        return redirect(url_for("main.dashboard"))
    flash("Please fix the errors and try again.", "error")
    return render_template("auth/login.html", form=form), 400


@bp.get("/register")
def register_get():
    """Render the registration form."""
    form = RegisterForm()
    return render_template("auth/register.html", form=form)


@bp.post("/register")
def register_post():
    """Validate registration form submission."""
    form = RegisterForm()
    if form.validate_on_submit():
        # TODO: Add DB save and password hashing later
        flash("Account created (demo). You can now sign in.", "success")
        return redirect(url_for("auth.login"))
    flash("Please fix the errors and try again.", "error")
    return render_template("auth/register.html", form=form), 400


@bp.post("/logout")
def logout():
    """Log the user out (session clear)."""
    # TODO: Clear session in real version
    flash("Signed out.", "success")
    return redirect(url_for("auth.login"))
