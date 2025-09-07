"""Advanced big screen display with enhanced text overlays and music integration."""

import reflex as rx
from typing import List, Dict, Optional
import asyncio
from sqlmodel import select, desc
from database.models import Photo, MusicQueue, Settings, get_session, get_setting
from utils.qr_generator import generate_qr_code, get_mobile_url
from utils.music_library import music_search, music_indexer
from utils.ollama_client import mood_suggester
from utils.youtube_fallback import music_resolver


class AdvancedBigScreenState(rx.State):
    """Enhanced state management for advanced big screen display."""
    
    # Photo slideshow state
    current_photo_index: int = 0
    photos: List[dict] = []
    is_slideshow_active: bool = True
    slideshow_duration: int = 8  # 8 seconds per photo as specified
    
    # Text overlay state
    overlay_visible: bool = False
    overlay_animation_class: str = ""
    current_overlay_text: str = ""
    current_overlay_user: str = ""
    
    # Music system state
    photo_queue: List[dict] = []
    music_queue: List[dict] = []
    current_song: dict = {}
    is_playing: bool = False
    volume: float = 0.7
    
    # Music search state
    search_query: str = ""
    search_type: str = "all"  # all, title, artist, album, mood
    search_results: List[dict] = []
    is_searching: bool = False
    
    # Music library stats
    library_stats: dict = {}
    is_indexing: bool = False
    indexing_progress: str = ""
    
    # App settings
    party_title: str = "50th Birthday Celebration"
    host_name: str = "Birthday Star"
    mobile_url: str = "http://localhost:3000"
    qr_code_data_uri: str = ""
    
    # Real-time sync
    is_loading: bool = False
    last_sync_time: str = ""
    
    # Ollama integration
    ollama_available: bool = False
    current_model: str = ""

    def on_load(self):
        """Initialize advanced big screen on page load."""
        self.load_settings()
        self.generate_qr_code()
        self.check_ollama_status()
        self.load_library_stats()
    
    def generate_qr_code(self):
        """Generate QR code for mobile interface."""
        self.mobile_url = get_mobile_url()
        self.qr_code_data_uri = generate_qr_code(self.mobile_url, size=120)
    
    def load_settings(self):
        """Load app settings from database."""
        self.party_title = get_setting("party_title", "50th Birthday Celebration")
        self.host_name = get_setting("host_name", "Birthday Star")
        self.slideshow_duration = int(get_setting("slideshow_duration", "8"))
    
    def load_photos(self):
        """Load processed photos for slideshow with enhanced metadata."""
        with get_session() as session:
            statement = select(Photo).where(
                Photo.is_processed == True
            ).order_by(desc(Photo.uploaded_at)).limit(50)
            
            photos = session.exec(statement).all()
            
            new_photo_ids = [photo.id for photo in photos]
            current_photo_ids = [p.get("id") for p in self.photos]
            
            if new_photo_ids != current_photo_ids:
                self.photos = [
                    {
                        "id": photo.id,
                        "filename": photo.filename,
                        "guest_name": photo.guest_name,
                        "wish_message": photo.wish_message or "",
                        "display_duration": photo.display_duration or self.slideshow_duration,
                        "uploaded_at": photo.uploaded_at.strftime("%H:%M"),
                        "file_path": f"/uploads/{photo.filename}"
                    }
                    for photo in photos
                ]
    
    def load_queues(self):
        """Load photo and music queues."""
        with get_session() as session:
            # Photo queue - next 6 photos
            photo_statement = select(Photo).where(
                Photo.is_processed == True
            ).order_by(desc(Photo.uploaded_at)).limit(6)
            
            upcoming_photos = session.exec(photo_statement).all()
            
            self.photo_queue = [
                {
                    "id": photo.id,
                    "filename": photo.filename,
                    "guest_name": photo.guest_name,
                    "thumbnail_path": f"/uploads/{photo.filename}",
                    "uploaded_at": photo.uploaded_at.strftime("%H:%M")
                }
                for photo in upcoming_photos
            ]
            
            # Music queue - next 5 songs
            music_statement = select(MusicQueue).where(
                MusicQueue.is_played == False
            ).order_by(MusicQueue.requested_at).limit(5)
            
            upcoming_songs = session.exec(music_statement).all()
            
            self.music_queue = [
                {
                    "id": song.id,
                    "title": song.title,
                    "artist": song.artist,
                    "guest_name": song.guest_name,
                    "source": song.source,
                    "requested_at": song.requested_at.strftime("%H:%M")
                }
                for song in upcoming_songs
            ]
    
    def next_photo(self):
        """Advance to next photo with overlay animation."""
        if len(self.photos) > 0:
            self.current_photo_index = (self.current_photo_index + 1) % len(self.photos)
            self.trigger_overlay_animation()
    
    def previous_photo(self):
        """Go to previous photo with overlay animation."""
        if len(self.photos) > 0:
            self.current_photo_index = (self.current_photo_index - 1) % len(self.photos)
            self.trigger_overlay_animation()
    
    def trigger_overlay_animation(self):
        """Trigger text overlay animation for current photo."""
        if len(self.photos) > 0 and self.current_photo_index < len(self.photos):
            current_photo = self.photos[self.current_photo_index]
            
            if current_photo.get("wish_message"):
                self.current_overlay_text = current_photo["wish_message"]
                self.current_overlay_user = current_photo["guest_name"]
                self.overlay_animation_class = "animate__animated animate__slideInUp"
                self.overlay_visible = True
            else:
                self.overlay_visible = False
    
    def hide_overlay(self):
        """Hide text overlay with fade out animation."""
        self.overlay_animation_class = "animate__animated animate__fadeOut"
        self.overlay_visible = False
    
    def toggle_slideshow(self):
        """Toggle slideshow play/pause."""
        self.is_slideshow_active = not self.is_slideshow_active
    
    def refresh_content(self):
        """Manually refresh slideshow and queues."""
        self.is_loading = True
        self.load_photos()
        self.load_queues()
        self.last_sync_time = "Just now"
        self.is_loading = False
    
    # Music Search Methods
    def update_search_query(self, query: str):
        """Update search query."""
        self.search_query = query
    
    def set_search_type(self, search_type: str):
        """Set search type."""
        self.search_type = search_type
    
    async def search_music(self):
        """Search music using selected method."""
        if not self.search_query.strip():
            return
        
        self.is_searching = True
        self.search_results = []
        
        try:
            if self.search_type == "mood" and self.ollama_available:
                # Use Ollama for mood-based search
                keywords = await mood_suggester.suggest_music_keywords(self.search_query)
                
                # Search for each keyword and combine results
                all_results = []
                for keyword in keywords:
                    results = music_search.search_all(keyword, limit=5)
                    all_results.extend(results)
                
                # Remove duplicates and limit results
                seen_ids = set()
                unique_results = []
                for result in all_results:
                    if result['id'] not in seen_ids:
                        seen_ids.add(result['id'])
                        unique_results.append(result)
                
                self.search_results = unique_results[:20]
                
            elif self.search_type == "title":
                self.search_results = music_search.search_by_title(self.search_query, limit=20)
            elif self.search_type == "artist":
                self.search_results = music_search.search_by_artist(self.search_query, limit=20)
            elif self.search_type == "album":
                self.search_results = music_search.search_by_album(self.search_query, limit=20)
            else:  # all
                self.search_results = music_search.search_all(self.search_query, limit=20)
                
        except Exception as e:
            print(f"Search error: {e}")
            self.search_results = []
        
        self.is_searching = False
    
    def add_to_queue(self, track_id: int):
        """Add track to music queue."""
        # TODO: Implement adding track to queue
        pass
    
    # Music Library Methods
    async def start_indexing(self):
        """Start music library indexing."""
        self.is_indexing = True
        self.indexing_progress = "Starting indexing..."
        
        try:
            result = music_indexer.index_library(force_reindex=False)
            if result['success']:
                self.indexing_progress = f"Indexed {result['indexed']} tracks"
                self.load_library_stats()
            else:
                self.indexing_progress = f"Error: {result.get('error', 'Unknown error')}"
        except Exception as e:
            self.indexing_progress = f"Error: {str(e)}"
        
        self.is_indexing = False
    
    def load_library_stats(self):
        """Load music library statistics."""
        try:
            self.library_stats = music_search.get_library_stats()
        except Exception as e:
            print(f"Error loading library stats: {e}")
            self.library_stats = {}
    
    async def check_ollama_status(self):
        """Check if Ollama is available."""
        try:
            await mood_suggester.initialize()
            model_info = await mood_suggester.get_model_info()
            self.ollama_available = model_info['is_available']
            self.current_model = model_info.get('preferred_model', 'None')
        except Exception as e:
            print(f"Ollama check error: {e}")
            self.ollama_available = False
            self.current_model = "Unavailable"
    
    # Music Player Controls
    def update_volume(self, value: list[int | float]):
        """Update music volume."""
        if value:
            self.volume = value[0] / 100
    
    def toggle_music(self):
        """Toggle music play/pause."""
        self.is_playing = not self.is_playing
    
    # Computed properties
    @rx.var
    def photo_queue_count_text(self) -> str:
        return f"{len(self.photo_queue)} photos queued"
    
    @rx.var
    def music_queue_count_text(self) -> str:
        return f"{len(self.music_queue)} songs queued"
    
    @rx.var
    def photo_counter_text(self) -> str:
        if len(self.photos) == 0:
            return "0 / 0"
        return f"{self.current_photo_index + 1} / {len(self.photos)}"
    
    @rx.var
    def celebration_text(self) -> str:
        return f"Celebrating {self.host_name}"
    
    @rx.var
    def library_stats_text(self) -> str:
        stats = self.library_stats
        if not stats:
            return "Library not indexed"
        
        tracks = stats.get('total_tracks', 0)
        artists = stats.get('total_artists', 0)
        
        return f"{tracks:,} tracks • {artists:,} artists"
    
    @rx.var
    def current_photo_data(self) -> dict:
        """Get current photo data safely."""
        if len(self.photos) > 0 and self.current_photo_index < len(self.photos):
            return self.photos[self.current_photo_index]
        return {}


def enhanced_slideshow_display() -> rx.Component:
    """Enhanced slideshow with Instagram-style text overlays."""
    return rx.box(
        # Photo container
        rx.cond(
            AdvancedBigScreenState.photos.length() > 0,
            rx.box(
                # Current photo with Swiper-like transitions
                rx.cond(
                    AdvancedBigScreenState.photos.length() > AdvancedBigScreenState.current_photo_index,
                    rx.image(
                        src=AdvancedBigScreenState.current_photo_data["file_path"],
                        alt="Current photo",
                        width="100%",
                        height="100%",
                        object_fit="contain",
                        class_name="slideshow-photo swiper-slide",
                        style={
                            "transition": "opacity 0.8s ease-in-out, transform 0.8s ease-in-out"
                        }
                    ),
                    rx.box()
                ),
                
                # Enhanced Instagram-style text overlay
                rx.cond(
                    AdvancedBigScreenState.overlay_visible & 
                    (AdvancedBigScreenState.current_photo_data.get("wish_message", "") != ""),
                    rx.box(
                        rx.vstack(
                            # User info with Tabler icons
                            rx.hstack(
                                rx.icon("user", size=20, color="white"),
                                rx.text(
                                    AdvancedBigScreenState.current_photo_data.get("guest_name", ""),
                                    size="3",
                                    weight="bold",
                                    color="white"
                                ),
                                align="center",
                                spacing="2"
                            ),
                            
                            # Wish message with heart icon
                            rx.hstack(
                                rx.icon("heart", size=18, color="#ff6b6b"),
                                rx.text(
                                    AdvancedBigScreenState.current_photo_data.get("wish_message", ""),
                                    size="4",
                                    color="white",
                                    style={
                                        "font_size": "clamp(1.2rem, 2.5vw, 2rem)",
                                        "line_height": "1.4",
                                        "text_shadow": "2px 2px 4px rgba(0,0,0,0.7)"
                                    }
                                ),
                                align="start",
                                spacing="3",
                                width="100%"
                            ),
                            
                            spacing="3",
                            align="start",
                            width="100%"
                        ),
                        
                        # Positioning and styling as per PRD specs
                        position="absolute",
                        bottom="15%",  # Bottom 15% of screen
                        left="4%",
                        right="4%",
                        max_height="25%",  # Max 25% height
                        background="rgba(0,0,0,0.6)",
                        backdrop_filter="blur(8px)",
                        border_radius="12px",
                        padding="20px",
                        
                        # Animation classes
                        class_name=AdvancedBigScreenState.overlay_animation_class,
                        
                        # AOS animation attributes
                        data_aos="slide-up",
                        data_aos_duration="800",
                        data_aos_easing="ease-out"
                    )
                ),
                
                position="relative",
                width="100%",
                height="100%",
                bg="black",
                overflow="hidden"
            ),
            
            # No photos placeholder
            rx.vstack(
                rx.icon("image", size=64, color="gray.500"),
                rx.heading("No Photos Yet", size="6", color="gray.600"),
                rx.text(
                    "Waiting for guests to share their memories...",
                    size="4",
                    color="gray.500",
                    text_align="center"
                ),
                rx.button(
                    "Load Photos",
                    on_click=AdvancedBigScreenState.refresh_content,
                    size="3",
                    color_scheme="blue",
                    variant="solid"
                ),
                spacing="4",
                align="center",
                justify="center",
                height="100%",
                bg="gray.900"
            )
        ),
        width="100%",
        height="100%"
    )


def music_search_interface() -> rx.Component:
    """Enhanced music search interface with multiple search types."""
    return rx.vstack(
        # Search header
        rx.hstack(
            rx.icon("search", size=20, color="blue.500"),
            rx.heading("Music Search", size="4", color="white"),
            align="center",
            spacing="2"
        ),
        
        # Search type selector
        rx.hstack(
            rx.select(
                ["all", "title", "artist", "album", "mood"],
                value=AdvancedBigScreenState.search_type,
                on_change=AdvancedBigScreenState.set_search_type,
                size="2"
            ),
            rx.cond(
                AdvancedBigScreenState.ollama_available,
                rx.badge("Ollama Ready", color_scheme="green"),
                rx.badge("Ollama Offline", color_scheme="gray")
            ),
            align="center",
            spacing="2",
            width="100%"
        ),
        
        # Search input
        rx.input(
            placeholder=rx.cond(
                AdvancedBigScreenState.search_type == "mood",
                "Describe the mood (e.g., 'happy party music')",
                "Search music..."
            ),
            value=AdvancedBigScreenState.search_query,
            on_change=AdvancedBigScreenState.update_search_query,
            size="3",
            width="100%"
        ),
        
        # Search button
        rx.button(
            rx.cond(
                AdvancedBigScreenState.is_searching,
                rx.hstack(
                    rx.spinner(size="1"),
                    rx.text("Searching..."),
                    align="center",
                    spacing="2"
                ),
                rx.hstack(
                    rx.icon("search", size=16),
                    rx.text("Search"),
                    align="center",
                    spacing="2"
                )
            ),
            on_click=AdvancedBigScreenState.search_music,
            disabled=AdvancedBigScreenState.is_searching | (AdvancedBigScreenState.search_query == ""),
            size="3",
            width="100%",
            color_scheme="blue"
        ),
        
        # Search results
        rx.cond(
            AdvancedBigScreenState.search_results.length() > 0,
            rx.vstack(
                rx.heading(f"Results ({AdvancedBigScreenState.search_results.length()})", size="3", color="white"),
                
                rx.scroll_area(
                    rx.vstack(
                        rx.foreach(
                            AdvancedBigScreenState.search_results[:5],  # Show top 5
                            lambda track: rx.card(
                                rx.hstack(
                                    rx.vstack(
                                        rx.text(track["title"], size="2", weight="bold", color="white"),
                                        rx.text(track["artist"], size="1", color="gray.300"),
                                        rx.text(track["duration_formatted"], size="1", color="gray.500"),
                                        spacing="1",
                                        align="start",
                                        flex="1"
                                    ),
                                    rx.icon_button(
                                        rx.icon("plus", size=14),
                                        on_click=lambda: AdvancedBigScreenState.add_to_queue(track["id"]),
                                        size="2",
                                        variant="ghost",
                                        color="white"
                                    ),
                                    align="center",
                                    justify="between",
                                    width="100%"
                                ),
                                bg="rgba(255,255,255,0.1)",
                                padding="3",
                                width="100%"
                            )
                        ),
                        spacing="2",
                        width="100%"
                    ),
                    height="200px"
                ),
                spacing="3",
                width="100%"
            )
        ),
        
        # Library stats
        rx.text(
            AdvancedBigScreenState.library_stats_text,
            size="2",
            color="gray.400",
            text_align="center"
        ),
        
        spacing="3",
        width="100%",
        max_width="350px"
    )


def music_library_panel() -> rx.Component:
    """Music library management panel."""
    return rx.vstack(
        # Library header
        rx.hstack(
            rx.icon("music", size=20, color="green.500"),
            rx.heading("Music Library", size="4", color="white"),
            align="center",
            spacing="2"
        ),
        
        # Indexing controls
        rx.cond(
            AdvancedBigScreenState.is_indexing,
            rx.vstack(
                rx.spinner(size="3"),
                rx.text(AdvancedBigScreenState.indexing_progress, size="2", color="white"),
                spacing="2",
                align="center"
            ),
            rx.button(
                "Index Music Library",
                on_click=AdvancedBigScreenState.start_indexing,
                size="2",
                width="100%",
                color_scheme="green"
            )
        ),
        
        # Search interface
        music_search_interface(),
        
        spacing="4",
        width="100%"
    )


def enhanced_photo_queue_sidebar() -> rx.Component:
    """Enhanced photo queue with real-time sync indicators."""
    return rx.vstack(
        # Header with sync status
        rx.hstack(
            rx.icon("images", size=20, color="blue.500"),
            rx.heading("Photo Queue", size="4", color="white"),
            rx.cond(
                AdvancedBigScreenState.is_loading,
                rx.spinner(size="1"),
                rx.badge("Live", color_scheme="green")
            ),
            align="center",
            spacing="2",
            justify="between",
            width="100%"
        ),
        
        # Queue items with AOS animations
        rx.scroll_area(
            rx.vstack(
                rx.foreach(
                    AdvancedBigScreenState.photo_queue,
                    lambda photo: rx.card(
                        rx.hstack(
                            rx.image(
                                src=photo["thumbnail_path"],
                                alt=f"Photo by {photo['guest_name']}",
                                width="50px",
                                height="50px",
                                border_radius="md",
                                object_fit="cover"
                            ),
                            rx.vstack(
                                rx.text(
                                    photo["guest_name"],
                                    size="2",
                                    weight="bold",
                                    color="white"
                                ),
                                rx.text(
                                    photo["uploaded_at"],
                                    size="1",
                                    color="gray.400"
                                ),
                                spacing="1",
                                align="start"
                            ),
                            align="center",
                            spacing="3",
                            width="100%"
                        ),
                        bg="rgba(255,255,255,0.1)",
                        border="1px solid rgba(255,255,255,0.2)",
                        padding="2",
                        width="100%",
                        class_name="queue-item",
                        data_aos="fade-in",
                        data_aos_delay="100"
                    )
                ),
                spacing="2",
                width="100%"
            ),
            height="300px",
            class_name="queue-container"
        ),
        
        # Queue status with last sync time
        rx.vstack(
            rx.text(
                AdvancedBigScreenState.photo_queue_count_text,
                size="2",
                color="gray.400",
                text_align="center"
            ),
            rx.cond(
                AdvancedBigScreenState.last_sync_time != "",
                rx.text(
                    f"Last sync: {AdvancedBigScreenState.last_sync_time}",
                    size="1",
                    color="gray.500",
                    text_align="center"
                )
            ),
            spacing="1",
            align="center"
        ),
        
        spacing="3",
        width="100%"
    )


def enhanced_music_queue_sidebar() -> rx.Component:
    """Enhanced music queue with source indicators."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.icon("music", size=20, color="green.500"),
            rx.heading("Music Queue", size="4", color="white"),
            align="center",
            spacing="2"
        ),
        
        # Queue items with source indicators
        rx.scroll_area(
            rx.vstack(
                rx.foreach(
                    AdvancedBigScreenState.music_queue,
                    lambda song: rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.icon(
                                    rx.cond(song["source"] == "local", "hard_drive", "youtube"),
                                    size=16,
                                    color=rx.cond(song["source"] == "local", "blue.400", "red.400")
                                ),
                                rx.vstack(
                                    rx.text(
                                        song["title"],
                                        size="2",
                                        weight="bold",
                                        color="white",
                                        text_wrap="wrap"
                                    ),
                                    rx.text(
                                        song["artist"],
                                        size="2",
                                        color="gray.300",
                                        text_wrap="wrap"
                                    ),
                                    spacing="1",
                                    align="start",
                                    flex="1"
                                ),
                                align="start",
                                spacing="2",
                                width="100%"
                            ),
                            rx.hstack(
                                rx.text(
                                    f"by {song['guest_name']}",
                                    size="1",
                                    color="gray.500"
                                ),
                                rx.spacer(),
                                rx.text(
                                    song["requested_at"],
                                    size="1",
                                    color="gray.500"
                                ),
                                width="100%",
                                align="center"
                            ),
                            spacing="2",
                            align="stretch"
                        ),
                        bg="rgba(255,255,255,0.1)",
                        border="1px solid rgba(255,255,255,0.2)",
                        padding="3",
                        width="100%",
                        class_name="queue-item",
                        data_aos="fade-in",
                        data_aos_delay="150"
                    )
                ),
                spacing="2",
                width="100%"
            ),
            height="200px",
            class_name="queue-container"
        ),
        
        # Queue status
        rx.text(
            AdvancedBigScreenState.music_queue_count_text,
            size="2",
            color="gray.400",
            text_align="center"
        ),
        
        spacing="3",
        width="100%"
    )


def enhanced_qr_code_display() -> rx.Component:
    """Enhanced QR code with animations."""
    return rx.vstack(
        rx.heading("Join the Party!", size="5", color="white", text_align="center"),
        
        # Animated QR code container
        rx.box(
            rx.vstack(
                rx.cond(
                    AdvancedBigScreenState.qr_code_data_uri != "",
                    rx.image(
                        src=AdvancedBigScreenState.qr_code_data_uri,
                        alt="QR Code for mobile interface",
                        width="120px",
                        height="120px",
                        border_radius="md",
                        class_name="animate__animated animate__pulse animate__infinite"
                    ),
                    rx.box(
                        rx.spinner(size="3"),
                        width="120px",
                        height="120px",
                        bg="white",
                        border_radius="md",
                        display="flex",
                        align_items="center",
                        justify_content="center"
                    )
                ),
                rx.text(
                    "Scan to share",
                    size="2",
                    color="white",
                    text_align="center"
                ),
                rx.text(
                    "your memories",
                    size="2",
                    color="white", 
                    text_align="center"
                ),
                spacing="2",
                align="center"
            ),
            padding="4",
            bg="rgba(255,255,255,0.1)",
            border_radius="xl",
            border="1px solid rgba(255,255,255,0.2)",
            class_name="qr-container",
            data_aos="zoom-in",
            data_aos_duration="1000"
        ),
        
        spacing="3",
        align="center"
    )


def enhanced_slideshow_controls() -> rx.Component:
    """Enhanced slideshow controls with better UX."""
    return rx.hstack(
        # Navigation controls
        rx.hstack(
            rx.icon_button(
                rx.icon("chevron_left", size=20),
                on_click=AdvancedBigScreenState.previous_photo,
                size="3",
                variant="ghost",
                color="white",
                disabled=AdvancedBigScreenState.photos.length() == 0
            ),
            
            rx.icon_button(
                rx.icon(
                    rx.cond(AdvancedBigScreenState.is_slideshow_active, "pause", "play"),
                    size=20
                ),
                on_click=AdvancedBigScreenState.toggle_slideshow,
                size="3",
                variant="solid",
                color_scheme="blue",
                disabled=AdvancedBigScreenState.photos.length() == 0
            ),
            
            rx.icon_button(
                rx.icon("chevron_right", size=20),
                on_click=AdvancedBigScreenState.next_photo,
                size="3",
                variant="ghost",
                color="white",
                disabled=AdvancedBigScreenState.photos.length() == 0
            ),
            
            align="center",
            spacing="2"
        ),
        
        # Refresh and info
        rx.hstack(
            rx.icon_button(
                rx.cond(
                    AdvancedBigScreenState.is_loading,
                    rx.spinner(size="1"),
                    rx.icon("refresh_cw", size=16)
                ),
                on_click=AdvancedBigScreenState.refresh_content,
                size="2",
                variant="ghost",
                color="white",
                title="Refresh content",
                disabled=AdvancedBigScreenState.is_loading
            ),
            
            rx.text(
                AdvancedBigScreenState.photo_counter_text,
                size="2",
                color="gray.400"
            ),
            
            align="center",
            spacing="3"
        ),
        
        align="center",
        justify="between",
        width="100%"
    )


def enhanced_music_player_controls() -> rx.Component:
    """Enhanced music player with real-time info."""
    return rx.hstack(
        # Now playing info
        rx.hstack(
            rx.icon("music_2", size=20, color="green.500"),
            rx.vstack(
                rx.text(
                    rx.cond(
                        AdvancedBigScreenState.current_song,
                        AdvancedBigScreenState.current_song.get("title", "No song selected"),
                        "No song selected"
                    ),
                    size="3",
                    weight="bold",
                    color="white"
                ),
                rx.text(
                    "Ready for music requests",
                    size="2",
                    color="gray.400"
                ),
                spacing="1",
                align="start"
            ),
            align="center",
            spacing="3",
            flex="1"
        ),
        
        # Controls with enhanced styling
        rx.hstack(
            rx.icon_button(
                rx.icon("skip_back", size=16),
                size="2",
                variant="ghost",
                color="white",
                class_name="music-control-btn"
            ),
            rx.icon_button(
                rx.icon(
                    rx.cond(AdvancedBigScreenState.is_playing, "pause", "play"),
                    size=20
                ),
                on_click=AdvancedBigScreenState.toggle_music,
                size="3",
                variant="solid",
                color_scheme="green",
                class_name="music-control-btn"
            ),
            rx.icon_button(
                rx.icon("skip_forward", size=16),
                size="2",
                variant="ghost",
                color="white",
                class_name="music-control-btn"
            ),
            align="center",
            spacing="2",
            class_name="music-controls"
        ),
        
        # Volume control
        rx.hstack(
            rx.icon("volume_2", size=16, color="gray.400"),
            rx.slider(
                default_value=[AdvancedBigScreenState.volume * 100],
                on_change=AdvancedBigScreenState.update_volume,
                max_value=100,
                step=1,
                width="100px",
                size="2",
                class_name="volume-slider"
            ),
            align="center",
            spacing="2"
        ),
        
        align="center",
        justify="between",
        width="100%",
        padding="3",
        bg="rgba(0,0,0,0.8)",
        border_radius="lg"
    )


def advanced_big_screen_layout() -> rx.Component:
    """Complete advanced big screen layout with all enhancements."""
    return rx.box(
        # Header with enhanced animations
        rx.hstack(
            rx.vstack(
                rx.heading(
                    AdvancedBigScreenState.party_title,
                    size="8",
                    color="white",
                    weight="bold",
                    data_aos="fade-right"
                ),
                rx.text(
                    AdvancedBigScreenState.celebration_text,
                    size="4",
                    color="gray.300",
                    data_aos="fade-right",
                    data_aos_delay="200"
                ),
                spacing="1",
                align="start"
            ),
            rx.spacer(),
            enhanced_qr_code_display(),
            align="center",
            width="100%",
            padding="4",
            bg="rgba(0,0,0,0.9)",
            position="relative",
            z_index="10",
            class_name="big-screen-header"
        ),
        
        # Main content area
        rx.hstack(
            # Main slideshow area (75% width)
            rx.box(
                enhanced_slideshow_display(),
                width="75%",
                height="calc(100vh - 120px)",
                position="relative"
            ),
            
            # Right sidebar (25% width) with tabbed interface
            rx.vstack(
                # Tab selector
                rx.hstack(
                    rx.button("Photos", size="1", variant="ghost", color="white"),
                    rx.button("Music", size="1", variant="ghost", color="white"),
                    rx.button("Library", size="1", variant="ghost", color="white"),
                    spacing="2",
                    width="100%"
                ),
                
                # Content based on selected tab - for now showing all
                enhanced_photo_queue_sidebar(),
                rx.divider(color="rgba(255,255,255,0.2)"),
                enhanced_music_queue_sidebar(),
                rx.divider(color="rgba(255,255,255,0.2)"),
                music_library_panel(),
                
                spacing="4",
                width="25%",
                height="calc(100vh - 120px)",
                padding="4",
                bg="rgba(0,0,0,0.8)",
                overflow_y="auto",
                class_name="sidebar"
            ),
            
            width="100%",
            height="calc(100vh - 120px)",
            spacing="0"
        ),
        
        # Bottom controls
        rx.hstack(
            enhanced_slideshow_controls(),
            rx.spacer(),
            enhanced_music_player_controls(),
            align="center",
            justify="between",
            width="100%",
            padding="4",
            bg="rgba(0,0,0,0.9)",
            border_top="1px solid rgba(255,255,255,0.1)",
            class_name="bottom-controls"
        ),
        
        width="100vw",
        height="100vh",
        bg="black",
        overflow="hidden",
        on_mount=AdvancedBigScreenState.on_load,
        
        # Initialize animation libraries
        style={
            "font_family": "Inter, sans-serif"
        }
    )