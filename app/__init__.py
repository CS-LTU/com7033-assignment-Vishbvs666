import os
from flask import Flask

from . import config as _config       # importing the module
from .extensions import db, login_manager
from .rate_limit import limiter
from .db.mongo import init_mongo
from .routes.main import bp as main_bp

def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
        instance_relative_config=True,
    )
    os.makedirs(app.instance_path, exist_ok=True)

    # 1) Config
    _config.load_config(app)

    # 2) Extensions
    db.init_app(app)
    init_mongo(app)
    limiter.init_app(app)
    login_manager.init_app(app)

    # 3) Blueprints
    app.register_blueprint(main_bp)
    # app.register_blueprint(auth_bp)  # ← enable after we add auth blueprint

    # 4) Tables
    with app.app_context():
        from . import models  # ensure models registered
        db.create_all()

    # 5) Security headers
    @app.after_request
    def _secure_headers(resp):
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
        )
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        return resp

    return app
