# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Birthday Party Memory & Music App** designed for a 2-day 50th birthday celebration. The app runs on a Raspberry Pi 4 with a big screen display and provides a mobile web interface for guests to:

- Share photos and videos with birthday wishes
- Suggest music (mood-based search via LLM + local library + YouTube fallback)
- View real-time slideshow and music queue on the big screen
- Generate a beautiful digital memory book as a final gift

## Current Status

**Project Phase:** Planning and Documentation
- PRD (Product Requirements Document) completed
- Phase-specific development prompts created (Phase1-4)
- Architecture decisions documented
- **No code implementation has begun yet**

## Technical Architecture

**Framework:** Originally planned for NiceGUI, but Phase1 prompts suggest using Reflex
**Database:** SQLite with file attachments
**LLM Integration:** Ollama API for mood-based music suggestions
**Music:** Local 20GB library + yt-dlp YouTube fallback
**Platform:** Raspberry Pi 4 (8GB recommended)
**Storage:** Local-only (no cloud, privacy-focused)

## File Structure (Planned)

```
birthday_app/
├── app.py                 # Main NiceGUI application
├── database/
│   ├── models.py         # SQLite models
│   └── migrations.py     # Database setup
├── static/
│   ├── uploads/          # Photo/video storage
│   ├── music/            # Music library
│   └── css/              # Custom styles
├── templates/
│   └── memory_book_template.html
├── services/
│   ├── music_service.py  # Music search/download
│   ├── ollama_service.py # LLM integration
│   └── usb_export_service.py # Memory book generator
├── export/               # Generated USB content
└── config.py             # App configuration
```

## Development Commands

**Current Status:** No code implementation exists yet. This is a planning and documentation phase project.

**Planned Framework Commands (when implementation begins):**
- If using Reflex: `reflex run` - Start the application
- If using NiceGUI: `python app.py` - Start the application
- `python -m pytest tests/` - Run tests (when implemented)
- `pip install -r requirements.txt` - Install dependencies

**Available Development Resources:**
- `PRD.md` - Complete Product Requirements Document
- `prompts/Phase1.md` - Phase 1 implementation guidance (foundational setup)
- `prompts/Phase2.md` - Phase 2 implementation guidance
- `prompts/Phase3.md` - Phase 3 implementation guidance  
- `prompts/Phase4.md` - Phase 4 implementation guidance
- `tricks.MD` - MCP server setup instructions for development environment

## Key Requirements

### Target Users
- **Guests:** Ages 8-80, minimal technical skills, mobile phones
- **Host:** Party administrator with content moderation needs
- **Celebrant:** Recipient of the digital memory book

### Core Features
1. **Mobile Interface:** QR code access, photo/video upload, birthday wishes, music suggestions
2. **Big Screen Display:** Real-time slideshow, music queue, celebratory interface
3. **Music System:** Local library search, LLM mood suggestions, YouTube fallback via yt-dlp
4. **Memory Book:** Standalone HTML export with embedded media for USB delivery

### Database Schema
- `guests` - Session management and names
- `photos` - Uploaded media with wishes and metadata
- `music_queue` - Song requests with play status
- `music_library` - Indexed local music collection
- `settings` - App configuration

### Security & Privacy
- All data stays local on Raspberry Pi
- No cloud storage or external transmission
- QR code access only (no permanent URLs)
- Host content moderation system
- Anonymous submissions supported

## Development Phases

The project is structured in 4 phases with detailed implementation prompts:

1. **Phase 1:** Framework setup (Reflex/NiceGUI), SQLite models, basic mobile interface, file uploads
2. **Phase 2:** Big screen slideshow, real-time displays, music player, QR codes  
3. **Phase 3:** Music library indexing, search, Ollama LLM integration, YouTube fallback
4. **Phase 4:** UI polish, memory book generator, admin panel, testing

Each phase has a detailed implementation prompt in the `prompts/` directory.

## Architecture Decisions

**Framework Choice:** The PRD originally suggested NiceGUI, but Phase1 prompts reference Reflex. Both are valid choices:
- **NiceGUI:** Python-only, rapid development, built-in WebSocket support
- **Reflex:** Modern Python web framework, better performance, component-based

**Key Technical Requirements:**
- Local-only operation (no cloud services)
- Real-time updates via WebSockets
- Mobile-first responsive design
- File upload handling (photos/videos up to 50MB)
- Audio processing and music library management
- SQLite database with proper schema (see PRD.md for full schema)

## Important Implementation Notes

- Target users: ages 8-80 with minimal technical skills
- Performance requirement: <2 second upload times, zero crashes during 2-day event
- Final deliverable: complete party experience + standalone USB memory book
- Privacy-focused: all data stays on local Raspberry Pi
- Content moderation system required for host approval