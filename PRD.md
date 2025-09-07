# Birthday Party Memory & Music App - PRD

## Project Overview

**Project Name:** Birthday Memory & Music Experience  
**Duration:** 2-day birthday celebration  
**Target User:** 50th birthday party guests (all ages, non-technical)  
**Platform:** Raspberry Pi 4 with big screen display + mobile web interface  
**Framework:** Reflex (Pure Python with React frontend)  
**Timeline:** [Insert your deadline here]

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
│  (Guest Input)  │    │ (Reflex-based)  │    │ (Real-time UI)  │
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
- **Framework:** Reflex (Pure Python with React frontend)
- **Database:** SQLite with file attachments
- **Icons:** Tabler Icons (professional, clean, modern)
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
│  [camera-icon] Share a Memory      │
├─────────────────────────┤
│                         │
│  [user-icon] Your Name:          │
│  ┌─────────────────────┐ │
│  │ Enter your name...  │ │
│  └─────────────────────┘ │
│                         │
│  [Upload Photo/Video]   │
│                         │
│  [heart-icon] Your Birthday Wish: │
│  ┌─────────────────────┐ │
│  │ Write your special  │ │
│  │ message here...     │ │
│  │ (Max 180 chars)     │ │
│  └─────────────────────┘ │
│                         │
│     [Submit Memory]     │
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

#### 1.3 Music Suggestion
```
┌─────────────────────────┐
│  [music-icon] Suggest Music       │
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

#### 2.1 Main Display Layout with Optimized Text Overlays
```
╔═══════════════════════════════════════════════════════════╗
║      [calendar-icon] Happy 50th Birthday, [Name]!        ║
╠═══════════════════════════════════════════════════════════╣
║                                               │           ║
║            Current Photo                      │  [music]  ║
║          [FULL FOCUS]                         │  Now      ║
║                                               │  Playing  ║
║                                               │           ║
║                                               │  [photo]  ║
║                                               │  Photo    ║
║                                               │  Queue    ║
║     ┌─────────────────────┐    ← 25% max     │           ║
║     │ [heart] "Happy      │      height      │  [music]  ║
║     │ Birthday! Love you" │      bottom      │  Music    ║
║     │ - Sarah             │      positioned  │  Queue    ║
║     └─────────────────────┘                  │           ║
╠═══════════════════════════════════════════════════════════╣
║    [qr-code] QR  |  Music Controls  |  [settings-icon]   ║
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
- **Photo Queue:** Thumbnail grid (next 6 photos)
- **Music Queue:** Song title, artist, submitted by (next 5 songs)  
- **Real-time Updates:** WebSocket-based live updates
- **Smooth Transitions:** Cross-fade between photos with text overlay sync
- **Photo Duration:** 8-12 seconds per image (configurable)

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
│  [photo-icon] [Polaroid-style photo]          │
│     [Click to view full size]       │
│                                     │
│     [user-icon] Submitted by: John Smith     │
│     [calendar-icon] March 15, 2024 - 3:42 PM    │
│                                     │
│  [heart-icon] "Happy 50th! You're amazing     │
│     and we love celebrating with   │
│     you!"                           │
│                                     │
│  [music-icon] [play-icon] "Happy" by Pharrell Williams │
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
        <div class="submitted-by">[user-icon] John Smith</div>
        <div class="timestamp">[calendar-icon] March 15, 2024 - 3:42 PM</div>
        
        <div class="wish-message">
            "Happy 50th! You're amazing and we love celebrating with you!"
        </div>
        
        <div class="music-suggestion">
            [music-icon] Music Suggestion:
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

#### **Frontend Animation & Effects**
```javascript
// Dynamic Text Overlays (Instagram/YouTube style)
- AOS (Animate On Scroll): 2.3KB - Smooth animations
- Animate.css: 4KB - CSS animation library  
- Typed.js: 8KB - Typewriter effects
- Particles.js: 15KB - Background effects (optional)

// Photo Slideshow
- Swiper.js: 38KB - Touch-enabled slider
- Lightbox2: 12KB - Photo enlargement
- Intersection Observer API: Native - Smooth transitions

// Icons
- Tabler Icons: Professional, clean, modern icon set
- React Icons: Easy integration with Reflex

// Audio/Music
- Howler.js: 25KB - Web audio library
- WaveSurfer.js: 89KB - Audio waveform visualization (optional)
```

#### **Backend Libraries**
```python
# Reflex Extensions
- Pillow: Image processing and thumbnails
- yt-dlp: YouTube audio download
- mutagen: Music metadata extraction
- sqlite3: Built-in database
- asyncio: Real-time updates

# LLM Integration  
- ollama: Local LLM server
- requests: API calls
- json: Data handling
```

#### **Specific Implementation Examples**

**Reflex Text Overlay Effects:**
```python
import reflex as rx
from reflex_tabler_icons import TablerIcon

def wish_overlay(wish_text: str, submitter: str, timestamp: str):
    return rx.box(
        rx.hstack(
            TablerIcon("heart-filled", color="gold", size=24),
            rx.text(wish_text, font_size="1.5rem", color="white"),
            spacing="2"
        ),
        rx.hstack(
            TablerIcon("user", color="gold", size=16),
            rx.text(f"{submitter}, {timestamp}", 
                    font_size="0.9rem", color="gold", font_style="italic"),
            spacing="1"
        ),
        position="absolute",
        bottom="15%",
        left="15%",
        right="15%",
        background="rgba(0,0,0,0.6)",
        backdrop_filter="blur(8px)",
        border_radius="15px",
        padding="20px",
        animation="slideInFromBottom 0.8s ease-out"
    )
```

**Photo Slideshow with Reflex:**
```python
def photo_slideshow(current_photo: str, wish_data: dict):
    return rx.box(
        rx.image(
            src=current_photo,
            width="100%",
            height="100vh",
            object_fit="cover"
        ),
        wish_overlay(
            wish_data["message"],
            wish_data["name"], 
            wish_data["time"]
        ),
        position="relative"
    )
```

#### **Real-Time Big Screen Display System**

**Live Photo Slideshow with Dynamic Text:**
```python
# Reflex implementation for big screen
import reflex as rx
from typing import List, Dict

class SlideshowState(rx.State):
    current_photos: List[Dict] = []
    current_index: int = 0
    current_wish: Dict = {}
    
    def load_photos(self):
        """Load photos from database"""
        # Implementation to load photos
        pass
    
    def next_photo(self):
        """Advance to next photo with wish overlay"""
        if self.current_photos:
            self.current_index = (self.current_index + 1) % len(self.current_photos)
            self.current_wish = self.current_photos[self.current_index]

def wish_overlay():
    """Dynamic text overlay component"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("heart", color="gold", size=24),
                rx.text(SlideshowState.current_wish.get("message", ""), 
                       font_size="1.5rem", color="white"),
                spacing="2"
            ),
            rx.hstack(
                rx.icon("user", color="gold", size=16),
                rx.text(f"{SlideshowState.current_wish.get('name', '')} - {SlideshowState.current_wish.get('time', '')}", 
                       font_size="0.9rem", color="gold", font_style="italic"),
                spacing="1"
            ),
            spacing="2"
        ),
        position="absolute",
        bottom="15%",
        left="15%", 
        right="15%",
        background="rgba(0,0,0,0.6)",
        backdrop_filter="blur(8px)",
        border_radius="15px",
        padding="20px",
        color="white",
        animation="slideInFromBottom 0.8s ease-out"
    )

def photo_slideshow():
    """Main photo slideshow component"""
    return rx.box(
        rx.image(
            src=SlideshowState.current_photos[SlideshowState.current_index].get("filename", ""),
            width="100%",
            height="100vh",
            object_fit="cover"
        ),
        wish_overlay(),
        position="relative",
        width="100%",
        height="100vh"
    )

@rx.page("/big-screen")
def big_screen_display():
    return rx.vstack(
        photo_slideshow(),
        # Auto-advance photos every 10 seconds
        rx.script("""
            setInterval(() => {
                window.location.reload();
            }, 10000);
        """),
        width="100%",
        height="100vh"
    )

# Real-time updates when new photos are uploaded
def add_new_photo_to_slideshow(photo_data):
    """Add new photo to big screen slideshow in real-time"""
    # Update Reflex state with new photo
    SlideshowState.current_photos.append(photo_data)
```

**Libraries Integration:**
- **Reflex Components:** Built-in smooth transitions
- **Reflex State:** Real-time state management  
- **Reflex Icons:** Professional icon system
- **WebSocket:** Built-in real-time updates
- **Custom Styling:** Instagram/YouTube style overlays

### Library Selection Criteria

1. **Size:** < 50KB when possible (for Raspberry Pi performance)
2. **Maintenance:** Active development and community
3. **Documentation:** Well-documented with examples
4. **Browser Support:** Works across all modern browsers
5. **Performance:** Optimized for smooth animations
6. **License:** MIT/Apache for commercial use

### Avoided Reinventions

❌ **Don't Build:** Custom slideshow engine  
✅ **Use:** Swiper.js

❌ **Don't Build:** Text animation system  
✅ **Use:** AOS + Animate.css

❌ **Don't Build:** Audio player controls  
✅ **Use:** Howler.js + HTML5 audio

❌ **Don't Build:** Image processing  
✅ **Use:** Pillow (Python)

❌ **Don't Build:** YouTube downloader  
✅ **Use:** yt-dlp

❌ **Don't Build:** Icon system  
✅ **Use:** Tabler Icons

### Performance Optimization

**Bundle Strategy:**
- **Critical CSS:** Inline essential styles
- **Deferred JS:** Load animations after core functionality
- **Lazy Loading:** Load images as needed
- **CDN Fallbacks:** Local copies for offline USB memory book

### Recommended Framework: Reflex + Libraries

Perfect combination because:
- **Reflex:** Handles Python backend, file uploads, real-time updates, modern React frontend
- **Frontend Libraries:** Handle animations, slideshows, effects
- **Easy Integration:** Reflex allows custom CSS/JS injection and React component wrapping
- **Raspberry Pi Performance:** Lightweight libraries ensure smooth operation
- **Modern Design:** Professional React components out of the box

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
6. **Professional Icons:** Tabler Icons for clean, modern appearance

### Color Palette
- **Primary:** Gold (#FFD700) - Celebration theme
- **Secondary:** Deep Pink (#FF1493) - Birthday vibes
- **Accent:** White (#FFFFFF) - Clean contrast
- **Background:** Light gradient (#FFF8DC to #F0E68C)

### Typography
- **Headers:** Large, bold, celebratory fonts
- **Body:** Clean, readable sans-serif
- **Special:** Script font for wishes display

### Icon System
- **Source:** Tabler Icons (professional, clean, modern)
- **Usage:** [camera-icon], [user-icon], [heart-icon], [music-icon], etc.
- **Style:** Consistent 24px size for interface elements
- **Color:** Match theme colors (gold, deep pink, white)

### Responsive Breakpoints
- **Mobile:** 320px - 768px (primary focus)
- **Tablet:** 768px - 1024px
- **Desktop/Big Screen:** 1920x1080+

---

## Admin Interface

### Export Options
```
┌─────────────────────────────────────┐
│  [settings] Party Control Center            │
├─────────────────────────────────────┤
│                                     │
│  Event Settings:                    │
│  • Birthday Person: [Input]         │
│  • Party Title: [Input]             │
│  • Slideshow Duration: [5s] [clock] │
│                                     │
│  Content Moderation:                │
│  • [Pending Photos: 3]             │
│  • [Pending Music: 1]              │
│                                     │
│  Memory Book Export:                │
│  • [Generate USB Memory Book] [gift]│
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

### Phase 1: Core Reflex Framework (Week 1)
- [ ] Set up Reflex application structure
- [ ] Create SQLite database and models
- [ ] Implement basic mobile interface with Reflex components
- [ ] Set up file upload handling

### Phase 2: Display System (Week 2)
- [ ] Big screen slideshow functionality using Reflex
- [ ] Real-time queue displays
- [ ] Music player integration
- [ ] QR code generation

### Phase 3: Dynamic Text Effects & Music Integration (Week 3)
- [ ] Implement AOS and Animate.css for text overlays
- [ ] Create Instagram/YouTube style wish animations
- [ ] Integrate Swiper.js for smooth photo transitions
- [ ] Local music library indexing with metadata
- [ ] Search functionality implementation
- [ ] Ollama LLM integration for mood-based suggestions
- [ ] YouTube fallback system with yt-dlp
- [ ] Real-time text overlay synchronization with photos

### Phase 4: Polish & Memory Book (Week 4)
- [ ] UI/UX refinements with Tabler Icons
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
├── app.py                 # Main Reflex application
├── database/
│   ├── models.py         # SQLite models
│   └── migrations.py     # Database setup
├── static/
│   ├── uploads/          # Photo/video storage
│   ├── music/            # Music library
│   └── assets/           # Static assets
├── components/
│   ├── mobile_interface.py # Mobile guest interface
│   ├── big_screen.py     # Big screen display
│   └── admin_panel.py    # Admin interface
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
    """Generate self-contained HTML with embedded CSS/JS and animations"""
    
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>50th Birthday Memory Book</title>
        
        <!-- Embedded Libraries (CDN fallback for offline use) -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css">
        <link rel="stylesheet" href="https://unpkg.com/aos@2.3.1/dist/aos.css">
        
        <style>
            /* Embedded CSS - works offline */
            body { 
                font-family: 'Arial', sans-serif; 
                background: linear-gradient(135deg, #fdf2f8, #fce7f3);
                margin: 0;
                padding: 20px;
            }
            
            .memory-book-header {
                text-align: center;
                margin-bottom: 40px;
                animation: fadeInDown 2s ease-out;
            }
            
            .polaroid { 
                background: white; 
                padding: 15px 15px 25px 15px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                transform: rotate(-2deg);
                transition: transform 0.3s ease;
                margin: 30px;
            }
            
            .polaroid:nth-child(even) { transform: rotate(2deg); }
            .polaroid:hover { transform: rotate(0deg) scale(1.05); }
            
            .memory-card { 
                margin: 20px auto; 
                max-width: 400px;
                position: relative;
            }
            
            .photo-container {
                position: relative;
                overflow: hidden;
                border-radius: 10px;
            }
            
            .photo-container img {
                width: 100%;
                height: auto;
                cursor: pointer;
                transition: transform 0.3s ease;
            }
            
            .photo-container:hover img {
                transform: scale(1.1);
            }
            
            .wish-text {
                font-style: italic;
                color: #2d3748;
                margin: 15px 0;
                font-size: 1.1em;
                line-height: 1.4;
            }
            
            .submitter-info {
                color: #ec4899;
                font-weight: bold;
                font-size: 0.9em;
            }
            
            .music-section {
                margin-top: 15px;
                padding: 10px;
                background: #f7fafc;
                border-radius: 8px;
            }
            
            .audio-player { 
                margin: 10px 0; 
                width: 100%;
            }
            
            .audio-player audio {
                width: 100%;
                outline: none;
            }
            
            .song-info {
                color: #4a5568;
                font-size: 0.9em;
                margin-top: 5px;
            }
            
            /* Fullscreen image modal */
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.9);
                animation: fadeIn 0.3s;
            }
            
            .modal-content {
                margin: auto;
                display: block;
                width: 80%;
                max-width: 800px;
                max-height: 80%;
                margin-top: 10%;
                animation: zoomIn 0.3s;
            }
            
            .close {
                position: absolute;
                top: 20px;
                right: 35px;
                color: #f1f1f1;
                font-size: 40px;
                font-weight: bold;
                cursor: pointer;
            }
            
            @keyframes fadeIn { from {opacity: 0;} to {opacity: 1;} }
            @keyframes zoomIn { from {transform: scale(0);} to {transform: scale(1);} }
            @keyframes fadeInDown { 
                from { opacity: 0; transform: translateY(-30px); } 
                to { opacity: 1; transform: translateY(0); } 
            }
        </style>
    </head>
    <body>
        <div class="memory-book-header" data-aos="fade-down">
            <h1 style="font-size: 3em; color: #ec4899; margin: 0;">Happy 50th Birthday!</h1>
            <p style="font-size: 1.2em; color: #6b7280;">A Collection of Beautiful Memories</p>
        </div>
        
        <div class="memories-container">
    """
    
    # Add each memory as HTML with AOS animations
    for i, memory in enumerate(memories):
        animation_type = ["fade-up", "fade-left", "fade-right", "zoom-in"][i % 4]
        delay = (i % 3) * 200  # Stagger animations
        
        html += f"""
        <div class="memory-card polaroid" data-aos="{animation_type}" data-aos-delay="{delay}">
            <div class="photo-container">
                <img src="photos/{memory['photo_filename']}" 
                     alt="Birthday Memory" 
                     onclick="showFullImage(this)">
            </div>
            
            <div class="wish-text">
                "{memory['wish_message']}"
            </div>
            
            <div class="submitter-info">
                {memory['guest_name']} • {memory['formatted_timestamp']}
            </div>
            
            <div class="music-section">
                <div style="font-weight: bold; color: #2d3748; margin-bottom: 8px;">
                    Music Suggestion:
                </div>
                <audio controls preload="none">
                    <source src="music/{memory['music_filename']}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
                <div class="song-info">
                    "{memory['song_title']}" by {memory['artist']}
                </div>
            </div>
        </div>
        """
    
    html += """
        </div>
        
        <!-- Fullscreen Modal -->
        <div id="imageModal" class="modal">
            <span class="close">&times;</span>
            <img class="modal-content" id="modalImage">
        </div>
        
        <!-- Embedded JavaScript Libraries -->
        <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>
        
        <script>
            // Initialize AOS animations
            AOS.init({
                duration: 1000,
                once: true,
                offset: 100
            });
            
            // Image modal functionality
            function showFullImage(img) {
                const modal = document.getElementById('imageModal');
                const modalImg = document.getElementById('modalImage');
                modal.style.display = 'block';
                modalImg.src = img.src;
            }
            
            // Close modal
            document.querySelector('.close').onclick = function() {
                document.getElementById('imageModal').style.display = 'none';
            }
            
            // Close modal on background click
            window.onclick = function(event) {
                const modal = document.getElementById('imageModal');
                if (event.target == modal) {
                    modal.style.display = 'none';
                }
            }
            
            // Add touch gestures for mobile
            document.addEventListener('touchstart', handleTouchStart, false);
            document.addEventListener('touchmove', handleTouchMove, false);
            
            let xDown = null;
            let yDown = null;
            
            function handleTouchStart(evt) {
                const firstTouch = evt.touches[0];
                xDown = firstTouch.clientX;
                yDown = firstTouch.clientY;
            }
            
            function handleTouchMove(evt) {
                if (!xDown || !yDown) return;
                
                const xUp = evt.touches[0].clientX;
                const yUp = evt.touches[0].clientY;
                
                const xDiff = xDown - xUp;
                const yDiff = yDown - yUp;
                
                // Close modal on swipe down
                if (Math.abs(yDiff) > Math.abs(xDiff) && yDiff < -50) {
                    document.getElementById('imageModal').style.display = 'none';
                }
                
                xDown = null;
                yDown = null;
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

*This PRD serves as the blueprint for creating a magical birthday celebration experience using Reflex framework. Each feature is designed with love, technical feasibility, and user joy in mind.*