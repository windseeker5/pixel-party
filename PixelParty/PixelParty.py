"""Birthday Party Memory & Music App - Main Application."""

import reflex as rx
from components.mobile import mobile_interface, MobileState
from components.big_screen import big_screen_layout, BigScreenState
from database.models import init_database

class State(rx.State):
    """The app state."""
    pass


def index() -> rx.Component:
    """Mobile guest interface - main entry point."""
    return mobile_interface()


def big_screen() -> rx.Component:
    """Big screen slideshow interface."""
    return big_screen_layout()


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
    ],
)

# Add pages
app.add_page(index, route="/", title="Birthday Party - Share Memories")
app.add_page(big_screen, route="/big-screen", title="Birthday Party - Big Screen")
app.add_page(admin, route="/admin", title="Birthday Party - Admin Panel")
