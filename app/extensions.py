# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect   # this import path is fine

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

# --------------------------
# User loader required by Flask-Login
# --------------------------
@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))
