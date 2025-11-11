import os

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-not-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///strokecare.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    # NEW: dataset path (override in instance/config.py if needed)
    DATASET_PATH = os.getenv("DATASET_PATH", os.path.join(os.path.dirname(__file__), "instance", "healthcare-dataset-stroke-data.csv"))

class DevConfig(BaseConfig):
    DEBUG = True

Config = DevConfig
