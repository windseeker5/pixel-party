"""Big screen display components for slideshow and real-time queues."""

import reflex as rx
from typing import List, Optional
import datetime
from sqlmodel import select, desc
from database.models import Photo, MusicQueue, Settings, get_session, get_setting
from utils.qr_generator import generate_qr_code, get_mobile_url


class BigScreenState(rx.State):
    """State management for big screen display."""
    
    # Slideshow state
    current_photo_index: int = 0
    photos: List[dict] = []
    is_slideshow_active: bool = True
    slideshow_duration: int = 10  # seconds
    last_update: datetime.datetime = datetime.datetime.now()
    
    # Queue display state
    photo_queue: List[dict] = []
    music_queue: List[dict] = []
    
    # Music player state
    current_song: dict = {}
    is_playing: bool = False
    volume: float = 0.7
    
    # App settings
    party_title: str = "50th Birthday Celebration"
    host_name: str = "Birthday Star"
    mobile_url: str = "http://localhost:3000"  # Will be updated with actual URL
    qr_code_data_uri: str = ""
    
    # Real-time update state
    is_loading: bool = False

    def on_load(self):
        """Initialize big screen on page load - minimal loading for performance."""
        self.load_settings()
        self.generate_qr_code()
        # Don't load photos/queues immediately - let user manually refresh
    
    def generate_qr_code(self):
        """Generate QR code for mobile interface."""
        self.mobile_url = get_mobile_url()
        self.qr_code_data_uri = generate_qr_code(self.mobile_url, size=120)
    
    def load_settings(self):
        """Load app settings from database."""
        self.party_title = get_setting("party_title", "50th Birthday Celebration")
        self.host_name = get_setting("host_name", "Birthday Star")
        self.slideshow_duration = int(get_setting("slideshow_duration", "10"))
    
    def load_photos(self):
        """Load processed photos for slideshow - optimized for performance."""
        with get_session() as session:
            # Limit to last 50 photos for better performance
            statement = select(Photo).where(
                Photo.is_processed == True
            ).order_by(desc(Photo.uploaded_at)).limit(50)
            
            photos = session.exec(statement).all()
            
            # Only rebuild list if photos changed
            new_photo_ids = [photo.id for photo in photos]
            current_photo_ids = [p.get("id") for p in self.photos]
            
            if new_photo_ids != current_photo_ids:
                self.photos = [
                    {
                        "id": photo.id,
                        "filename": photo.filename,
                        "guest_name": photo.guest_name,
                        "wish_message": photo.wish_message or "",
                        "display_duration": photo.display_duration,
                        "uploaded_at": photo.uploaded_at.strftime("%H:%M"),
                        "file_path": f"/uploads/{photo.filename}"
                    }
                    for photo in photos
                ]
    
    def load_queues(self):
        """Load photo and music queues - optimized."""
        with get_session() as session:
            # Photo queue - only top 6
            photo_statement = select(Photo).where(
                Photo.is_processed == True
            ).order_by(desc(Photo.uploaded_at)).limit(6)
            
            upcoming_photos = session.exec(photo_statement).all()
            
            # Use placeholder thumbnails to avoid file system overhead
            self.photo_queue = [
                {
                    "id": photo.id,
                    "filename": photo.filename,
                    "guest_name": photo.guest_name,
                    "thumbnail_path": f"/uploads/{photo.filename}",  # Direct path, no thumbnails
                    "uploaded_at": photo.uploaded_at.strftime("%H:%M")
                }
                for photo in upcoming_photos
            ]
            
            # Music queue - only top 5
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
        """Advance to next photo in slideshow."""
        if len(self.photos) > 0:
            self.current_photo_index = (self.current_photo_index + 1) % len(self.photos)
    
    def previous_photo(self):
        """Go to previous photo in slideshow."""
        if len(self.photos) > 0:
            self.current_photo_index = (self.current_photo_index - 1) % len(self.photos)
    
    def toggle_slideshow(self):
        """Toggle slideshow play/pause."""
        self.is_slideshow_active = not self.is_slideshow_active
    
    
    def refresh_content(self):
        """Manually refresh slideshow and queues."""
        self.is_loading = True
        self.load_photos()
        self.load_queues()
        self.is_loading = False
    
    def advance_slideshow(self):
        """Manually advance slideshow if active."""
        if self.is_slideshow_active and len(self.photos) > 0:
            self.next_photo()
    
    def update_volume(self, value: list[int | float]):
        """Update music volume."""
        if value:
            self.volume = value[0] / 100
    
    def toggle_music(self):
        """Toggle music play/pause."""
        self.is_playing = not self.is_playing
    
    @rx.var
    def photo_queue_count_text(self) -> str:
        """Photo queue count as text."""
        return f"{len(self.photo_queue)} photos queued"
    
    @rx.var
    def music_queue_count_text(self) -> str:
        """Music queue count as text."""
        return f"{len(self.music_queue)} songs queued"
    
    @rx.var
    def photo_counter_text(self) -> str:
        """Current photo counter as text."""
        if len(self.photos) == 0:
            return "0 / 0"
        return f"{self.current_photo_index + 1} / {len(self.photos)}"
    
    @rx.var
    def celebration_text(self) -> str:
        """Celebration header text."""
        return f"Celebrating {self.host_name}"


def slideshow_display() -> rx.Component:
    """Main photo slideshow display."""
    return rx.box(
        # Photo container
        rx.cond(
            BigScreenState.photos.length() > 0,
            rx.box(
                # Current photo
                rx.cond(
                    BigScreenState.photos.length() > BigScreenState.current_photo_index,
                    rx.image(
                        src=BigScreenState.photos[BigScreenState.current_photo_index]["file_path"],
                        alt="Current photo",
                        width="100%",
                        height="100%",
                        object_fit="contain",
                        class_name="slideshow-photo",
                    ),
                    rx.box()  # Empty box when no photo
                ),
                # Overlay with photo info
                rx.box(
                    rx.vstack(
                        rx.cond(
                            BigScreenState.photos.length() > BigScreenState.current_photo_index,
                            rx.hstack(
                                rx.avatar(
                                    name=BigScreenState.photos[BigScreenState.current_photo_index]["guest_name"],
                                    size="3"
                                ),
                                rx.vstack(
                                    rx.text(
                                        BigScreenState.photos[BigScreenState.current_photo_index]["guest_name"],
                                        size="4",
                                        weight="bold",
                                        color="white"
                                    ),
                                    rx.text(
                                        BigScreenState.photos[BigScreenState.current_photo_index]["uploaded_at"],
                                        size="2",
                                        color="rgba(255,255,255,0.8)"
                                    ),
                                    spacing="1",
                                    align="start"
                                ),
                                align="center",
                                spacing="3"
                            )
                        ),
                        # Wish message if present
                        rx.cond(
                            (BigScreenState.photos.length() > BigScreenState.current_photo_index) & 
                            (BigScreenState.photos[BigScreenState.current_photo_index]["wish_message"] != ""),
                            rx.box(
                                rx.text(
                                    BigScreenState.photos[BigScreenState.current_photo_index]["wish_message"],
                                    size="4",
                                    color="white",
                                    text_align="center",
                                    style={"font_style": "italic"}
                                ),
                                bg="rgba(0,0,0,0.6)",
                                border_radius="lg",
                                padding="4",
                                max_width="80%"
                            )
                        ),
                        spacing="4",
                        align="center"
                    ),
                    position="absolute",
                    bottom="4",
                    left="50%",
                    transform="translateX(-50%)",
                    bg="rgba(0,0,0,0.7)",
                    border_radius="xl",
                    padding="6",
                    min_width="300px",
                    class_name="photo-overlay visible"
                ),
                position="relative",
                width="100%",
                height="100%",
                bg="black"
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


def photo_queue_sidebar() -> rx.Component:
    """Photo queue sidebar showing upcoming photos."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.icon("images", size=20, color="blue.500"),
            rx.heading("Photo Queue", size="4", color="white"),
            align="center",
            spacing="2"
        ),
        
        # Queue items
        rx.scroll_area(
            rx.vstack(
                rx.foreach(
                    BigScreenState.photo_queue,
                    lambda photo: rx.card(
                        rx.hstack(
                            # Thumbnail
                            rx.image(
                                src=photo["thumbnail_path"],
                                alt=f"Photo by {photo['guest_name']}",
                                width="50px",
                                height="50px",
                                border_radius="md",
                                object_fit="cover"
                            ),
                            # Info
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
                        class_name="queue-item"
                    )
                ),
                spacing="2",
                width="100%"
            ),
            height="300px",
            class_name="queue-container"
        ),
        
        # Queue status
        rx.text(
            BigScreenState.photo_queue_count_text,
            size="2",
            color="gray.400",
            text_align="center"
        ),
        
        spacing="3",
        width="100%"
    )


def music_queue_sidebar() -> rx.Component:
    """Music queue sidebar showing upcoming songs."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.icon("music", size=20, color="green.500"),
            rx.heading("Music Queue", size="4", color="white"),
            align="center",
            spacing="2"
        ),
        
        # Queue items
        rx.scroll_area(
            rx.vstack(
                rx.foreach(
                    BigScreenState.music_queue,
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
                        class_name="queue-item"
                    )
                ),
                spacing="2",
                width="100%"
            ),
            height="250px",
            class_name="queue-container"
        ),
        
        # Queue status
        rx.text(
            BigScreenState.music_queue_count_text,
            size="2",
            color="gray.400",
            text_align="center"
        ),
        
        spacing="3",
        width="100%"
    )


def music_player_controls() -> rx.Component:
    """Music player controls and now playing display."""
    return rx.hstack(
        # Now playing info
        rx.hstack(
            rx.icon("music_2", size=20, color="green.500"),
            rx.vstack(
                rx.text(
                    rx.cond(
                        BigScreenState.current_song,
                        BigScreenState.current_song.get("title", "No song selected"),
                        "No song selected"
                    ),
                    size="3",
                    weight="bold",
                    color="white"
                ),
                rx.text(
                    rx.cond(
                        BigScreenState.current_song,
                        "Ready for music requests",
                        "Ready for music requests"
                    ),
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
        
        # Controls
        rx.hstack(
            rx.icon_button(
                rx.icon("skip_back", size=16),
                size="2",
                variant="ghost",
                color="white"
            ),
            rx.icon_button(
                rx.icon(
                    rx.cond(BigScreenState.is_playing, "pause", "play"),
                    size=20
                ),
                on_click=BigScreenState.toggle_music,
                size="3",
                variant="solid",
                color_scheme="green"
            ),
            rx.icon_button(
                rx.icon("skip_forward", size=16),
                size="2",
                variant="ghost",
                color="white"
            ),
            align="center",
            spacing="2",
            class_name="music-controls"
        ),
        
        # Volume control
        rx.hstack(
            rx.icon("volume_2", size=16, color="gray.400"),
            rx.slider(
                default_value=[BigScreenState.volume * 100],
                on_change=BigScreenState.update_volume,
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


def qr_code_display() -> rx.Component:
    """QR code for mobile interface access."""
    return rx.vstack(
        rx.heading("Join the Party!", size="5", color="white", text_align="center"),
        
        # QR code
        rx.box(
            rx.vstack(
                rx.cond(
                    BigScreenState.qr_code_data_uri != "",
                    rx.image(
                        src=BigScreenState.qr_code_data_uri,
                        alt="QR Code for mobile interface",
                        width="120px",
                        height="120px",
                        border_radius="md"
                    ),
                    # Placeholder while loading
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
            class_name="qr-container"
        ),
        
        spacing="3",
        align="center"
    )


def slideshow_controls() -> rx.Component:
    """Slideshow control buttons."""
    return rx.hstack(
        rx.icon_button(
            rx.icon("chevron_left", size=20),
            on_click=BigScreenState.previous_photo,
            size="3",
            variant="ghost",
            color="white"
        ),
        
        rx.icon_button(
            rx.icon(
                rx.cond(BigScreenState.is_slideshow_active, "pause", "play"),
                size=20
            ),
            on_click=BigScreenState.toggle_slideshow,
            size="3",
            variant="solid",
            color_scheme="blue"
        ),
        
        rx.icon_button(
            rx.icon("chevron_right", size=20),
            on_click=BigScreenState.next_photo,
            size="3",
            variant="ghost",
            color="white"
        ),
        
        rx.icon_button(
            rx.cond(
                BigScreenState.is_loading,
                rx.spinner(size="1"),
                rx.icon("refresh_cw", size=16)
            ),
            on_click=BigScreenState.refresh_content,
            size="2",
            variant="ghost",
            color="white",
            title="Refresh content",
            disabled=BigScreenState.is_loading
        ),
        
        rx.text(
            BigScreenState.photo_counter_text,
            size="2",
            color="gray.400"
        ),
        
        align="center",
        spacing="3"
    )


def big_screen_layout() -> rx.Component:
    """Complete big screen layout with all components."""
    return rx.box(
        # Header
        rx.hstack(
            rx.vstack(
                rx.heading(
                    BigScreenState.party_title,
                    size="8",
                    color="white",
                    weight="bold"
                ),
                rx.text(
                    BigScreenState.celebration_text,
                    size="4",
                    color="gray.300"
                ),
                spacing="1",
                align="start"
            ),
            rx.spacer(),
            qr_code_display(),
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
                slideshow_display(),
                width="75%",
                height="calc(100vh - 120px)",
                position="relative"
            ),
            
            # Right sidebar (25% width)
            rx.vstack(
                photo_queue_sidebar(),
                rx.divider(color="rgba(255,255,255,0.2)"),
                music_queue_sidebar(),
                spacing="4",
                width="25%",
                height="calc(100vh - 120px)",
                padding="4",
                bg="rgba(0,0,0,0.8)",
                overflow="hidden",
                class_name="sidebar"
            ),
            
            width="100%",
            height="calc(100vh - 120px)",
            spacing="0"
        ),
        
        # Bottom controls
        rx.hstack(
            slideshow_controls(),
            rx.spacer(),
            music_player_controls(),
            align="center",
            justify="between",
            width="100%",
            padding="4",
            bg="rgba(0,0,0,0.9)",
            border_top="1px solid rgba(255,255,255,0.1)",
            class_name="slideshow-controls"
        ),
        
        width="100vw",
        height="100vh",
        bg="black",
        overflow="hidden",
        on_mount=BigScreenState.on_load
    )