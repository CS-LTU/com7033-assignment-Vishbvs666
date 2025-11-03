from __future__ import annotations
import os, secrets
from flask import Flask, request, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect

def create_app() -> Flask:
    app = Flask(__name__)

    # --- SECURITY CONFIG ---
    app.config["SECRET_KEY"] = (
        os.environ.get("SECRET_KEY") or "dev-secret-change-me"
    )
    app.config["WTF_CSRF_TIME_LIMIT"] = 3600
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Enable CSRF protection globally
    csrf = CSRFProtect(app)

    # --- SECURITY HEADERS ---
    @app.after_request
    def security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none';"
        )
        return resp

    # --- BLUEPRINTS ---
    from .routes.main import bp as main_bp
    from .auth import bp as auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="")

    # --- AUTH-FIRST RULE ---
    @app.before_request
    def require_login():
        ep = request.endpoint or ""
        if ep.startswith("static.") or ep.startswith("auth.") or ep in {"main.healthz"}:
            return
        # if main routes but user is not logged in → redirect to login
        if ep.startswith("main.") and not session.get("user_id"):
            return redirect(url_for("auth.login_get", next=request.full_path or "/login"))

    return app
