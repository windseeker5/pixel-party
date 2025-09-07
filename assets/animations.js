// Animation libraries initialization for PixelParty

// Initialize AOS (Animate On Scroll) when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-out',
            once: false,
            mirror: true,
            offset: 50
        });
    }
});

// Swiper initialization for photo transitions
function initializePhotoSwiper() {
    if (typeof Swiper !== 'undefined') {
        const photoSwiper = new Swiper('.photo-swiper', {
            effect: 'fade',
            fadeEffect: {
                crossFade: true
            },
            autoplay: {
                delay: 8000,
                disableOnInteraction: false,
            },
            loop: true,
            allowTouchMove: false
        });
        
        return photoSwiper;
    }
    return null;
}

// Text overlay animations
function animateTextOverlay(element, type = 'slideUp') {
    if (!element) return;
    
    element.classList.remove('animate__fadeIn', 'animate__slideInUp', 'animate__fadeOut');
    
    switch (type) {
        case 'slideUp':
            element.classList.add('animate__animated', 'animate__slideInUp');
            break;
        case 'fadeIn':
            element.classList.add('animate__animated', 'animate__fadeIn');
            break;
        case 'fadeOut':
            element.classList.add('animate__animated', 'animate__fadeOut');
            break;
    }
}

// Auto-hide overlay after duration
function autoHideOverlay(element, duration = 8000) {
    if (!element) return;
    
    setTimeout(() => {
        animateTextOverlay(element, 'fadeOut');
        
        // Remove element after fade out
        setTimeout(() => {
            element.style.display = 'none';
        }, 1000);
    }, duration);
}

// Enhanced music control animations
function animateMusicControls() {
    const controls = document.querySelectorAll('.music-control-btn');
    
    controls.forEach(control => {
        control.addEventListener('click', function() {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    });
}

// Photo transition effects
function transitionPhoto(fromIndex, toIndex, photos) {
    const currentPhoto = document.querySelector(`[data-photo-index="${fromIndex}"]`);
    const nextPhoto = document.querySelector(`[data-photo-index="${toIndex}"]`);
    
    if (currentPhoto && nextPhoto) {
        // Fade out current
        currentPhoto.style.opacity = '0';
        currentPhoto.style.transform = 'scale(0.98)';
        
        // Fade in next
        setTimeout(() => {
            currentPhoto.style.display = 'none';
            nextPhoto.style.display = 'block';
            nextPhoto.style.opacity = '0';
            nextPhoto.style.transform = 'scale(1.02)';
            
            setTimeout(() => {
                nextPhoto.style.opacity = '1';
                nextPhoto.style.transform = 'scale(1)';
            }, 50);
        }, 400);
    }
}

// Queue item animations
function animateQueueItem(element, delay = 0) {
    if (!element) return;
    
    setTimeout(() => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.3s ease-out';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, 50);
    }, delay);
}

// Initialize all animations
function initializeAnimations() {
    // Initialize AOS
    if (typeof AOS !== 'undefined') {
        AOS.refresh();
    }
    
    // Initialize music controls
    animateMusicControls();
    
    // Add smooth transitions to all elements
    const elements = document.querySelectorAll('.queue-item, .slideshow-photo, .qr-container');
    elements.forEach(el => {
        el.style.transition = 'all 0.3s ease-out';
    });
}

// Call initialization when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAnimations);
} else {
    initializeAnimations();
}

// Re-initialize when content changes (for Reflex updates)
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            setTimeout(initializeAnimations, 100);
        }
    });
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});