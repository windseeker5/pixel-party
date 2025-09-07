Based on the PRD.md PRD document, create the foundational Reflex application for the birthday party memory app with:

1. **Initial Reflex Project Setup:**
   - Set up proper Reflex project structure
   - Install required dependencies (reflex, pillow, sqlite3, yt-dlp, mutagen)
   - Configure Tabler Icons integration
   - Create main app.py entry point

2. **SQLite Database Models:**
   - Create database/models.py with all tables from PRD schema:
     * guests table (name, session_id, first_seen, total_submissions)
     * photos table (guest info, filename, wish_message, uploaded_at, display_duration)
     * music_queue table (song info, artist, album, source, played_at)
     * music_library table (local music indexing)
     * settings table (app configuration)
   - Add database initialization and migration functions

3. **Basic Mobile Interface Structure:**
   - Create mobile guest interface with Reflex components
   - Welcome screen with QR code access
   - Name entry form (required field, stored in session)
   - Photo/video upload component (max 50MB, auto-resize to 1920x1080)
   - Birthday wish text input (180 character limit with counter)
   - Use Tabler Icons throughout (camera-icon, user-icon, heart-icon)

4. **File Upload Handling:**
   - Set up file storage system in static/uploads/ directory
   - Implement image processing with Pillow for auto-resize
   - Create file validation and error handling
   - Store uploads with proper naming convention

5. **Basic Project Structure:**