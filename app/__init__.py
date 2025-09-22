"""Flask app factory."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name='default'):
    """Create Flask application using app factory pattern."""
    
    app = Flask(__name__, template_folder='../templates', static_folder='static')
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from app.routes.mobile import mobile_bp
    from app.routes.big_screen import big_screen_bp
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(mobile_bp, url_prefix='/mobile')
    app.register_blueprint(big_screen_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp)
    
    # Main route
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Note: Media file routes are handled by app/routes/__init__.py
    
    return app