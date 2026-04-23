"""Application configuration classes."""
import os


class BaseConfig:
    """Base configuration shared across environments."""

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-change-in-production-at-least-32-bytes")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    JSON_SORT_KEYS: bool = False
    CORS_ORIGINS: str = os.environ.get("CORS_ORIGINS", "*")

    # JWT settings (used by app.auth)
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", "1800"))  # seconds


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL", "sqlite:///dev.db"
    )


class TestingConfig(BaseConfig):
    """Testing configuration."""

    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    # Disable rate limiting in tests
    RATELIMIT_ENABLED: bool = False


class ProductionConfig(BaseConfig):
    """Production configuration."""

    DEBUG: bool = False
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "")  # MUST be set in env
    SQLALCHEMY_DATABASE_URI: str = os.environ.get("DATABASE_URL", "")
    CORS_ORIGINS: str = os.environ.get("CORS_ORIGINS", "")
