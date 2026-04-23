"""Shared pytest fixtures for the Flask REST API test suite."""
import pytest

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    """Create the Flask application configured for testing.

    Uses an in-memory SQLite database so no external services are needed.
    Session-scoped so the app is only constructed once per test run.
    """
    flask_app = create_app("config.TestingConfig")
    return flask_app


@pytest.fixture(scope="session")
def _db_tables(app):
    """Create all tables once per session, then drop them at teardown."""
    with app.app_context():
        _db.create_all()
        yield
        _db.drop_all()


@pytest.fixture()
def db(app, _db_tables):
    """Provide a transactional database session that is rolled back after each test.

    Each test gets a clean slate without needing to recreate the schema.
    """
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        # Bind the session to this connection so the same transaction is used
        _db.session.bind = connection

        yield _db

        _db.session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(app, db):
    """Return a Flask test client with the database already set up."""
    return app.test_client()
