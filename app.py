"""Main Flask application entry point."""

import os
from flask import Flask
from flask_migrate import Migrate
from app import create_app, db
from app.models import init_default_settings

# Create Flask app
app = create_app(os.environ.get('FLASK_CONFIG', 'development'))

# Initialize database
with app.app_context():
    db.create_all()
    init_default_settings()

if __name__ == '__main__':
    # For party: bind only to guest network to avoid routing issues
    app.run(host='192.168.4.1', port=5001, debug=True)