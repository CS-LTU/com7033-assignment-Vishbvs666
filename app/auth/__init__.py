from __future__ import annotations
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.forms import LoginForm, RegisterForm  # <-- import from forms only

bp = Blueprint("auth", __name__, url_prefix="")

@bp.get("/login")
def login_get():
    return render_template("auth/login.html", form=LoginForm())

@bp.post("/login")
def login_post():
    form = LoginForm()
    if form.validate_on_submit():
        session["user_id"] = "demo-user"
        session["user_name"] = (form.email.data or "").split("@", 1)[0].title() or "User"
        flash("Signed in (demo).", "success")
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
        session["user_id"] = "demo-user"
        session["user_name"] = (form.name.data or "").strip() or "User"
        flash("Account created (demo).", "success")
        return redirect(url_for("main.dashboard"))
    flash("Please fix the errors and try again.", "error")
    return render_template("auth/register.html", form=form), 400

@bp.post("/logout")
def logout():
    session.clear()
    flash("Signed out successfully.", "success")
    return redirect(url_for("auth.login_get"))

@bp.get("/demo")
def demo_login():
    # minimal demo identity
    session["user_id"] = "demo-user"
    session["user_name"] = "Demo User"
    flash("You're in! (demo session, no database)", "success")
    nxt = request.args.get("next") or url_for("main.dashboard")
    return redirect(nxt)
