# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Birthday Party Memory & Music App - A **Reflex-based web application** designed for a 2-day 50th birthday celebration. Runs on Raspberry Pi 4 with big screen display and mobile interface for guests to share photos, videos, wishes, and music suggestions.

## Current Status

**Pre-implementation phase** - Documentation and planning complete, no code exists yet.

## Technical Architecture

**Framework:** Reflex (Pure Python with React frontend)
**Database:** SQLite with local file storage  
**LLM Integration:** Ollama API for mood-based music suggestions
**Music System:** Local 20GB library + yt-dlp YouTube fallback
**Platform:** Raspberry Pi 4 (8GB recommended)
**Privacy:** Local-only storage, no cloud services

## Development Commands

**When implementation begins:**
- `reflex init` - Initialize new Reflex project
- `reflex run` - Start development server
- `pip install reflex pillow sqlite3 yt-dlp mutagen` - Install core dependencies

## Project Structure (from Phase 1 requirements)

**Core Routes:**
- `/` - Mobile guest interface (QR code access)
- `/big-screen` - Full-screen slideshow display
- `/admin` - Host moderation panel

**Database Schema:**
- `guests` - Session management (name, session_id, submissions count)
- `photos` - Media uploads (filename, wish_message, display_duration)
- `music_queue` - Song requests (title, artist, source, play status)
- `music_library` - Local music indexing
- `settings` - App configuration

## Implementation Phases

**Phase 1:** Foundation (Reflex setup, SQLite models, mobile interface, file uploads)
**Phase 2:** Big screen (Slideshow, real-time queues, music player, QR codes)
**Phase 3:** Music system (Library indexing, Ollama LLM, YouTube fallback)
**Phase 4:** Polish (Memory book generator, admin panel, testing)

Detailed requirements available in `prompts/Phase[1-4].md`

## Key Technical Requirements

- **Performance:** <2 second upload times, zero crashes during 2-day event
- **File Handling:** Photos/videos up to 50MB, auto-resize to 1920x1080
- **Real-time Updates:** WebSocket integration for live slideshow/queue updates
- **Target Users:** Ages 8-80, minimal technical skills, mobile-first design
- **Final Output:** Complete party system + standalone HTML memory book for USB export