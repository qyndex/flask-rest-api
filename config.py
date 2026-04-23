"""Application configuration classes."""
import os


class BaseConfig:
    """Base configuration shared across environments."""

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    JSON_SORT_KEYS: bool = False


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


class ProductionConfig(BaseConfig):
    """Production configuration."""

    DEBUG: bool = False
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI: str = os.environ.get("DATABASE_URL", "sqlite:///app.db")
