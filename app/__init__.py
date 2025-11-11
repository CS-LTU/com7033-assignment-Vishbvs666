from __future__ import annotations
import os
from flask import Flask, request, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect

def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # --- SECURITY / CORE CONFIG ---
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or "dev-secret-change-me"
    app.config["SECURITY_PASSWORD_SALT"] = os.environ.get("SECURITY_PASSWORD_SALT") or "dev-salt-change-me"
    app.config["WTF_CSRF_TIME_LIMIT"] = 3600
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # --- LOAD instance/config.py (for DATASET_PATH etc.) ---
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.from_pyfile("config.py", silent=True)
    app.config.setdefault(
        "DATASET_PATH",
        os.path.join(app.instance_path, "healthcare-dataset-stroke-data.csv"),
    )

    # --- SQLITE (auth/sessions/audit) ---
    db_path = os.path.join(app.instance_path, "strokecare.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- MONGO (analytics/patients) ---
    app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME", "strokecare")

    # --- EXTENSIONS ---
    from app.models import db, seed_demo_data
    db.init_app(app)
    CSRFProtect(app)

    with app.app_context():
        db.create_all()
        seed_demo_data()  # only seeds demo auth user(s)

    # --- SECURITY HEADERS ---
    @app.after_request
    def security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        # No external CDNs; SVG charts render server-side.
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none';"
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
        ep = (request.endpoint or "")
        allow = (
            ep.startswith("static.") or ep.startswith("auth.") or
            ep in {"main.healthz", "main.root", "main.mongo_test"}
        )
        if allow:
            return
        if ep.startswith("main.") and not session.get("user_id"):
            nxt = request.full_path or url_for("main.dashboard")
            return redirect(url_for("auth.login_get", next=nxt))

    # --- TEARDOWN MONGO ---
    from app.db.mongo import close_mongo
    app.teardown_appcontext(close_mongo)

    @app.errorhandler(403)
    def forbidden(_e):
        from flask import render_template
        return render_template("error/403.html"), 403

    return app
