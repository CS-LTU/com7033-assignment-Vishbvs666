from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"   # type: ignore[attr-defined]
login_manager.session_protection = "strong"  # type: ignore[attr-defined]
login_manager.login_message_category = "warning"  # type: ignore[attr-defined]
