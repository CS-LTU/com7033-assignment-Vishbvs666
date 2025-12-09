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

# app/__init__.py
from __future__ import annotations

import logging
import os
from datetime import timedelta
from typing import TYPE_CHECKING

from flask import Flask

from app.extensions import db as sa_db, login_manager, csrf
from app.db.mongo import close_mongo_client
from config import Config  # <-- use ROOT config.py, not app.config

if TYPE_CHECKING:
    from config import Config as ConfigType


def create_app(config_object: type[ConfigType] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # ----------------- Config -----------------
    if config_object is not None:
        # e.g. tests can pass their own Config subclass
        app.config.from_object(config_object)
    else:
        # default: use root/config.py::Config
        app.config.from_object(Config)

    # Secret key + session lifetime
    app.secret_key = app.config.get("SECRET_KEY") or os.environ.get(
        "SECRET_KEY",
        "change-me-please",
    )

    minutes = int(
        app.config.get(
            "SECURITY_SESSION_MINUTES",
            os.environ.get("SECURITY_SESSION_MINUTES", 60),
        )
    )
    app.permanent_session_lifetime = timedelta(minutes=minutes)

    # ----------------- Init extensions -----------------
    sa_db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"  # type: ignore[assignment]
    login_manager.login_message_category = "info"

    # ----------------- Blueprints -----------------
    from app.routes.auth import bp as auth_bp
    from app.routes.main import bp as main_bp
    from app.routes.doctor import bp as doctor_bp
    from app.routes.hcp import bp as hcp_bp      
    from app.routes.patient import bp as patient_bp
    from app.routes.predict import bp as predict_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.privacy import bp as privacy_bp


    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(hcp_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(privacy_bp)

    # ----------------- Teardown Mongo -----------------
    @app.teardown_appcontext
    def teardown_mongo(exception: BaseException | None) -> None:  # pragma: no cover
        # close shared Mongo client cleanly
        close_mongo_client(None)

    # ----------------- Logging (optional) -----------------
    if not app.debug and not app.testing:
        logging.basicConfig(level=logging.INFO)

    return app
