"""WSGI entry point for Gunicorn."""

import os
from app import create_app, db
from app.models import init_default_settings

# Create Flask app
app = create_app(os.environ.get('FLASK_CONFIG', 'production'))

# Initialize database
with app.app_context():
    db.create_all()
    init_default_settings()

if __name__ == "__main__":
    app.run()