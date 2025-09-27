"""Debug configuration for local development with production data."""

import os
from pathlib import Path

# Set environment variables for debugging with production data
def setup_debug_environment():
    """Configure environment for local debugging with production data."""

    # Get absolute path to project
    project_root = Path(__file__).resolve().parent

    # Use production database from Docker volume
    database_path = project_root / "data" / "birthday_party.db"

    # Set environment variables
    env_vars = {
        'FLASK_CONFIG': 'development',
        'DATABASE_URL': f'sqlite:///{database_path}',
        'OLLAMA_BASE_URL': 'http://127.0.0.1:11434',
        'SECRET_KEY': 'debug-secret-key-for-local-development',
        'FLASK_ENV': 'development',
        'FLASK_DEBUG': '1'
    }

    # Set all environment variables
    for key, value in env_vars.items():
        os.environ[key] = str(value)
        print(f"Set {key}={value}")

    # Verify database exists
    if database_path.exists():
        print(f"✅ Production database found: {database_path}")
        print(f"   Size: {database_path.stat().st_size / 1024:.1f} KB")
    else:
        print(f"❌ Database not found: {database_path}")

    # Check media directory
    media_path = project_root / "media"
    if media_path.exists():
        photos = len(list((media_path / "photos").glob("*"))) if (media_path / "photos").exists() else 0
        videos = len(list((media_path / "videos").glob("*"))) if (media_path / "videos").exists() else 0
        music = len(list((media_path / "music").glob("*"))) if (media_path / "music").exists() else 0
        print(f"✅ Media directory found: {photos} photos, {videos} videos, {music} music files")
    else:
        print(f"❌ Media directory not found: {media_path}")

    return env_vars

if __name__ == "__main__":
    print("🐛 Setting up debug environment...")
    setup_debug_environment()
    print("\n🚀 Environment ready! Run: python app.py")