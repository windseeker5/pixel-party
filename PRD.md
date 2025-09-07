# 🎉 Birthday Party Memory & Music App - PRD

## Project Overview

**Project Name:** Birthday Memory & Music Experience  
**Duration:** 2-day birthday celebration  
**Target User:** 50th birthday party guests (all ages, non-technical)  
**Platform:** Raspberry Pi 4 with big screen display + mobile web interface  
**Timeline:** [Insert your deadline here]

## 🎯 Project Vision

Create an interactive party experience where guests can easily share photos, wishes, and music suggestions through their mobile devices, with real-time display on a big screen, culminating in a beautiful digital memory book as a gift for the birthday celebrant.

---

## 👥 User Personas

### Primary Users (Party Guests)
- **Age Range:** 8-80 years old
- **Technical Skill:** Minimal to none
- **Device:** Personal mobile phones
- **Goals:** Share memories, wishes, and music easily
- **Pain Points:** Complex interfaces, long forms, technical barriers

### Secondary User (Party Host - You)
- **Role:** Administrator
- **Goals:** Smooth party experience, beautiful memory book creation
- **Needs:** Real-time monitoring, content moderation, system control

### Tertiary User (Birthday Celebrant)
- **Role:** Memory book recipient
- **Goals:** Receive meaningful digital keepsake
- **Needs:** Beautiful, organized memories from the celebration

---

## 🔑 Core User Stories

### Guest Mobile Experience
1. **As a guest**, I want to scan a QR code to instantly access the app
2. **As a guest**, I want to enter my name once and have it remembered
3. **As a guest**, I want to upload a photo/video with a simple tap
4. **As a guest**, I want to write a birthday wish in a text box
5. **As a guest**, I want to search for music by mood, song name, or artist
6. **As a guest**, I want to see my submissions added to the queue
7. **As a guest**, I want the interface to work perfectly on my phone

### Big Screen Display Experience
8. **As a party attendee**, I want to see a beautiful slideshow of photos
9. **As a party attendee**, I want to see what music is playing and what's coming next
10. **As a party attendee**, I want to see who submitted each photo/song
11. **As a party attendee**, I want to read birthday wishes as they appear

### Host Administration
12. **As the host**, I want to control slideshow timing and settings
13. **As the host**, I want to moderate content before it goes live
14. **As the host**, I want to generate a memory book at the end
15. **As the host**, I want to export all media files easily

---

## 🏗 Technical Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mobile Web    │    │  Raspberry Pi   │    │   Big Screen    │
│   Interface     │───▶│   Application   │───▶│    Display      │
│  (Guest Input)  │    │ (NiceGUI-based) │    │ (Real-time UI)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ SQLite Database │
                    │   + File Store  │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Ollama LLM     │
                    │ Music Suggest.  │
                    └─────────────────┘
```

### Tech Stack Recommendation
- **Framework:** NiceGUI (Python) - Perfect for your requirements
- **Database:** SQLite with file attachments
- **LLM Integration:** Ollama API calls
- **Music Download:** yt-dlp for YouTube fallback
- **File Handling:** PIL for image processing
- **Deployment:** Raspberry Pi 4 (8GB recommended)

---

## 📱 Feature Specifications

### 1. Mobile Guest Interface

#### 1.1 Welcome Screen
- **QR Code Access:** Instant app launch via QR scan
- **Name Entry:** Simple text input (stored for session)
- **Welcome Message:** "Help celebrate [Name]'s 50th Birthday!"

#### 1.2 Photo/Video Upload
```
┌─────────────────────────┐
│  📸 Share a Memory      │
├─────────────────────────┤
│                         │
│  [Upload Photo/Video]   │
│                         │
│  💝 Your Birthday Wish: │
│  ┌─────────────────────┐ │
│  │                     │ │
│  │                     │ │
│  └─────────────────────┘ │
│                         │
│     [Submit Memory]     │
└─────────────────────────┘
```

**Requirements:**
- Single tap photo/video selection
- Max file size: 50MB per upload
- Auto-resize images to 1920x1080 max
- Character limit for wishes: 280 characters
- Immediate upload with progress indicator

#### 1.3 Music Suggestion
```
┌─────────────────────────┐
│  🎵 Suggest Music       │
├─────────────────────────┤
│                         │
│  Search by:             │
│  • Mood (LLM powered)   │
│  • Song name            │
│  • Artist               │
│  • Album                │
│                         │
│  ┌─────────────────────┐ │
│  │ Search...           │ │
│  └─────────────────────┘ │
│                         │
│  [Search Results...]    │
│                         │
│     [Add to Queue]      │
└─────────────────────────┘
```

**Requirements:**
- Search local library first (20GB collection)
- LLM mood-based suggestions via Ollama
- YouTube fallback with yt-dlp audio download
- Preview functionality (30-second clips)
- Queue position feedback

### 2. Big Screen Display

#### 2.1 Main Display Layout
```
╔═══════════════════════════════════════════════════════════╗
║                🎉 Happy 50th Birthday, [Name]! 🎉        ║
╠═══════════════════════════════════════════════════════════╣
║                                               │           ║
║                                               │  🎵 Now   ║
║            Current Photo                      │  Playing  ║
║            [Slideshow]                        │           ║
║                                               │  📸 Photo ║
║                                               │  Queue    ║
║                                               │           ║
║                                               │  🎶 Music ║
║    Submitted by: [Name]                       │  Queue    ║
║    Wish: "Happy Birthday..."                  │           ║
╠═══════════════════════════════════════════════════════════╣
║           [QR Code]  |  Music Controls  |  [Settings]     ║
╚═══════════════════════════════════════════════════════════╝
```

#### 2.2 Queue Displays
- **Photo Queue:** Thumbnail grid (next 6 photos)
- **Music Queue:** Song title, artist, submitted by (next 5 songs)
- **Real-time Updates:** WebSocket-based live updates
- **Transitions:** Smooth fade/slide animations

### 3. Music System

#### 3.1 Local Library Integration
- **Indexing:** Scan 20GB music collection on startup
- **Metadata:** Extract title, artist, album, duration
- **Search:** Full-text search across all metadata
- **Format Support:** MP3, FLAC, M4A, OGG

#### 3.2 LLM-Powered Suggestions
```python
# Example Ollama integration
def get_mood_suggestions(mood_description):
    """
    User input: "romantic slow songs"
    LLM output: ["The Way You Look Tonight", "At Last", "Wonderful Tonight"]
    """
    prompt = f"Suggest 5 songs for the mood: {mood_description}"
    # Return relevant songs from local library
```

#### 3.3 YouTube Fallback
- **Search:** YouTube API or scraping
- **Download:** yt-dlp audio extraction
- **Quality:** 192kbps MP3
- **Storage:** Auto-save to music library
- **Legal:** Fair use for private party

### 4. Memory Book Generator

#### 4.1 Layout Design
```
┌─────────────────────────────────────┐
│  📸 [Polaroid-style photo]          │
│                                     │
│     Submitted by: John Smith        │
│     Date: March 15, 2024 - 3:42 PM │
│                                     │
│  💝 "Happy 50th! You're amazing     │
│     and we love celebrating with   │
│     you!"                           │
│                                     │
│  🎵 Suggested: "Happy" by Pharrell  │
└─────────────────────────────────────┘
```

#### 4.2 Export Options
- **PDF Generation:** High-quality printable format
- **Web Gallery:** Interactive HTML page
- **Media Archive:** ZIP file with all photos/videos/music
- **Print Ready:** 300 DPI for physical printing

---

## 🗄 Database Schema

### Tables Structure

```sql
-- Users/Guests
CREATE TABLE guests (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    session_id TEXT UNIQUE,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Photo submissions
CREATE TABLE photos (
    id INTEGER PRIMARY KEY,
    guest_id INTEGER,
    filename TEXT NOT NULL,
    original_filename TEXT,
    wish_message TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    displayed_at TIMESTAMP,
    file_size INTEGER,
    FOREIGN KEY (guest_id) REFERENCES guests(id)
);

-- Music submissions
CREATE TABLE music_queue (
    id INTEGER PRIMARY KEY,
    guest_id INTEGER,
    song_title TEXT,
    artist TEXT,
    album TEXT,
    filename TEXT,
    source TEXT, -- 'local' or 'youtube'
    played_at TIMESTAMP,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guest_id) REFERENCES guests(id)
);

-- Local music library
CREATE TABLE music_library (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    title TEXT,
    artist TEXT,
    album TEXT,
    duration INTEGER, -- seconds
    file_size INTEGER,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- App settings
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎨 UI/UX Requirements

### Design Principles
1. **Simplicity First:** Large buttons, clear typography
2. **Accessibility:** High contrast, readable fonts
3. **Mobile Optimized:** Touch-friendly interface
4. **Real-time Feedback:** Immediate visual confirmation
5. **Celebratory Theme:** Warm colors, birthday aesthetics

### Color Palette
- **Primary:** Gold (#FFD700) - Celebration theme
- **Secondary:** Deep Pink (#FF1493) - Birthday vibes
- **Accent:** White (#FFFFFF) - Clean contrast
- **Background:** Light gradient (#FFF8DC to #F0E68C)

### Typography
- **Headers:** Large, bold, celebratory fonts
- **Body:** Clean, readable sans-serif
- **Special:** Script font for wishes display

### Responsive Breakpoints
- **Mobile:** 320px - 768px (primary focus)
- **Tablet:** 768px - 1024px
- **Desktop/Big Screen:** 1920x1080+

---

## ⚙️ Admin Interface

### Settings Panel
```
┌─────────────────────────────────────┐
│  🎛 Party Control Center            │
├─────────────────────────────────────┤
│                                     │
│  Event Settings:                    │
│  • Birthday Person: [Input]         │
│  • Party Title: [Input]             │
│  • Slideshow Duration: [5s] ⏱      │
│                                     │
│  Content Moderation:                │
│  • [Pending Photos: 3]             │
│  • [Pending Music: 1]              │
│                                     │
│  Export Options:                    │
│  • [Generate Memory Book]          │
│  • [Download All Media]            │
│  • [Export Database]               │
│                                     │
│  System Status:                     │
│  • Storage: 85% (17GB/20GB)        │
│  • Active Guests: 12               │
│  • Queue Status: Playing           │
└─────────────────────────────────────┘
```

---

## 🚀 Development Timeline

### Phase 1: Core Framework (Week 1)
- [ ] Set up NiceGUI application structure
- [ ] Create SQLite database and models
- [ ] Implement basic mobile interface
- [ ] Set up file upload handling

### Phase 2: Display System (Week 2)
- [ ] Big screen slideshow functionality
- [ ] Real-time queue displays
- [ ] Music player integration
- [ ] QR code generation

### Phase 3: Music Integration (Week 3)
- [ ] Local music library indexing
- [ ] Search functionality implementation
- [ ] Ollama LLM integration
- [ ] YouTube fallback system

### Phase 4: Polish & Memory Book (Week 4)
- [ ] UI/UX refinements
- [ ] Memory book generator
- [ ] Admin panel completion
- [ ] Testing and optimization

---

## 🔒 Security & Privacy

### Data Protection
- **Local Storage:** All data remains on Raspberry Pi
- **No Cloud:** No external data transmission
- **Guest Privacy:** Optional anonymous submissions
- **Content Moderation:** Host approval system

### Access Control
- **Guest Access:** QR code only (no permanent links)
- **Admin Access:** Password-protected settings
- **Network Security:** Local WiFi only

---

## 📊 Success Metrics

### Party Experience
- **Engagement:** 80%+ of guests submit content
- **Technical:** Zero crashes during 2-day event
- **Performance:** <2 second upload times
- **Satisfaction:** Positive feedback from celebrant

### Memory Book
- **Completeness:** All submissions included
- **Quality:** Print-ready output
- **Emotional Impact:** Meaningful keepsake created

---

## ⚠️ Risk Assessment

### Technical Risks
| Risk | Impact | Likelihood | Mitigation |
|------|---------|------------|------------|
| Raspberry Pi overheating | High | Medium | Cooling fan, performance monitoring |
| Storage exhaustion | High | Low | Storage alerts, file compression |
| WiFi congestion | Medium | Medium | Dedicated network, bandwidth limits |
| Music download failures | Low | Medium | Graceful fallbacks, error handling |

### User Experience Risks
| Risk | Impact | Likelihood | Mitigation |
|------|---------|------------|------------|
| Complex interface | High | Low | User testing, simplified design |
| Mobile compatibility | Medium | Low | Cross-device testing |
| Content moderation needs | Medium | Medium | Pre-approval system |

---

## 🛠 Technical Implementation Notes

### Recommended Framework: NiceGUI
Perfect for this project because:
- **Rapid Development:** Python-only, no JavaScript needed
- **Real-time Updates:** Built-in WebSocket support
- **File Handling:** Easy upload/download management
- **Custom Styling:** Full CSS control for beautiful UI
- **Raspberry Pi Performance:** FastAPI backend optimized

### File Structure
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
│   └── memory_book_template.html  # Standalone HTML template
├── services/
│   ├── music_service.py  # Music search/download
│   ├── ollama_service.py # LLM integration
│   └── usb_export_service.py # USB Memory Book generator
├── export/               # Generated USB content
│   ├── index.html        # Final memory book
│   ├── photos/           # Copied photos
│   ├── music/            # Copied music
│   └── party_database.db # Database backup
└── config.py             # App configuration
```

### USB Memory Book Generation Code Example
```python
# usb_export_service.py
import sqlite3
import shutil
import os
from pathlib import Path

def generate_usb_memory_book(export_path="/media/usb/birthday_memory"):
    """Generate standalone HTML memory book for USB"""
    
    # Create export directory structure
    os.makedirs(f"{export_path}/photos", exist_ok=True)
    os.makedirs(f"{export_path}/music", exist_ok=True)
    
    # Query all memories from database
    memories = get_all_memories_from_db()
    
    # Copy all media files
    copy_media_files(memories, export_path)
    
    # Generate standalone HTML
    html_content = generate_html_template(memories)
    
    # Save complete HTML file (CSS/JS embedded)
    with open(f"{export_path}/index.html", "w") as f:
        f.write(html_content)
    
    # Copy database backup
    shutil.copy("party.db", f"{export_path}/party_database.db")
    
    return f"USB Memory Book generated at: {export_path}"

def generate_html_template(memories):
    """Generate self-contained HTML with embedded CSS/JS"""
    
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>50th Birthday Memory Book</title>
        <style>
            /* Embedded CSS - works offline */
            body { font-family: 'Arial', sans-serif; background: linear-gradient(135deg, #fdf2f8, #fce7f3); }
            .polaroid { background: white; padding: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
            .memory-card { margin: 20px auto; max-width: 400px; }
            .audio-player { margin: 10px 0; }
            /* ... more embedded styles ... */
        </style>
        <script>
            /* Embedded JavaScript - works offline */
            function showFullImage(img) {
                // Image enlargement functionality
            }
            function playMusic(audioElement) {
                // Music player functionality
            }
        </script>
    </head>
    <body>
        <h1>🎉 Happy 50th Birthday Memory Book 🎉</h1>
    """
    
    # Add each memory as HTML
    for memory in memories:
        html += f"""
        <div class="memory-card polaroid">
            <img src="photos/{memory['photo_filename']}" onclick="showFullImage(this)">
            <p><strong>{memory['guest_name']}</strong> - {memory['timestamp']}</p>
            <p>"{memory['wish_message']}"</p>
            <audio controls>
                <source src="music/{memory['music_filename']}" type="audio/mpeg">
            </audio>
            <p>🎵 {memory['song_title']} by {memory['artist']}</p>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    
    return html
```

---

## 🎁 Final Deliverable

A complete party experience system that creates lasting memories while providing seamless real-time interaction for all guests, culminating in a beautiful digital memory book that the birthday celebrant will treasure forever.

**The ultimate goal:** Transform a birthday party into an interactive, memorable experience where technology enhances human connection rather than replacing it.

---

*This PRD serves as the blueprint for creating a magical birthday celebration experience. Each feature is designed with love, technical feasibility, and user joy in mind.*