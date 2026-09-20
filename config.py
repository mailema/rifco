"""
Central configuration for the RIFCO application.

All values that differ between development and production come from
environment variables (loaded from .env in development). Nothing
sensitive is hard-coded here.
"""

import os
import secrets

# In development, if SECRET_KEY is not set, generate a clearly-marked
# fallback so the app can still run. This value is NOT persisted, so
# sessions are invalidated whenever the process restarts. It must never
# be used in production.
_DEV_FALLBACK_SECRET_KEY = "dev-only-insecure-key-" + secrets.token_hex(8)


def _normalize_database_url(url: str) -> str:
    """
    Neon and some other providers hand out URLs starting with
    'postgres://'. SQLAlchemy needs 'postgresql://' at minimum, and
    since requirements.txt installs psycopg (v3) rather than the
    older psycopg2, the driver must be named explicitly as
    'postgresql+psycopg://' - otherwise SQLAlchemy defaults to
    trying psycopg2, which isn't installed, and the app fails to
    import entirely.
    """
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Config:
    # ---- Secret key -----------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY") or _DEV_FALLBACK_SECRET_KEY

    # ---- Database ----------------------------------------------------
    _raw_database_url = os.environ.get("DATABASE_URL", "")
    _database_url = _normalize_database_url(_raw_database_url)

    if _database_url:
        SQLALCHEMY_DATABASE_URI = _database_url
        USING_FALLBACK_DATABASE = False
    else:
        # Development-only fallback so the project runs without a real
        # Postgres/Neon database configured. This must never be relied
        # on in production - set DATABASE_URL instead.
        SQLALCHEMY_DATABASE_URI = "sqlite:///rifco_dev.db"
        USING_FALLBACK_DATABASE = True

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- Uploads -------------------------------------------------------
    UPLOAD_FOLDER = os.path.join("static", "uploads", "players")
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024  # 3 MB max upload

    # ---- Session / cookie security --------------------------------
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME_SECONDS = 60 * 60 * 8  # 8 hours

    FLASK_ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = FLASK_ENV != "production"

    # In production, cookies must only travel over HTTPS.
    SESSION_COOKIE_SECURE = FLASK_ENV == "production"
