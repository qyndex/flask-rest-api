"""Flask REST API application factory."""
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import ValidationError

from .api.auth_routes import auth_bp
from .api.routes import api_bp
from .extensions import db, ma, migrate

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour", "50 per minute"],
    storage_uri="memory://",
)


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
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    limiter.init_app(app)

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")

    # ---- Application-wide error handlers ----
    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return jsonify({"error": "Validation failed", "details": err.messages}), 422

    @app.errorhandler(429)
    def handle_rate_limit(err):
        return jsonify({"error": "Rate limit exceeded", "message": str(err.description)}), 429

    @app.errorhandler(500)
    def handle_internal_error(err):
        return jsonify({"error": "Internal server error"}), 500

    # Health check
    @app.get("/health")
    def health():
        return jsonify({"status": "healthy"})

    return app
