"""
TaskFlow API - A RESTful Task Management Application
Author: Rahel Siburian (NIM: 0110225159)
"""

from flask import Flask
from .config import Config
from .database import init_db


def create_app(config_class=Config):
    """Application factory pattern for creating Flask app instance."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize database
    init_db(app)

    # Register blueprints
    from .routes import tasks_bp, auth_bp, health_bp
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(health_bp, url_prefix="/api")

    return app
