"""Main Flask application entry point."""

import os
from datetime import datetime
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

@app.route('/health')
def health_check():
    """Health check endpoint for container monitoring."""
    try:
        # Test database connection
        with app.app_context():
            db.engine.execute('SELECT 1')
        return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 503

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=5001, debug=True)