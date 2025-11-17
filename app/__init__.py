from flask import Flask
from app.extensions import db, login_manager, csrf

def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=True)

    # Load config
    if config_object:
        app.config.from_object(config_object)
    else:
        app.config.from_pyfile("config.py", silent=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"  # type: ignore[assignment]
    login_manager.login_message_category = "warning"

    # Blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.main import bp as main_bp
    from app.routes.patients import bp as patients_bp
    from app.routes.predict import bp as predict_bp
    from app.routes.admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(admin_bp)

    return app
