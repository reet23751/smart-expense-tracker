import os
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "smart-expense-tracker-secret-key-2026")
    instance_dir = os.path.join(basedir, "instance")
    os.makedirs(instance_dir, exist_ok=True)
    db_env = os.getenv("DATABASE_URL")
    if not db_env or "instance/smart_tracker.db" in db_env:
        db_path = os.path.join(instance_dir, "smart_tracker.db").replace("\\", "/")
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    else:
        SQLALCHEMY_DATABASE_URI = db_env
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    # Google Gemini AI settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    # Default to modern fast Gemini model
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    # App Settings
    DEFAULT_CURRENCY = "₹"
    DEFAULT_CURRENCY_CODE = "INR"
    ITEMS_PER_PAGE = 15


class TestConfig(Config):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    GEMINI_API_KEY = "test-mock-key"
