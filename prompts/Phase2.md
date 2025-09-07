Based on the completed Phase 1 and the PRD requirements, implement the big screen display system:

1. **Big Screen Slideshow Functionality:**
   - Create /big-screen route with full-screen photo display
   - Implement photo slideshow with Reflex components
   - Auto-advance photos every 10 seconds (configurable)
   - Real-time photo queue system showing next 6 photos as thumbnails
   - Smooth transitions between photos using Reflex animations

2. **Real-time Queue Displays:**
   - Photo queue sidebar showing upcoming submissions with thumbnails
   - Music queue sidebar showing next 5 songs (title, artist, submitted by)
   - Real-time updates using Reflex's built-in state management
   - WebSocket integration for instant updates when guests submit content

3. **Music Player Integration:**
   - Basic HTML5 audio player integration
   - Music controls (play, pause, skip, volume)
   - Now playing display with song info and submitter name
   - Queue management system

4. **QR Code Generation:**
   - Generate QR code linking to mobile interface
   - Display QR code prominently on big screen
   - Make QR code easily scannable from phones
   - Add instructions "Scan to share your memories"

5. **Layout Implementation:**
   - Follow the PRD layout specification with proper proportions
   - Header with birthday title and Tabler Icons
   - Main photo display area (75% visual priority)
   - Right sidebar with queues (20% visual priority)
   - Bottom controls bar (5% visual priority)
   - Responsive design for different screen sizes

Create the complete big screen experience with real-time updates and proper visual hierarchy as specified in the PRD.