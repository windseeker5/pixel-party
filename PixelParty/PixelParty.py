"""Birthday Party Memory & Music App - Main Application."""

import reflex as rx
from components.mobile import mobile_interface, MobileState
from components.advanced_big_screen import advanced_big_screen_layout, AdvancedBigScreenState
from database.models import init_database

class State(rx.State):
    """The app state."""
    pass


def index() -> rx.Component:
    """Mobile guest interface - main entry point."""
    return mobile_interface()


def big_screen() -> rx.Component:
    """Advanced big screen slideshow interface."""
    return advanced_big_screen_layout()


def admin() -> rx.Component:
    """Admin panel for host management."""
    return rx.container(
        rx.vstack(
            rx.heading("🎛️ Admin Panel", size="8", text_align="center"),
            rx.text(
                "Host administration panel coming soon...",
                size="5",
                text_align="center",
                color="gray.600"
            ),
            rx.vstack(
                rx.card(
                    rx.text("📸 Manage Photos & Videos", size="4", weight="bold"),
                    rx.text("Review, approve, and organize submissions", size="3", color="gray.600"),
                    padding="4"
                ),
                rx.card(
                    rx.text("🎵 Music Queue", size="4", weight="bold"),
                    rx.text("Manage song requests and playlists", size="3", color="gray.600"),
                    padding="4"
                ),
                rx.card(
                    rx.text("⚙️ Settings", size="4", weight="bold"),
                    rx.text("Configure app behavior and preferences", size="3", color="gray.600"),
                    padding="4"
                ),
                spacing="4",
                width="100%",
                max_width="600px"
            ),
            spacing="6",
            justify="center",
            min_height="85vh",
        ),
    )


# Initialize database
init_database()

app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        accent_color="blue",
    ),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
        "https://cdn.jsdelivr.net/npm/animate.css@4.1.1/animate.min.css",
        "https://unpkg.com/aos@2.3.1/dist/aos.css",
        "https://unpkg.com/swiper@11/swiper-bundle.min.css",
    ],
    
    # Add external JavaScript libraries
    head_components=[
        rx.script(src="https://unpkg.com/aos@2.3.1/dist/aos.js"),
        rx.script(src="https://unpkg.com/swiper@11/swiper-bundle.min.js"),
        rx.script(src="/assets/animations.js", defer=True),
    ],
)

# Add pages
app.add_page(index, route="/", title="Birthday Party - Share Memories")
app.add_page(big_screen, route="/big-screen", title="Birthday Party - Big Screen")
app.add_page(admin, route="/admin", title="Birthday Party - Admin Panel")
