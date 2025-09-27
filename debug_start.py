#!/usr/bin/env python3
"""
Debug startup script for PixelParty local development.
This script sets up the environment to use production data from Docker volumes.
"""

import os
import sys
import subprocess
from pathlib import Path
from debug_config import setup_debug_environment

def check_prerequisites():
    """Check if all prerequisites are met for debugging."""
    print("🔍 Checking prerequisites...")

    issues = []

    # Check Python version
    if sys.version_info < (3, 8):
        issues.append(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} is too old. Need Python 3.8+")
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # Check if virtual environment is activated
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is active")
    else:
        print("⚠️  No virtual environment detected. Consider running: source venv/bin/activate")

    # Check project structure
    project_root = Path(__file__).parent
    required_files = [
        'app.py',
        'config.py',
        'requirements.txt',
        'app/__init__.py',
        'app/models.py'
    ]

    for file_path in required_files:
        if (project_root / file_path).exists():
            print(f"✅ {file_path}")
        else:
            issues.append(f"❌ Missing: {file_path}")

    # Check production data availability
    data_dir = project_root / "data"
    media_dir = project_root / "media"

    if data_dir.exists():
        db_file = data_dir / "birthday_party.db"
        if db_file.exists():
            print(f"✅ Production database: {db_file} ({db_file.stat().st_size / 1024:.1f} KB)")
        else:
            issues.append("❌ Production database not found")
    else:
        issues.append("❌ Data directory not found")

    if media_dir.exists():
        photo_count = len(list((media_dir / "photos").glob("*"))) if (media_dir / "photos").exists() else 0
        print(f"✅ Media directory with {photo_count} photos")
    else:
        issues.append("❌ Media directory not found")

    # Check Docker containers
    try:
        result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            if 'pixelparty-app' in result.stdout:
                print("✅ PixelParty Docker container is running")
            else:
                issues.append("❌ PixelParty Docker container not found")
        else:
            issues.append("❌ Cannot check Docker containers")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  Docker not available or not responding")

    # Check Ollama
    try:
        result = subprocess.run(['curl', '-s', 'http://127.0.0.1:11434/api/tags'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Ollama is accessible")
        else:
            print("⚠️  Ollama not accessible at localhost:11434")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  Cannot check Ollama (curl not available)")

    return issues

def check_dependencies():
    """Check if required Python packages are installed."""
    print("\n📦 Checking Python dependencies...")

    required_packages = [
        'flask',
        'yt-dlp',
        'mutagen',
        'PIL',  # Pillow imports as PIL
        'requests',
        'sqlalchemy'
    ]

    missing_packages = []

    package_map = {
        'PIL': 'pillow'  # Map module name to package name
    }

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            display_name = package_map.get(package, package)
            print(f"✅ {display_name}")
        except ImportError:
            display_name = package_map.get(package, package)
            missing_packages.append(display_name)
            print(f"❌ {display_name}")

    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("💡 Install with: pip install -r requirements.txt")
        return False

    return True

def setup_logging():
    """Configure enhanced logging for debugging."""
    import logging

    # Create logs directory
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / "debug.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set specific loggers to DEBUG
    debug_loggers = [
        'app.services.youtube_service',
        'app.services.music_service',
        'app.services.ollama_client',
        'app.routes.api',
        'yt_dlp'
    ]

    for logger_name in debug_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

    print(f"✅ Enhanced logging configured. Logs will be saved to: {logs_dir / 'debug.log'}")

def show_debug_commands():
    """Show useful debugging commands."""
    print("\n🛠️  Useful debugging commands:")
    print("├── Check container logs:     docker logs -f pixelparty-app")
    print("├── Access container shell:   docker exec -it pixelparty-app /bin/bash")
    print("├── Watch log file:          tail -f logs/debug.log")
    print("├── Test YouTube:            python test_youtube.py")
    print("├── Test Ollama:             curl http://127.0.0.1:11434/api/tags")
    print("└── Database query:          sqlite3 data/birthday_party.db '.tables'")

def main():
    """Main debugging setup function."""
    print("🐛 PixelParty Debug Environment Setup")
    print("=" * 50)

    # Check prerequisites
    issues = check_prerequisites()

    if issues:
        print(f"\n❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"   {issue}")
        print("\n💡 Please fix these issues before proceeding.")
        return False

    # Check dependencies
    if not check_dependencies():
        return False

    # Setup environment variables
    print(f"\n🔧 Setting up debug environment...")
    try:
        setup_debug_environment()
        print("✅ Environment variables configured")
    except Exception as e:
        print(f"❌ Error setting up environment: {e}")
        return False

    # Setup logging
    setup_logging()

    # Show debug commands
    show_debug_commands()

    print(f"\n🚀 Debug environment ready!")
    print(f"📍 You can now run:")
    print(f"   python app.py        # Start debug server on port 5001")
    print(f"   python test_youtube.py # Test YouTube functionality")

    return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)