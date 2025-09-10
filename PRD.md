# Birthday Party Memory & Music App - PRD

## Project Overview

**Project Name:** PixelParty (Birthday Memory & Music Experience )  
**Target User:** 50th birthday party guests/users (all ages, non-technical)  
**Platform:** Raspberry Pi 4 with big screen display + mobile web interface  
**Framework:** Flask (Python backend) + HTMX (dynamic frontend) + daisyUI (beautiful components)  


## Project Vision

Create an interactive party experience where guests can easily share photos, wishes, and music suggestions through their mobile devices, with real-time display on a big screen, culminating in a beautiful digital memory book as a gift for the birthday celebrant.

---

## User Personas

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

## Core User Stories

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

## Technical Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mobile Web    │    │  Raspberry Pi   │    │   Big Screen    │
│   Interface     │───▶│   Application   │───▶│    Display      │
│  (Guest Input)  │    │ (Flask + HTMX)  │    │ (Real-time UI)  │
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
- **Framework:** Flask (Python backend) + HTMX (dynamic frontend)
- **UI Components:** daisyUI (beautiful components) + Tailwind CSS 
- **Icons:** Heroicons (professional, modern icons)
- **Dark Theme:** Built-in Tailwind CSS dark mode
- **Database:** SQLite with file attachments
- **LLM Integration:** Ollama API calls
- **Music Download:** yt-dlp for YouTube fallback
- **File Handling:** PIL for image processing
- **Deployment:** Raspberry Pi 4 (8GB recommended)

---

## Feature Specifications

### 1. Mobile Guest Interface

#### 1.1 Welcome Screen
- **QR Code Access:** Instant app launch via QR scan
- **Name Entry:** Simple text input (stored for session)
- **Welcome Message:** "Help celebrate [Name]'s 50th Birthday!"

#### 1.2 Photo/Video Upload with Wish Capture
```
┌─────────────────────────┐
│  Share a Memory         │
├─────────────────────────┤
│                         │
│  Your Name:             │
│  [daisyUI input]        │
│        
│  Photo - video          │
│  [daisyUI file-input]   │
│                         │
│  Your Birthday Wish:    │
│  [daisyUI textarea]     │
│  (Max 180 chars)        │
│                         │
│  Music suggestion:      │
│                         │
│  [daisyUI input]        │
│                         │
│  [Search Results...]    │
│                         │
│                         │
│  [daisyUI btn-primary]  │
└─────────────────────────┘
```

**Requirements:**
- **Name Input:** Required field, stored with submission
- **Wish/Note Text:** 180 character limit for optimal display
- **Real-time Preview:** Show character count as user types
- **Text Validation:** Ensure appropriate content
- **Immediate Feedback:** Confirmation after successful upload
- **Single tap photo/video selection**
- **Max file size:** 50MB per upload
- **Auto-resize images:** 1920x1080 max for big screen display
- **Search local library first (20GB collection)
- **LLM mood-based suggestions via Ollama
- **YouTube fallback with yt-dlp audio download
- **Preview functionality (30-second clips)
- **Queue position feedback
- **Thank you confirmation message after a post 

### 2. Big Screen Display

#### 2.1 Main Display Layout with Optimized Text Overlays
```
╔═══════════════════════════════════════════════════════════╗
║      Happy 50th Birthday, [Name]!                        ║
╠═══════════════════════════════════════════════════════════╣
║                                               │           ║
║            Current Photo                      │  Now      ║
║          [FULL FOCUS]                         │  Playing  ║
║                                               │           ║
║                                               │  Photo    ║
║                                               │  Queue    ║
║                                               │           ║
║     ┌─────────────────────┐    ← 25% max     │  Music    ║
║     │ "Happy Birthday!    │      height      │  Queue    ║
║     │ Love you"           │      bottom      │           ║
║     │ - Sarah             │      positioned  │           ║
║     └─────────────────────┘                  │           ║
╠═══════════════════════════════════════════════════════════╣
║    QR Code   |  Music Controls  |  Settings              ║
╚═══════════════════════════════════════════════════════════╝
```

#### 2.2 Text Overlay Best Practices

**Sizing Guidelines (Following Instagram/YouTube Standards):**
- **Maximum Height:** 25% of screen height
- **Width:** 60-80% of photo area (centered)
- **Position:** Bottom third of image
- **Padding:** 40px from screen edges

**Visual Hierarchy:**
1. **Photo:** 75% visual priority (main focus)
2. **Text Overlay:** 20% visual priority (supporting)
3. **UI Elements:** 5% visual priority (functional)

**Text Overlay Styling Best Practices:**
```css
.wish-overlay {
    position: absolute;
    bottom: 15%;                    /* Bottom third positioning */
    left: 15%;
    right: 15%;                     /* 70% width maximum */
    max-height: 25vh;               /* Never more than 25% of screen */
    
    background: rgba(0, 0, 0, 0.6); /* Subtle, not overwhelming */
    backdrop-filter: blur(8px);     /* Modern glass effect */
    border-radius: 15px;
    padding: 20px 25px;             /* Compact padding */
    
    color: white;
    font-size: clamp(1.2rem, 2.5vw, 2rem); /* Responsive sizing */
    text-align: center;
    line-height: 1.3;               /* Tight line spacing */
    
    animation: slideInFromBottom 0.8s ease-out;
}

.wish-text {
    font-weight: 400;               /* Not too bold */
    margin-bottom: 8px;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 3;          /* Max 3 lines */
    -webkit-box-orient: vertical;
}

.submitter-info {
    font-size: 0.8em;               /* Smaller, supporting text */
    color: #FFD700;                 /* Gold accent color */
    font-style: italic;
    opacity: 0.9;
}
```

#### 2.3 Responsive Overlay Behavior

**Screen Size Adaptations:**
- **Large Screens (>1920px):** Text overlay max 20% height
- **Medium Screens (1080-1920px):** Text overlay max 25% height  
- **Small Screens (<1080px):** Text overlay max 30% height

**Text Length Handling:**
- **Short wishes (1-50 chars):** Larger font, centered
- **Medium wishes (51-120 chars):** Standard font, 2 lines max
- **Long wishes (121-180 chars):** Smaller font, 3 lines max, with fade

**Animation Timing:**
- **Slide in:** 0.8 seconds (smooth, not jarring)
- **Display duration:** 8 seconds (readable but not overwhelming)
- **Fade out:** 1 second (gentle exit)
- **Photo transition:** 0.5 seconds after text exits

#### 2.4 Focus Priority Design
```
Photo Priority:     ████████████████████ 75%
Text Overlay:       █████ 20%
UI Elements:        █ 5%
```

**Visual Weight Distribution:**
- **Photo dominates** the visual space
- **Text enhances** but doesn't compete
- **UI stays minimal** and functional

#### 2.5 Queue Displays & Transitions
- **Photo Queue:** Thumbnail grid (next 6 photos) using daisyUI carousel
- **Music Queue:** Song title, artist, submitted by (next 5 songs) using daisyUI list
- **Real-time Updates:** HTMX polling for live updates
- **Smooth Transitions:** CSS transitions between photos with text overlay sync
- **Photo Duration:** 8-12 seconds per image (configurable)

### 3. Music System

#### 3.1 Local Library Integration
- **Indexing:** Scan 20GB music collection on startup
- **Metadata:** Extract title, artist, album, duration using mutagen
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

### 4. Standalone Memory Book Generator

#### 4.1 USB Key Package Structure
```
Birthday_Memory_Book_USB/
├── index.html              # Standalone memory book
├── photos/                 # All uploaded photos/videos
│   ├── photo_001.jpg
│   ├── photo_002.mp4
│   └── ...
├── music/                  # All suggested music
│   ├── song_001.mp3
│   ├── song_002.mp3
│   └── ...
├── styles/
│   └── memory_book.css     # Embedded styling
├── scripts/
│   └── memory_book.js      # Embedded JavaScript
└── party_database.db       # SQLite backup (optional)
```

#### 4.2 Standalone HTML Layout Design
```
┌─────────────────────────────────────┐
│  [Polaroid-style photo]             │
│     [Click to view full size]       │
│                                     │
│     Submitted by: John Smith        │
│     March 15, 2024 - 3:42 PM       │
│                                     │
│  "Happy 50th! You're amazing       │
│     and we love celebrating with   │
│     you!"                           │
│                                     │
│  [play-icon] "Happy" by Pharrell Williams │
│     [Inline audio player]          │
└─────────────────────────────────────┘
```

#### 4.3 Technical Implementation
- **Self-Contained:** No server required, works offline
- **Cross-Platform:** Opens in any modern browser
- **Interactive:** Click photos for full view, play music inline
- **Responsive:** Works on mobile, tablet, desktop
- **Portable:** Complete package on USB key

#### 4.4 HTML Features
```html
<!-- Example memory card structure -->
<div class="memory-card polaroid">
    <div class="photo-container">
        <img src="photos/photo_001.jpg" alt="Birthday Memory" 
             onclick="showFullImage(this)">
        <div class="photo-overlay">Click to enlarge</div>
    </div>
    
    <div class="memory-details">
        <div class="submitted-by">John Smith</div>
        <div class="timestamp">March 15, 2024 - 3:42 PM</div>
        
        <div class="wish-message">
            "Happy 50th! You're amazing and we love celebrating with you!"
        </div>
        
        <div class="music-suggestion">
            Music Suggestion:
            <div class="audio-player">
                <audio controls preload="none">
                    <source src="music/happy_pharrell.mp3" type="audio/mpeg">
                </audio>
                <span class="song-info">"Happy" by Pharrell Williams</span>
            </div>
        </div>
    </div>
</div>
```

#### 4.5 Export Process
1. **Generate HTML:** Template-based generation with all memories
2. **Copy Media:** Organize photos/music in folders
3. **Embed Assets:** CSS/JS embedded for offline use
4. **Package USB:** Ready-to-gift complete package
5. **Test Locally:** Verify everything works without internet

---

## Technical Implementation Strategy

### Development Philosophy: Leverage Existing Libraries

**Core Principle:** Don't reinvent the wheel. Use proven, lightweight, well-maintained libraries for maximum efficiency and reliability.

### Recommended Library Stack

#### **Frontend Components & Styling**
```html
<!-- daisyUI Components (Beautiful by Default) -->
- daisyUI: Complete component library (buttons, forms, cards, etc.)
- Tailwind CSS: Utility-first CSS framework with built-in dark mode
- Heroicons: Professional icon set
- HTMX: Dynamic interactions without JavaScript frameworks

<!-- Simple Animations -->
- CSS Transitions: Built into Tailwind
- CSS Keyframes: For text overlay animations
- No external animation libraries needed
```

#### **Backend Libraries**
```python
# Flask Extensions
- Flask: Web framework
- Pillow: Image processing and thumbnails
- yt-dlp: YouTube audio download
- mutagen: Music metadata extraction
- sqlite3: Built-in database

# LLM Integration  
- ollama: Local LLM server
- requests: API calls
- json: Data handling
```

#### **Specific Implementation Examples**

**Flask + HTMX Text Overlay:**
```html
<!-- HTMX handles real-time updates -->
<div hx-get="/current-photo" hx-trigger="every 10s" hx-target="#photo-display">
    <img src="{{ current_photo }}" class="w-full h-screen object-cover">
    
    <!-- Text overlay with Tailwind styling -->
    <div class="absolute bottom-16 left-16 right-16 bg-black bg-opacity-60 
                backdrop-blur-sm rounded-2xl p-6 text-white text-center
                animate-slide-up">
        <p class="text-2xl mb-2">"{{ wish_message }}"</p>
        <p class="text-yellow-400 italic">- {{ guest_name }}, {{ timestamp }}</p>
    </div>
</div>
```

**daisyUI Mobile Interface:**
```html
<!-- Beautiful form with daisyUI components -->
<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <h2 class="card-title">Share a Memory</h2>
        
        <div class="form-control">
            <label class="label">
                <span class="label-text">Your Name</span>
            </label>
            <input type="text" class="input input-bordered" required>
        </div>
        
        <div class="form-control">
            <label class="label">
                <span class="label-text">Upload Photo</span>
            </label>
            <input type="file" class="file-input file-input-bordered w-full">
        </div>
        
        <div class="form-control">
            <label class="label">
                <span class="label-text">Birthday Wish</span>
            </label>
            <textarea class="textarea textarea-bordered" 
                      placeholder="Write your special message..." 
                      maxlength="180"></textarea>
        </div>
        
        <div class="card-actions justify-end">
            <button class="btn btn-primary" 
                    hx-post="/upload" 
                    hx-include="form">
                Submit Memory
            </button>
        </div>
    </div>
</div>
```

### Library Selection Criteria

1. **Size:** Minimal footprint for Raspberry Pi performance
2. **Maintenance:** Active development and community
3. **Documentation:** Well-documented with examples
4. **Browser Support:** Works across all modern browsers
5. **Performance:** Optimized for smooth interactions
6. **License:** MIT/Apache for commercial use

### Avoided Reinventions

❌ **Don't Build:** Custom UI components  
✅ **Use:** daisyUI components

❌ **Don't Build:** Complex JavaScript frameworks  
✅ **Use:** HTMX for dynamic interactions

❌ **Don't Build:** Custom styling system  
✅ **Use:** Tailwind CSS + daisyUI

❌ **Don't Build:** Image processing  
✅ **Use:** Pillow (Python)

❌ **Don't Build:** YouTube downloader  
✅ **Use:** yt-dlp

❌ **Don't Build:** Icon system  
✅ **Use:** Heroicons

### Performance Optimization

**Bundle Strategy:**
- **Minimal CSS:** Tailwind + daisyUI only
- **No JavaScript frameworks:** HTMX handles all interactions
- **Lazy Loading:** HTMX lazy loading for images
- **CDN Fallbacks:** Local copies for offline USB memory book

### Recommended Framework: Flask + HTMX + daisyUI

Perfect combination because:
- **Flask:** Proven, reliable, you already know it
- **HTMX:** Handles real-time updates without JavaScript complexity
- **daisyUI:** Beautiful components out of the box, no custom styling needed
- **Tailwind:** Built-in dark mode, responsive design
- **Raspberry Pi Performance:** Lightweight stack ensures smooth operation
- **No Bugs:** All mature, battle-tested technologies

---

## Database Schema

### Tables Structure

```sql
-- Users/Guests
CREATE TABLE guests (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,              -- First name or full name
    session_id TEXT UNIQUE,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_submissions INTEGER DEFAULT 0
);

-- Photo submissions with wishes
CREATE TABLE photos (
    id INTEGER PRIMARY KEY,
    guest_id INTEGER,
    guest_name TEXT NOT NULL,        -- Stored for easy access
    filename TEXT NOT NULL,
    original_filename TEXT,
    wish_message TEXT NOT NULL,      -- Birthday wish/note (max 180 chars)
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    displayed_at TIMESTAMP,
    display_duration INTEGER DEFAULT 10, -- Seconds to show on screen
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

## UI/UX Requirements

### Design Principles
1. **Simplicity First:** Large buttons, clear typography
2. **Accessibility:** High contrast, readable fonts
3. **Mobile Optimized:** Touch-friendly interface
4. **Real-time Feedback:** Immediate visual confirmation
5. **Celebratory Theme:** Warm colors, birthday aesthetics
6. **Professional Icons:** Heroicons for clean, modern appearance

### Color Palette
- **Primary:** Gold (#FFD700) - Celebration theme
- **Secondary:** Deep Pink (#FF1493) - Birthday vibes
- **Accent:** White (#FFFFFF) - Clean contrast
- **Background:** Light gradient (#FFF8DC to #F0E68C)

### Typography
- **Headers:** Large, bold, celebratory fonts
- **Body:** Clean, readable sans-serif
- **Special:** Script font for wishes display

### Component System
- **Source:** daisyUI (professional, beautiful components)
- **Icons:** Heroicons (clean, modern icons)
- **Dark Mode:** Built-in Tailwind CSS dark mode
- **Responsive:** Tailwind responsive breakpoints

### Responsive Breakpoints
- **Mobile:** 320px - 768px (primary focus)
- **Tablet:** 768px - 1024px
- **Desktop/Big Screen:** 1920x1080+

---

## Admin Interface

### Export Options
```
┌─────────────────────────────────────┐
│  Party Control Center               │
├─────────────────────────────────────┤
│                                     │
│  Event Settings:                    │
│  • Birthday Person: [input]         │
│  • Party Title: [input]             │
│  • Slideshow Duration: [select]     │
│                                     │
│  Content Moderation:                │
│  • [Pending Photos: 3]             │
│  • [Pending Music: 1]              │
│                                     │
│  Memory Book Export:                │
│  • [Generate USB Memory Book]      │
│  • [Preview HTML Page]             │
│  • [Download Media Archive]        │
│  • [Export Database Backup]        │
│                                     │
│  System Status:                     │
│  • Storage: 85% (17GB/20GB)        │
│  • Active Guests: 12               │
│  • Queue Status: Playing           │
└─────────────────────────────────────┘
```

---

## Development Timeline

### Phase 1: Core Flask + HTMX Framework (Week 1)
- [ ] Set up Flask application structure
- [ ] Create SQLite database and models
- [ ] Implement mobile interface with daisyUI components
- [ ] Set up file upload handling with HTMX

### Phase 2: Display System (Week 2)
- [ ] Big screen slideshow functionality using Flask routes
- [ ] Real-time queue displays with HTMX polling
- [ ] Music player integration
- [ ] QR code generation

### Phase 3: Dynamic Text Effects & Music Integration (Week 3)
- [ ] Implement CSS text overlays with Tailwind animations
- [ ] Create Instagram/YouTube style wish animations
- [ ] Local music library indexing with metadata
- [ ] Search functionality implementation
- [ ] Ollama LLM integration for mood-based suggestions
- [ ] YouTube fallback system with yt-dlp
- [ ] Real-time text overlay synchronization with HTMX

### Phase 4: Polish & Memory Book (Week 4)
- [ ] UI/UX refinements with daisyUI components
- [ ] Memory book generator
- [ ] Admin panel completion
- [ ] Testing and optimization

---

## Security & Privacy

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

## Success Metrics

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

## Risk Assessment

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

## File Structure
```
birthday_app/
├── app.py                 # Main Flask application
├── database/
│   ├── models.py         # SQLite models
│   └── migrations.py     # Database setup
├── static/
│   ├── uploads/          # Photo/video storage
│   ├── music/            # Music library
│   └── css/              # Tailwind + daisyUI
├── templates/
│   ├── mobile_interface.html
│   ├── big_screen.html
│   └── base.html
├── routes/
│   ├── mobile.py
│   ├── big_screen.py
│   └── api.py
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
    
    # Save complete HTML file (CSS embedded)
    with open(f"{export_path}/index.html", "w") as f:
        f.write(html_content)
    
    # Copy database backup
    shutil.copy("party.db", f"{export_path}/party_database.db")
    
    return f"USB Memory Book generated at: {export_path}"

def generate_html_template(memories):
    """Generate self-contained HTML with embedded Tailwind + daisyUI"""
    
    html = """
    <!DOCTYPE html>
    <html lang="en" data-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>50th Birthday Memory Book</title>
        
        <!-- Embedded Tailwind + daisyUI (offline) -->
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdn.jsdelivr.net/npm/daisyui@4.4.24/dist/full.min.css" rel="stylesheet">
        
        <style>
            .polaroid { 
                transform: rotate(-2deg);
                transition: transform 0.3s ease;
            }
            .polaroid:nth-child(even) { transform: rotate(2deg); }
            .polaroid:hover { transform: rotate(0deg) scale(1.05); }
        </style>
    </head>
    <body class="bg-gradient-to-br from-pink-50 to-purple-50 dark:from-gray-900 dark:to-purple-900">
        <div class="container mx-auto px-4 py-8">
            <div class="text-center mb-12">
                <h1 class="text-5xl font-bold text-pink-600 dark:text-pink-400 mb-4">
                    Happy 50th Birthday!
                </h1>
                <p class="text-xl text-gray-600 dark:text-gray-300">
                    A Collection of Beautiful Memories
                </p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
    """
    
    # Add each memory as HTML using daisyUI components
    for memory in memories:
        html += f"""
        <div class="card bg-base-100 shadow-xl polaroid">
            <figure class="px-4 pt-4">
                <img src="photos/{memory['photo_filename']}" 
                     alt="Birthday Memory" 
                     class="rounded-xl cursor-pointer hover:scale-105 transition-transform"
                     onclick="showFullImage(this)">
            </figure>
            <div class="card-body">
                <div class="chat chat-start">
                    <div class="chat-bubble chat-bubble-primary">
                        "{memory['wish_message']}"
                    </div>
                </div>
                
                <div class="card-actions justify-between items-center mt-4">
                    <div class="text-sm text-gray-500">
                        <div class="font-semibold">{memory['guest_name']}</div>
                        <div>{memory['formatted_timestamp']}</div>
                    </div>
                    
                    <div class="dropdown dropdown-end">
                        <label tabindex="0" class="btn btn-ghost btn-sm">
                            Music
                        </label>
                        <div class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-80">
                            <audio controls class="w-full mb-2">
                                <source src="music/{memory['music_filename']}" type="audio/mpeg">
                            </audio>
                            <p class="text-sm">"{memory['song_title']}" by {memory['artist']}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    html += """
            </div>
        </div>
        
        <!-- Image Modal -->
        <input type="checkbox" id="image-modal" class="modal-toggle" />
        <div class="modal">
            <div class="modal-box max-w-4xl">
                <img id="modal-image" src="" alt="Full Size" class="w-full rounded-lg">
                <div class="modal-action">
                    <label for="image-modal" class="btn">Close</label>
                </div>
            </div>
        </div>
        
        <script>
            function showFullImage(img) {
                document.getElementById('modal-image').src = img.src;
                document.getElementById('image-modal').checked = true;
            }
        </script>
    </body>
    </html>
    """
    
    return html
```

---

## Final Deliverable

### The USB Memory Book Gift

**Primary Deliverable:** A beautiful USB key containing a complete, standalone memory book that works on any device:

#### USB Contents:
- **`index.html`** - Interactive memory book (no server needed)
- **`photos/`** - All party photos and videos
- **`music/`** - All suggested songs
- **`party_database.db`** - Complete backup for future reference

#### Gift Experience:
1. **Immediate Access:** Plug USB into any computer/smart TV
2. **Open index.html:** Beautiful memory book opens in any browser
3. **Interactive Browsing:** Click photos to enlarge, play music inline
4. **Permanent Keepsake:** Works forever, no apps or servers needed
5. **Shareable:** Easy to copy and share with family

**The ultimate goal:** Transform a birthday party into an interactive, memorable experience where technology enhances human connection, culminating in a permanent, beautiful digital keepsake that the birthday celebrant can enjoy anywhere, anytime, on any device - a true gift that keeps giving.

**Technical Achievement:** A completely self-contained memory book that captures every moment, wish, and song from the celebration in a format that will work decades from now.

---

*This PRD serves as the blueprint for creating a magical birthday celebration experience using Flask + HTMX + daisyUI stack. Each feature is designed with love, technical feasibility, and user joy in mind.*