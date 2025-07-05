"""
Configuration Settings
Centralized configuration management for the Sentiment Analysis Platform.
"""

import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    """Base configuration class."""
    
    # Application Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # File Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # API Settings
    GOOGLE_CLOUD_API_URL = "https://language.googleapis.com/v1/documents:analyzeSentiment"
    MAX_TEXT_LENGTH = 1000  # Maximum text length for API processing
    MIN_TEXT_LENGTH = 10    # Minimum text length for analysis
    
    # Sentiment Analysis Settings
    POSITIVE_THRESHOLD = 0.02
    NEGATIVE_THRESHOLD = -0.02
    CONFIDENCE_MULTIPLIER = 200
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        # Ensure upload directory exists
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            file_handler = RotatingFileHandler(
                'logs/sentiment-analysis.log', 
                maxBytes=10240000, 
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Sentiment Analysis Platform startup')

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'test_uploads')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}