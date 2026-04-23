"""Flask REST API application factory."""
from flask import Flask

from .extensions import db, ma, migrate
from .api.routes import api_bp


def create_app(config_object: str = "config.DevelopmentConfig") -> Flask:
    """Create and configure the Flask application.

    Args:
        config_object: Dotted-path to a config class.

    Returns:
        Configured Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Initialise extensions
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
