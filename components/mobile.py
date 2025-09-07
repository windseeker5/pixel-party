"""Mobile interface components for guest interactions."""

import reflex as rx
from typing import List, Optional


class MobileState(rx.State):
    """State management for mobile interface."""
    
    # Guest information
    guest_name: str = ""
    session_id: str = ""
    is_name_set: bool = False
    
    # Upload state
    uploaded_files: List[dict] = []
    upload_progress: int = 0
    is_uploading: bool = False
    upload_error: str = ""
    
    # Wish message
    wish_message: str = ""
    character_count: int = 0
    
    # Submission tracking
    total_submissions: int = 0
    max_submissions: int = 10
    
    # UI state
    show_success_message: bool = False
    current_view: str = "welcome"  # welcome, upload, success
    
    def set_guest_name(self, name: str):
        """Set the guest name and create session."""
        if name.strip():
            self.guest_name = name.strip()
            self.is_name_set = True
            self.current_view = "upload"
            # TODO: Create guest session in database
    
    def update_wish_message(self, message: str):
        """Update wish message and character count."""
        if len(message) <= 180:
            self.wish_message = message
            self.character_count = len(message)
    
    def clear_wish_message(self):
        """Clear the wish message."""
        self.wish_message = ""
        self.character_count = 0
    
    def reset_upload_state(self):
        """Reset upload related state."""
        self.upload_progress = 0
        self.is_uploading = False
        self.upload_error = ""
        self.uploaded_files = []
    
    def show_success(self):
        """Show success message."""
        self.show_success_message = True
        self.current_view = "success"
    
    def hide_success(self):
        """Hide success message."""
        self.show_success_message = False
        self.current_view = "upload"
        self.clear_wish_message()
        self.reset_upload_state()
    
    def can_submit(self) -> bool:
        """Check if user can submit more content."""
        return self.total_submissions < self.max_submissions


def welcome_screen() -> rx.Component:
    """Welcome screen with name entry."""
    return rx.vstack(
        # Party title and welcome message
        rx.vstack(
            rx.heading(
                "🎉 50th Birthday Celebration",
                size="8",
                text_align="center",
                color="blue.600"
            ),
            rx.text(
                "Share your photos, videos, and birthday wishes!",
                size="5",
                text_align="center",
                color="gray.700"
            ),
            spacing="3",
            align="center"
        ),
        
        # Name entry form
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("user", size=24, color="blue.600"),
                    rx.heading("Enter Your Name", size="6"),
                    align="center",
                    spacing="2"
                ),
                rx.text(
                    "Please enter your name to get started:",
                    size="4",
                    color="gray.600"
                ),
                rx.input(
                    placeholder="Your name...",
                    value=MobileState.guest_name,
                    on_change=MobileState.set_guest_name,
                    size="3",
                    width="100%"
                ),
                rx.button(
                    "Get Started",
                    on_click=lambda: MobileState.set_guest_name(MobileState.guest_name),
                    disabled=MobileState.guest_name.length() < 2,
                    size="3",
                    width="100%",
                    color_scheme="blue"
                ),
                spacing="4",
                align="stretch"
            ),
            width="100%",
            max_width="400px"
        ),
        
        spacing="8",
        align="center",
        justify="center",
        min_height="80vh",
        padding="4"
    )


def file_upload_component() -> rx.Component:
    """File upload component with drag and drop."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("camera", size=24, color="green.600"),
                rx.heading("Share a Photo or Video", size="5"),
                align="center",
                spacing="2"
            ),
            
            # Upload area
            rx.box(
                rx.vstack(
                    rx.cond(
                        MobileState.is_uploading,
                        rx.vstack(
                            rx.spinner(size="3"),
                            rx.text("Uploading...", size="3"),
                            rx.progress(value=MobileState.upload_progress, width="100%"),
                            spacing="2",
                            align="center"
                        ),
                        rx.vstack(
                            rx.icon("cloud_upload", size=32, color="gray.500"),
                            rx.text(
                                "Tap to select or drag files here",
                                size="3",
                                color="gray.600"
                            ),
                            rx.text(
                                "Max 50MB • Photos & Videos",
                                size="2",
                                color="gray.500"
                            ),
                            spacing="2",
                            align="center"
                        )
                    ),
                    align="center",
                    justify="center",
                    min_height="120px"
                ),
                border="2px dashed",
                border_color="gray.300",
                border_radius="md",
                padding="4",
                width="100%",
                _hover={"border_color": "blue.400"},
                cursor="pointer"
            ),
            
            # Error message
            rx.cond(
                MobileState.upload_error != "",
                rx.box(
                    rx.hstack(
                        rx.icon("triangle_alert", size=16, color="red.500"),
                        rx.text("Upload Error: ", size="3", weight="bold", color="red.600"),
                        rx.text(MobileState.upload_error, size="3", color="red.600"),
                        align="center",
                        spacing="2"
                    ),
                    bg="red.50",
                    border="1px solid",
                    border_color="red.200",
                    border_radius="md",
                    padding="3",
                    width="100%"
                )
            ),
            
            spacing="4",
            align="stretch"
        ),
        width="100%"
    )


def wish_message_component() -> rx.Component:
    """Birthday wish message input."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("heart", size=24, color="red.500"),
                rx.heading("Add a Birthday Wish", size="5"),
                align="center",
                spacing="2"
            ),
            
            rx.vstack(
                rx.text_area(
                    placeholder="Write a special birthday message...",
                    value=MobileState.wish_message,
                    on_change=MobileState.update_wish_message,
                    resize="vertical",
                    min_height="100px",
                    width="100%"
                ),
                rx.hstack(
                    rx.text(
                        f"{MobileState.character_count}/180 characters",
                        size="2",
                        color=rx.cond(
                            MobileState.character_count > 160,
                            "red.500",
                            "gray.500"
                        )
                    ),
                    rx.spacer(),
                    rx.button(
                        "Clear",
                        on_click=MobileState.clear_wish_message,
                        size="1",
                        variant="ghost",
                        disabled=MobileState.character_count == 0
                    ),
                    width="100%",
                    align="center"
                ),
                spacing="2",
                align="stretch"
            ),
            
            spacing="4",
            align="stretch"
        ),
        width="100%"
    )


def submission_summary() -> rx.Component:
    """Show submission summary and submit button."""
    return rx.card(
        rx.vstack(
            rx.heading("Ready to Share?", size="5", text_align="center"),
            
            # Summary
            rx.vstack(
                rx.cond(
                    MobileState.uploaded_files.length() > 0,
                    rx.hstack(
                        rx.icon("image", size=16, color="green.600"),
                        rx.text("Files selected"),
                        align="center",
                        spacing="2"
                    )
                ),
                rx.cond(
                    MobileState.wish_message != "",
                    rx.hstack(
                        rx.icon("heart", size=16, color="red.500"),
                        rx.text("Birthday wish included"),
                        align="center",
                        spacing="2"
                    )
                ),
                spacing="2",
                align="start"
            ),
            
            # Submit button
            rx.button(
                rx.hstack(
                    rx.icon("send", size=16),
                    rx.text("Share with Everyone!"),
                    align="center",
                    spacing="2"
                ),
                on_click=MobileState.show_success,
                size="3",
                width="100%",
                color_scheme="green",
                disabled=rx.cond(
                    (MobileState.uploaded_files.length() == 0) & (MobileState.wish_message == ""),
                    True,
                    False
                )
            ),
            
            # Submission count
            rx.text(
                f"Submissions: {MobileState.total_submissions}/{MobileState.max_submissions}",
                size="2",
                color="gray.500",
                text_align="center"
            ),
            
            spacing="4",
            align="stretch"
        ),
        width="100%"
    )


def success_message() -> rx.Component:
    """Success message after submission."""
    return rx.vstack(
        rx.card(
            rx.vstack(
                rx.icon("check_check", size=48, color="green.500"),
                rx.heading("Thank You!", size="7", color="green.600"),
                rx.text(
                    "Your photo and message have been shared!",
                    size="4",
                    text_align="center",
                    color="gray.700"
                ),
                rx.text(
                    "Watch the big screen to see your contribution appear in the slideshow.",
                    size="3",
                    text_align="center",
                    color="gray.600"
                ),
                spacing="4",
                align="center"
            ),
            width="100%",
            max_width="400px"
        ),
        
        rx.button(
            "Share Another",
            on_click=MobileState.hide_success,
            size="3",
            color_scheme="blue",
            disabled=MobileState.total_submissions >= MobileState.max_submissions
        ),
        
        spacing="6",
        align="center",
        justify="center",
        min_height="60vh",
        padding="4"
    )


def upload_interface() -> rx.Component:
    """Main upload interface for guests."""
    return rx.vstack(
        # Header with guest name
        rx.card(
            rx.hstack(
                rx.avatar(
                    name=MobileState.guest_name,
                    size="2"
                ),
                rx.vstack(
                    rx.text(f"Welcome, {MobileState.guest_name}!", size="4", weight="bold"),
                    rx.text("Share your memories below", size="2", color="gray.600"),
                    spacing="1",
                    align="start"
                ),
                align="center",
                spacing="3",
                width="100%"
            ),
            width="100%"
        ),
        
        # Upload components
        file_upload_component(),
        wish_message_component(),
        submission_summary(),
        
        spacing="4",
        width="100%",
        max_width="500px",
        padding="4"
    )


def mobile_interface() -> rx.Component:
    """Main mobile interface with conditional views."""
    return rx.container(
        rx.cond(
            MobileState.current_view == "welcome",
            welcome_screen(),
            rx.cond(
                MobileState.current_view == "upload",
                upload_interface(),
                rx.cond(
                    MobileState.current_view == "success",
                    success_message(),
                    welcome_screen()  # fallback
                )
            )
        ),
        width="100%",
        max_width="600px",
        margin="0 auto",
        min_height="100vh",
        bg="gray.50"
    )