# TikTok-Style Text Animations Implementation Plan

## 🎯 Project Goal
Implement 3 beautiful, rotating TikTok-style text animations for the big screen birthday party display using smart JavaScript libraries that won't conflict with HTMX.

## 📸 Current Issues (From Screenshots)
1. Text overlay appears correctly initially
2. After 1-2 seconds, text becomes garbled/corrupted
3. Conflict between current JavaScript and HTMX updates

## ✨ Solution Strategy: Smart JavaScript Libraries

### Core Principle
- Use well-tested, lightweight JavaScript animation libraries
- Ensure compatibility with HTMX's DOM updates
- Implement animations that complete before HTMX refresh (8-second cycle)

## 🎨 Three TikTok-Style Animations

### Animation 1: Typewriter Effect
**Library Option: TypeIt.js or Typed.js**
- Professional typewriter animation library
- Lightweight (~4KB gzipped)
- Features:
  - Letter-by-letter reveal
  - Customizable speed
  - Cursor effects
  - Works with dynamic content

### Animation 2: Neon Glow Pulse
**Library Option: Anime.js**
- Powerful animation library (16KB gzipped)
- Features:
  - Text glow effects
  - Color morphing
  - Pulsing animations
  - Timeline control for sequencing

### Animation 3: Bounce & Split Text
**Library Option: GSAP TextPlugin or Splitting.js**
- Industry-standard animation library
- Features:
  - Character/word splitting
  - Elastic bounce effects
  - Staggered animations
  - 3D transforms

## 🛠️ Implementation Approach

### 1. Library Integration
```html
<!-- Add to base.html or photo_display.html -->
<!-- Option A: Lightweight approach -->
<script src="https://cdn.jsdelivr.net/npm/typed.js@2.0.12"></script>
<script src="https://unpkg.com/splitting/dist/splitting.min.js"></script>

<!-- Option B: Full animation suite -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.1/anime.min.js"></script>
```

### 2. HTMX-Safe Implementation
```javascript
// Use HTMX events to initialize animations AFTER content loads
document.body.addEventListener('htmx:afterSwap', function(event) {
    // Only initialize on photo display updates
    if (event.detail.target.id === 'photo-display') {
        initTextAnimation();
    }
});

function initTextAnimation() {
    // Randomly select 1 of 3 animation styles
    const style = Math.floor(Math.random() * 3) + 1;
    
    switch(style) {
        case 1:
            initTypewriterEffect();
            break;
        case 2:
            initNeonGlowEffect();
            break;
        case 3:
            initBounceEffect();
            break;
    }
}
```

### 3. Animation Implementations

#### Style 1: Typewriter Effect
```javascript
function initTypewriterEffect() {
    const wishElement = document.querySelector('.wish-text-tiktok');
    if (!wishElement) return;
    
    new Typed('.wish-text-tiktok', {
        strings: [wishElement.textContent],
        typeSpeed: 50,
        showCursor: false,
        onComplete: () => {
            // Show sender name after wish completes
            animateSenderName();
        }
    });
}
```

#### Style 2: Neon Glow Effect
```javascript
function initNeonGlowEffect() {
    anime({
        targets: '.wish-text-tiktok',
        opacity: [0, 1],
        scale: [0.8, 1],
        textShadow: [
            '0 0 0px #fff',
            '0 0 80px #fff, 0 0 100px #00ffff'
        ],
        duration: 2000,
        easing: 'easeOutElastic(1, .5)'
    });
}
```

#### Style 3: Bounce Split Effect
```javascript
function initBounceEffect() {
    // Split text into characters
    Splitting({ target: '.wish-text-tiktok' });
    
    anime({
        targets: '.wish-text-tiktok .char',
        translateY: [-50, 0],
        opacity: [0, 1],
        delay: anime.stagger(50),
        duration: 800,
        easing: 'easeOutBounce'
    });
}
```

## 📁 Files to Modify

### 1. `/templates/components/photo_display.html`
- Remove conflicting JavaScript
- Add library-specific HTML structure
- Include animation trigger classes

### 2. `/templates/base.html`
- Add animation library CDN links
- Include global HTMX event listeners

### 3. `/templates/big_screen/slideshow.html`
- Ensure proper container structure
- Add animation-specific CSS classes

## 🎯 Animation Timing Design
```
Timeline (8 seconds total):
0s - 0.5s:  Photo fade in
0.5s - 2.5s: Text animation entrance
2.5s - 6.5s: Display with subtle effects
6.5s - 7.5s: Text fade out
7.5s - 8s:  Prepare for next photo
```

## 🚀 Implementation Steps

### Phase 1: Setup (30 minutes)
1. Back up current `photo_display.html`
2. Choose and integrate animation libraries
3. Remove conflicting JavaScript code

### Phase 2: Core Implementation (1 hour)
1. Implement typewriter effect with Typed.js
2. Create neon glow effect with Anime.js
3. Build bounce effect with Splitting.js
4. Add random style selection logic

### Phase 3: HTMX Integration (30 minutes)
1. Set up HTMX event listeners
2. Ensure animations reinitialize on content swap
3. Test animation cleanup between transitions

### Phase 4: Polish & Testing (30 minutes)
1. Fine-tune animation timings
2. Add mobile responsiveness
3. Test on Raspberry Pi hardware
4. Verify 8-second cycle compatibility

## ✅ Success Criteria
- [ ] No text corruption or garbling
- [ ] Smooth animations that complete within 8 seconds
- [ ] Random rotation between 3 distinct styles
- [ ] Compatible with HTMX updates
- [ ] Mobile responsive
- [ ] Performs well on Raspberry Pi 4

## 🎨 Visual References

### TikTok Text Trends (2024-2025)
1. **Typewriter**: Popular for reveals and announcements
2. **Neon Glow**: Used for party/celebration content
3. **Bounce/Elastic**: Common in birthday and celebration videos

## 📚 Library Resources
- **Typed.js**: https://github.com/mattboldt/typed.js/
- **Anime.js**: https://animejs.com/
- **Splitting.js**: https://splitting.js.org/
- **GSAP**: https://greensock.com/gsap/

## 🔧 Fallback Strategy
If libraries cause issues, implement simplified CSS-only versions:
- CSS `@keyframes` with calculated delays
- CSS custom properties for randomization
- Server-side text splitting for character animations

## 📝 Notes
- Priority is visual impact and reliability for 2-day party
- Animations should enhance, not distract from photos
- Keep total JavaScript payload under 50KB
- Test extensively with HTMX polling (every 8 seconds)

---

*Plan created for PixelParty - Birthday Memory & Music Experience*
*Date: 2025-01-12*