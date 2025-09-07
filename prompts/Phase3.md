Based on Phases 1-2 and the PRD specifications, implement the advanced features:

1. **Dynamic Text Overlay System:**
   - Implement Instagram/YouTube style text overlays on photos
   - Text overlay positioning: bottom 15% of screen, max 25% height
   - Animated entrance: slide up from bottom with fade-in (0.8s)
   - Display duration: 8 seconds per photo
   - Animated exit: fade out (1s) before next photo
   - Typography: responsive font sizing (clamp(1.2rem, 2.5vw, 2rem))
   - Background: rgba(0,0,0,0.6) with backdrop-filter blur(8px)
   - Include Tabler heart-icon and user-icon in overlay

2. **Animation Libraries Integration:**
   - Integrate AOS (Animate On Scroll) for text animations
   - Add Animate.css for overlay effects
   - Implement Swiper.js for smooth photo transitions
   - Ensure animations work smoothly on Raspberry Pi

3. **Local Music Library System:**
   - Index the 20GB music collection on startup
   - Extract metadata (title, artist, album, duration) using mutagen
   - Create search functionality across all metadata
   - Support MP3, FLAC, M4A, OGG formats
   - Build fast search index for real-time searching

4. **Music Search Implementation:**
   - Create search interface with multiple options:
     * Song name search
     * Artist search  
     * Album search
     * Mood-based search (prepare for LLM integration)
   - Display search results with play preview (30-second clips)
   - Add to queue functionality with immediate feedback

5. **Ollama LLM Integration:**
   - Connect to local Ollama server for mood-based music suggestions
   - Implement mood description → song recommendation pipeline
   - Example: "romantic slow songs" → suggest relevant tracks from library
   - Fallback to text search if LLM unavailable

6. **YouTube Fallback System:**
   - Integrate yt-dlp for audio-only downloads
   - Search YouTube when song not found locally
   - Download audio as 192kbps MP3
   - Auto-save to music library for future use
   - Show download progress to user

7. **Real-time Synchronization:**
   - Sync text overlays with photo display timing
   - Coordinate wish display with photo submitter
   - Real-time updates when new content submitted
   - Smooth transitions between all elements

Implement all advanced features following the "don't reinvent the wheel" principle using proven libraries as specified in the PRD.