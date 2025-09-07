"""Database models for Birthday Party Memory & Music App."""

import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Session, select, text


class Guest(SQLModel, table=True):
    """Guest table for managing user sessions and submissions."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    session_id: str = Field(unique=True, index=True)
    first_seen: datetime.datetime = Field(default_factory=datetime.datetime.now)
    total_submissions: int = Field(default=0)


class Photo(SQLModel, table=True):
    """Photos and videos uploaded by guests."""
    id: Optional[int] = Field(default=None, primary_key=True)
    guest_id: Optional[int] = Field(foreign_key="guest.id")
    guest_name: str = Field(max_length=100)
    filename: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    wish_message: Optional[str] = Field(max_length=180, default=None)
    uploaded_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    display_duration: int = Field(default=5)  # seconds
    file_size: int = Field(default=0)  # bytes
    is_processed: bool = Field(default=False)


class MusicQueue(SQLModel, table=True):
    """Music queue for requested songs."""
    id: Optional[int] = Field(default=None, primary_key=True)
    guest_id: Optional[int] = Field(foreign_key="guest.id")
    guest_name: str = Field(max_length=100)
    title: str = Field(max_length=200)
    artist: str = Field(max_length=200)
    album: Optional[str] = Field(max_length=200, default=None)
    source: str = Field(max_length=20)  # "local" or "youtube"
    source_path: Optional[str] = Field(max_length=500, default=None)
    youtube_url: Optional[str] = Field(max_length=500, default=None)
    requested_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    played_at: Optional[datetime.datetime] = Field(default=None)
    is_played: bool = Field(default=False)
    mood_tag: Optional[str] = Field(max_length=50, default=None)


class MusicLibrary(SQLModel, table=True):
    """Local music library index."""
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(max_length=255, unique=True)
    title: str = Field(max_length=200)
    artist: str = Field(max_length=200)
    album: Optional[str] = Field(max_length=200, default=None)
    genre: Optional[str] = Field(max_length=100, default=None)
    duration: Optional[int] = Field(default=None)  # seconds
    file_path: str = Field(max_length=500)
    file_size: int = Field(default=0)
    date_added: datetime.datetime = Field(default_factory=datetime.datetime.now)
    play_count: int = Field(default=0)
    last_played: Optional[datetime.datetime] = Field(default=None)


class Settings(SQLModel, table=True):
    """App configuration settings."""
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(max_length=100, unique=True, index=True)
    value: str = Field(max_length=1000)
    description: Optional[str] = Field(max_length=255, default=None)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


# Database connection and initialization
DATABASE_URL = "sqlite:///./birthday_party.db"
engine = create_engine(DATABASE_URL, echo=False)


def init_database():
    """Initialize database tables."""
    SQLModel.metadata.create_all(engine)
    
    # Initialize default settings
    with Session(engine) as session:
        # Check if settings already exist
        existing_settings = session.exec(
            select(Settings)
        ).all()
        
        if len(existing_settings) == 0:
            default_settings = [
                Settings(
                    key="slideshow_duration", 
                    value="5", 
                    description="Default photo display duration in seconds"
                ),
                Settings(
                    key="max_file_size", 
                    value="52428800", 
                    description="Maximum file upload size in bytes (50MB)"
                ),
                Settings(
                    key="max_submissions_per_guest", 
                    value="10", 
                    description="Maximum number of submissions per guest"
                ),
                Settings(
                    key="auto_play_music", 
                    value="true", 
                    description="Auto play queued music"
                ),
                Settings(
                    key="party_title", 
                    value="50th Birthday Celebration", 
                    description="Party title displayed on screens"
                ),
                Settings(
                    key="host_name", 
                    value="Birthday Star", 
                    description="Host name for the celebration"
                ),
            ]
            
            for setting in default_settings:
                session.add(setting)
            
            session.commit()
    
    print("Database initialized successfully!")


def get_session():
    """Get database session."""
    return Session(engine)


def get_setting(key: str, default: str = None) -> str:
    """Get a setting value by key."""
    with get_session() as session:
        statement = select(Settings).where(Settings.key == key)
        setting = session.exec(statement).first()
        return setting.value if setting else default


def update_setting(key: str, value: str):
    """Update a setting value."""
    with get_session() as session:
        statement = select(Settings).where(Settings.key == key)
        setting = session.exec(statement).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.datetime.now()
        else:
            setting = Settings(key=key, value=value)
            session.add(setting)
        
        session.commit()