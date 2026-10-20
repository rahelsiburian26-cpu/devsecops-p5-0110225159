"""
Configuration module for TaskFlow API.
Manages different environment configurations: development, testing, production.
"""

import os


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DATABASE_URI = os.environ.get("DATABASE_URI", "sqlite:///taskflow.db")
    DEBUG = False
    TESTING = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    JWT_EXPIRATION_HOURS = 24
    ALLOWED_EXTENSIONS = {"json", "csv"}


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    DATABASE_URI = "sqlite:///taskflow_dev.db"


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret-key"


class ProductionConfig(Config):
    """Production environment configuration."""
    DATABASE_URI = os.environ.get("DATABASE_URI", "postgresql://localhost/taskflow_prod")
    SECRET_KEY = os.environ.get("SECRET_KEY")

    @classmethod
    def validate(cls):
        """Validate that required production environment variables are set."""
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable must be set in production")


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
