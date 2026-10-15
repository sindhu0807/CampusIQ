import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "local-only-change-this-secret"
    )

        # Support common Neon and Vercel PostgreSQL variable names.
    database_url = (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("POSTGRES_PRISMA_URL")
        or os.getenv("NEON_DATABASE_URL")
    )

    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://", "postgresql+psycopg://", 1
            )
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )

        SQLALCHEMY_DATABASE_URI = database_url
    else:
        raise RuntimeError(
            "No PostgreSQL connection variable is available. "
            "Check DATABASE_URL, POSTGRES_URL, "
            "POSTGRES_PRISMA_URL, and NEON_DATABASE_URL."
        )

        SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{BASE_DIR / 'campusiq.db'}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True
    }

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = (
        os.getenv("VERCEL") == "1"
    )
