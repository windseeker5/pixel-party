"""Database models for Birthday Party Memory & Music App - PRD Schema."""

import datetime
from app import db


class Guest(db.Model):
    """Users/Guests table."""
    __tablename__ = 'guests'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # First name or full name
    session_id = db.Column(db.String(255), unique=True, index=True, nullable=False)
    first_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    total_submissions = db.Column(db.Integer, default=0)
    
    # Relationships
    photos = db.relationship('Photo', backref='guest', lazy=True)
    music_requests = db.relationship('MusicQueue', backref='guest', lazy=True)


class Photo(db.Model):
    """Photo submissions with wishes."""
    __tablename__ = 'photos'
    
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'), nullable=True)
    guest_name = db.Column(db.String(100), nullable=False)  # Stored for easy access
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    wish_message = db.Column(db.String(140), nullable=False)  # Birthday wish/note (max 140 chars)
    uploaded_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    displayed_at = db.Column(db.DateTime, nullable=True)
    display_duration = db.Column(db.Integer, default=10)  # Seconds to show on screen
    file_size = db.Column(db.Integer, default=0)  # bytes


class MusicQueue(db.Model):
    """Music submissions."""
    __tablename__ = 'music_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'), nullable=True)
    song_title = db.Column(db.String(200), nullable=True)
    artist = db.Column(db.String(200), nullable=True)
    album = db.Column(db.String(200), nullable=True)
    filename = db.Column(db.String(255), nullable=True)
    source = db.Column(db.String(20), nullable=False)  # 'local' or 'youtube'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'downloading', 'ready', 'error'
    played_at = db.Column(db.DateTime, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class MusicLibrary(db.Model):
    """Local music library index."""
    __tablename__ = 'music_library'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    artist = db.Column(db.String(200), nullable=True)
    album = db.Column(db.String(200), nullable=True)
    genre = db.Column(db.String(100), nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # seconds
    file_path = db.Column(db.String(500), nullable=False, unique=True, index=True)
    file_size = db.Column(db.Integer, default=0)
    indexed_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Lowercase fields for case-insensitive search
    title_lower = db.Column(db.String(200), nullable=True, index=True)
    artist_lower = db.Column(db.String(200), nullable=True, index=True)
    album_lower = db.Column(db.String(200), nullable=True, index=True)
    genre_lower = db.Column(db.String(100), nullable=True, index=True)
    
    # File modification tracking for incremental updates
    file_modified_at = db.Column(db.DateTime, nullable=True)
    
    # Index status tracking
    index_status = db.Column(db.String(20), default='indexed')  # 'indexed', 'error', 'missing'
    index_error = db.Column(db.Text, nullable=True)
    
    # Composite index for search performance
    __table_args__ = (
        db.Index('idx_music_search', 'title_lower', 'artist_lower', 'album_lower'),
    )


class Settings(db.Model):
    """App settings."""
    __tablename__ = 'settings'
    
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


def init_default_settings():
    """Initialize default settings if they don't exist."""
    default_settings = [
        ('slideshow_duration', '8'),
        ('max_file_size', '52428800'),
        ('max_submissions_per_guest', '10'),
        ('auto_play_music', 'true'),
        ('party_title', '50th Birthday Celebration'),
        ('host_name', 'Birthday Star'),
        ('welcome_screen_interval_type', 'photos'),
        ('welcome_screen_interval_value', '5'),
        ('welcome_screen_duration', '8'),
        ('enable_ai_suggestions', 'true'),
    ]
    
    for key, value in default_settings:
        existing = Settings.query.filter_by(key=key).first()
        if not existing:
            setting = Settings(key=key, value=value)
            db.session.add(setting)
    
    db.session.commit()


def get_setting(key, default=None):
    """Get a setting value by key."""
    setting = Settings.query.filter_by(key=key).first()
    return setting.value if setting else default


def update_setting(key, value):
    """Update a setting value."""
    setting = Settings.query.filter_by(key=key).first()
    if setting:
        setting.value = value
        setting.updated_at = datetime.datetime.utcnow()
    else:
        setting = Settings(key=key, value=value)
        db.session.add(setting)
    
    db.session.commit()