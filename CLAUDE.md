# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PixelParty is a Flask-based birthday party memory collection app designed for a 50th birthday celebration. It allows guests to upload photos with wishes via mobile interface and displays them on a big screen with text overlays.

**Key Principle:** This is a one-time use app for a 2-day party. Keep it simple and functional.

## Essential Commands

### Development
```bash
# Start development server
python app.py

# Install dependencies
pip install -r requirements.txt

# Run with virtual environment
source venv/bin/activate  # or venv/Scripts/activate on Windows
python app.py
```

### Database
```bash
# Create database tables (auto-run on startup)
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

## Architecture Overview

### Tech Stack
- **Framework:** Flask + HTMX for dynamic interactions
- **Frontend:** daisyUI components + Tailwind CSS
- **Database:** SQLite with models in `app/models.py`
- **LLM Integration:** Ollama client for music suggestions
- **Music Handling:** Mutagen for metadata, yt-dlp for downloads

### Application Structure
```
PixelParty/
├── app.py                  # Main application entry point
├── config.py               # Configuration settings
├── app/
│   ├── __init__.py         # App factory
│   ├── models.py           # Database models
│   ├── routes/             # Blueprint routes
│   │   ├── mobile.py       # Mobile guest interface
│   │   ├── big_screen.py   # Display slideshow
│   │   ├── api.py          # HTMX endpoints
│   │   └── admin.py        # Admin controls
│   ├── services/           # Business logic
│   │   ├── music_service.py    # Music search/download
│   │   ├── ollama_client.py    # LLM integration
│   │   ├── music_library.py    # Local music indexing
│   │   └── file_handler.py     # Media file processing
│   └── static/             # Static assets
├── templates/              # Jinja2 templates
│   ├── mobile/            # Guest mobile interface
│   ├── big_screen/        # Display screens  
│   └── components/        # Reusable template parts
└── media/                 # Uploaded content (created at runtime)
    ├── photos/
    ├── videos/
    └── music/
```

### Database Schema
- **guests**: Party guests with session management
- **photos**: Photo uploads with wish messages
- **music_queue**: Song requests and queue management
- **music_library**: Indexed local music collection
- **settings**: App configuration

## Key Configuration

### File Paths (config.py)
- Photos: `media/photos/`
- Videos: `media/videos/`
- Music Library Source: `/mnt/media/MUSIC`
- Music Copies: `media/music/`
- Export: `export/`

### Important Settings
- Max file size: 50MB
- Slideshow duration: 8 seconds per photo
- Ollama model: `deepseek-r1:8b`

## Development Guidelines

### Working with Routes
- Mobile interface: `/mobile/*` - Guest photo/wish submission
- Big screen: `/` and `/display/*` - Slideshow and real-time display  
- API endpoints: `/api/*` - HTMX dynamic updates
- Admin: `/admin/*` - Party management

### HTMX Integration
The app uses HTMX for dynamic updates without page reloads:
- Real-time slideshow updates
- Live queue displays
- Form submissions with immediate feedback

### Music System
1. **Local Library**: Scans `/mnt/media/MUSIC` for existing songs
2. **LLM Suggestions**: Uses Ollama for mood-based recommendations
3. **YouTube Fallback**: Downloads audio with yt-dlp if not found locally

### Visual Effects
All animations use pure CSS (no JavaScript frameworks):
- Ken Burns effect on photos
- Text overlay animations
- Smooth transitions between photos

## Common Development Tasks

### Adding New Routes
Register blueprints in `app/__init__.py`:
```python
app.register_blueprint(new_bp, url_prefix='/prefix')
```

### Database Changes
Models are in `app/models.py`. Database is auto-created on app startup.

### Template System
- Base template: `templates/base.html` with daisyUI/Tailwind
- Mobile templates: `templates/mobile/`
- Big screen templates: `templates/big_screen/`

### Media File Handling
File uploads processed by `app/services/file_handler.py`:
- Automatic resizing for big screen display
- File type validation
- Thumbnail generation

## Important Notes

### Project Context
This codebase was built iteratively with lessons learned documented in `nexttime.md`. The key insight: keep things simple for a short-term party app.

### Performance Considerations
- Designed for Raspberry Pi 4 deployment
- Lightweight stack chosen for smooth operation
- Local-first approach (no external dependencies during party)

### Party Day Workflow
1. Start app on Raspberry Pi connected to big screen
2. Guests scan QR code to access mobile interface
3. Real-time display shows photos with wishes overlaid
4. Music plays from suggestions/local library
5. Export memory book at end of party

The app prioritizes simplicity and reliability over feature completeness - it needs to work flawlessly for the party duration.