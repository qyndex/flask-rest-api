"""Shared pytest fixtures for the Flask REST API test suite."""
import pytest

from app import create_app
from app.auth import create_access_token
from app.extensions import db as _db
from app.models import User


@pytest.fixture(scope="session")
def app():
    """Create the Flask application configured for testing.

    Uses an in-memory SQLite database so no external services are needed.
    Session-scoped so the app is only constructed once per test run.
    """
    flask_app = create_app("config.TestingConfig")
    return flask_app


@pytest.fixture(autouse=True)
def _reset_db(app):
    """Drop and recreate all tables before each test for a clean slate."""
    with app.app_context():
        _db.create_all()
        yield
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def db(app):
    """Provide the database extension inside an app context."""
    with app.app_context():
        yield _db


@pytest.fixture()
def client(app):
    """Return a Flask test client with the database already set up."""
    return app.test_client()


@pytest.fixture()
def test_user(app):
    """Create and return a test user for authenticated requests."""
    with app.app_context():
        user = User(email="test@example.com", full_name="Test User")
        user.set_password("testpass123")
        _db.session.add(user)
        _db.session.commit()
        # Refresh to ensure all attributes are loaded
        _db.session.refresh(user)
        return user


@pytest.fixture()
def auth_headers(app, test_user):
    """Return Authorization headers with a valid JWT for test_user."""
    with app.app_context():
        token = create_access_token(test_user)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
