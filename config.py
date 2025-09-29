"""Flask configuration settings."""

import os
from pathlib import Path

class Config:
    """Base configuration."""
    
    # Get project root directory
    BASE_DIR = Path(__file__).resolve().parent
    
    # Basic Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'birthday-party-secret-key-change-in-production'
    
    # Database with explicit UTF-8 encoding for emoji support
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///birthday_party.db?charset=utf8'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False},
        'pool_pre_ping': True,
        'echo': False
    }
    
    # File upload settings
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    UPLOAD_FOLDER = BASE_DIR / 'media' / 'photos'
    VIDEO_FOLDER = BASE_DIR / 'media' / 'videos'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'mp4', 'mov', 'avi', 'mkv', 'webm'}
    
    # Music library settings
    MUSIC_LIBRARY_PATH = Path('/mnt/pixelparty/Music')  # Source library
    MUSIC_COPY_FOLDER = BASE_DIR / 'media' / 'music'        # Destination for selected songs
    SUPPORTED_AUDIO_FORMATS = {'.mp3', '.flac', '.m4a', '.ogg', '.wav', '.aac'}
    
    # Ollama settings
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL') or 'http://127.0.0.1:11434'
    PREFERRED_MODEL = 'deepseek-r1:8b'
    
    # Party settings
    PARTY_TITLE = '50th Birthday Celebration'
    HOST_NAME = 'Birthday Star'
    SLIDESHOW_DURATION = 8  # seconds per photo
    MAX_SUBMISSIONS_PER_GUEST = 10
    
    # Memory book settings
    EXPORT_FOLDER = BASE_DIR / 'export'
    
    @staticmethod
    def init_app(app):
        """Initialize app with config."""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.VIDEO_FOLDER, exist_ok=True)
        os.makedirs(Config.MUSIC_COPY_FOLDER, exist_ok=True)
        os.makedirs(Config.EXPORT_FOLDER, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}