"""Music library indexing and management system."""

import os
import asyncio
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sqlite3
from mutagen import File
from mutagen.id3 import ID3NoHeaderError
from sqlmodel import Session, select
from database.models import MusicLibrary, get_session
import logging

# Supported audio formats
SUPPORTED_FORMATS = {
    '.mp3', '.flac', '.m4a', '.ogg', '.wav', '.aac', '.wma'
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MusicLibraryIndexer:
    """Handles indexing of the local music library."""
    
    def __init__(self, library_path: str = "./music_library_demo/"):
        self.library_path = Path(library_path)
        self.indexed_count = 0
        self.error_count = 0
        self.total_files = 0
        
    def get_audio_metadata(self, file_path: Path) -> Optional[Dict]:
        """Extract metadata from audio file using mutagen."""
        try:
            audio_file = File(str(file_path))
            if audio_file is None:
                return None
                
            metadata = {
                'filename': file_path.name,
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
                'title': '',
                'artist': '',
                'album': '',
                'genre': '',
                'duration': 0
            }
            
            # Extract common metadata fields
            if 'TIT2' in audio_file:  # Title for ID3
                metadata['title'] = str(audio_file['TIT2'])
            elif 'TITLE' in audio_file:  # Title for other formats
                metadata['title'] = str(audio_file['TITLE'][0])
            elif hasattr(audio_file, 'title') and audio_file.title:
                metadata['title'] = str(audio_file.title[0])
                
            if 'TPE1' in audio_file:  # Artist for ID3
                metadata['artist'] = str(audio_file['TPE1'])
            elif 'ARTIST' in audio_file:  # Artist for other formats
                metadata['artist'] = str(audio_file['ARTIST'][0])
            elif hasattr(audio_file, 'artist') and audio_file.artist:
                metadata['artist'] = str(audio_file.artist[0])
                
            if 'TALB' in audio_file:  # Album for ID3
                metadata['album'] = str(audio_file['TALB'])
            elif 'ALBUM' in audio_file:  # Album for other formats
                metadata['album'] = str(audio_file['ALBUM'][0])
            elif hasattr(audio_file, 'album') and audio_file.album:
                metadata['album'] = str(audio_file.album[0])
                
            if 'TCON' in audio_file:  # Genre for ID3
                metadata['genre'] = str(audio_file['TCON'])
            elif 'GENRE' in audio_file:  # Genre for other formats
                metadata['genre'] = str(audio_file['GENRE'][0])
            elif hasattr(audio_file, 'genre') and audio_file.genre:
                metadata['genre'] = str(audio_file.genre[0])
                
            # Get duration in seconds
            if hasattr(audio_file, 'info') and audio_file.info:
                metadata['duration'] = int(audio_file.info.length)
                
            # Fallback to filename if no title
            if not metadata['title']:
                metadata['title'] = file_path.stem
                
            # Fallback to "Unknown" for empty fields
            for field in ['artist', 'album', 'genre']:
                if not metadata[field]:
                    metadata[field] = 'Unknown'
                    
            return metadata
            
        except (ID3NoHeaderError, Exception) as e:
            logger.warning(f"Error reading metadata from {file_path}: {e}")
            return None
    
    def scan_directory(self, directory: Path) -> List[Path]:
        """Recursively scan directory for audio files."""
        audio_files = []
        
        if not directory.exists():
            logger.error(f"Music library directory does not exist: {directory}")
            return audio_files
            
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
                    audio_files.append(file_path)
                    
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
            
        return audio_files
    
    def index_library(self, force_reindex: bool = False) -> Dict:
        """Index the entire music library."""
        logger.info(f"Starting music library indexing: {self.library_path}")
        
        # Check if library exists
        if not self.library_path.exists():
            logger.error(f"Music library path does not exist: {self.library_path}")
            return {
                'success': False,
                'error': f'Music library path does not exist: {self.library_path}',
                'indexed': 0,
                'errors': 0,
                'total': 0
            }
        
        # Scan for audio files
        logger.info("Scanning for audio files...")
        audio_files = self.scan_directory(self.library_path)
        self.total_files = len(audio_files)
        
        logger.info(f"Found {self.total_files} audio files")
        
        if self.total_files == 0:
            return {
                'success': True,
                'message': 'No audio files found in library',
                'indexed': 0,
                'errors': 0,
                'total': 0
            }
        
        # Get existing files from database
        existing_files = set()
        if not force_reindex:
            with get_session() as session:
                existing_records = session.exec(select(MusicLibrary.file_path)).all()
                existing_files = set(existing_records)
        
        # Process files
        batch_size = 100
        current_batch = []
        
        for file_path in audio_files:
            # Skip if already indexed and not forcing reindex
            if not force_reindex and str(file_path) in existing_files:
                continue
                
            metadata = self.get_audio_metadata(file_path)
            if metadata:
                current_batch.append(metadata)
                
                # Process batch when full
                if len(current_batch) >= batch_size:
                    self._save_batch(current_batch, force_reindex)
                    current_batch = []
            else:
                self.error_count += 1
        
        # Process remaining batch
        if current_batch:
            self._save_batch(current_batch, force_reindex)
        
        logger.info(f"Indexing complete: {self.indexed_count} indexed, {self.error_count} errors")
        
        return {
            'success': True,
            'indexed': self.indexed_count,
            'errors': self.error_count,
            'total': self.total_files
        }
    
    def _save_batch(self, batch: List[Dict], force_reindex: bool = False):
        """Save a batch of music records to database."""
        try:
            with get_session() as session:
                for metadata in batch:
                    # Check if file already exists
                    if not force_reindex:
                        existing = session.exec(
                            select(MusicLibrary).where(
                                MusicLibrary.file_path == metadata['file_path']
                            )
                        ).first()
                        
                        if existing:
                            continue
                    else:
                        # Delete existing record if force reindexing
                        existing = session.exec(
                            select(MusicLibrary).where(
                                MusicLibrary.file_path == metadata['file_path']
                            )
                        ).first()
                        
                        if existing:
                            session.delete(existing)
                    
                    # Create new record
                    music_record = MusicLibrary(
                        filename=metadata['filename'],
                        title=metadata['title'],
                        artist=metadata['artist'],
                        album=metadata['album'],
                        genre=metadata['genre'],
                        duration=metadata['duration'],
                        file_path=metadata['file_path'],
                        file_size=metadata['file_size']
                    )
                    
                    session.add(music_record)
                    self.indexed_count += 1
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Error saving batch to database: {e}")
            self.error_count += len(batch)


class MusicSearchEngine:
    """Handles searching through the indexed music library."""
    
    def __init__(self):
        pass
    
    def search_by_title(self, query: str, limit: int = 20) -> List[Dict]:
        """Search music by title."""
        with get_session() as session:
            statement = select(MusicLibrary).where(
                MusicLibrary.title.ilike(f"%{query}%")
            ).limit(limit)
            
            results = session.exec(statement).all()
            
            return [self._format_result(track) for track in results]
    
    def search_by_artist(self, query: str, limit: int = 20) -> List[Dict]:
        """Search music by artist."""
        with get_session() as session:
            statement = select(MusicLibrary).where(
                MusicLibrary.artist.ilike(f"%{query}%")
            ).limit(limit)
            
            results = session.exec(statement).all()
            
            return [self._format_result(track) for track in results]
    
    def search_by_album(self, query: str, limit: int = 20) -> List[Dict]:
        """Search music by album."""
        with get_session() as session:
            statement = select(MusicLibrary).where(
                MusicLibrary.album.ilike(f"%{query}%")
            ).limit(limit)
            
            results = session.exec(statement).all()
            
            return [self._format_result(track) for track in results]
    
    def search_all(self, query: str, limit: int = 20) -> List[Dict]:
        """Search across all fields."""
        with get_session() as session:
            statement = select(MusicLibrary).where(
                (MusicLibrary.title.ilike(f"%{query}%")) |
                (MusicLibrary.artist.ilike(f"%{query}%")) |
                (MusicLibrary.album.ilike(f"%{query}%")) |
                (MusicLibrary.genre.ilike(f"%{query}%"))
            ).limit(limit)
            
            results = session.exec(statement).all()
            
            return [self._format_result(track) for track in results]
    
    def get_random_tracks(self, limit: int = 10) -> List[Dict]:
        """Get random tracks from library."""
        with get_session() as session:
            # SQLite random function
            statement = select(MusicLibrary).order_by("RANDOM()").limit(limit)
            results = session.exec(statement).all()
            
            return [self._format_result(track) for track in results]
    
    def get_library_stats(self) -> Dict:
        """Get music library statistics."""
        with get_session() as session:
            total_tracks = session.exec(select(MusicLibrary)).all()
            
            if not total_tracks:
                return {
                    'total_tracks': 0,
                    'total_artists': 0,
                    'total_albums': 0,
                    'total_duration': 0,
                    'total_size': 0
                }
            
            unique_artists = set(track.artist for track in total_tracks if track.artist != 'Unknown')
            unique_albums = set(track.album for track in total_tracks if track.album != 'Unknown')
            total_duration = sum(track.duration or 0 for track in total_tracks)
            total_size = sum(track.file_size or 0 for track in total_tracks)
            
            return {
                'total_tracks': len(total_tracks),
                'total_artists': len(unique_artists),
                'total_albums': len(unique_albums),
                'total_duration': total_duration,  # seconds
                'total_size': total_size  # bytes
            }
    
    def _format_result(self, track: MusicLibrary) -> Dict:
        """Format database result for display."""
        return {
            'id': track.id,
            'title': track.title,
            'artist': track.artist,
            'album': track.album,
            'genre': track.genre,
            'duration': track.duration,
            'file_path': track.file_path,
            'file_size': track.file_size,
            'duration_formatted': self._format_duration(track.duration)
        }
    
    def _format_duration(self, seconds: Optional[int]) -> str:
        """Format duration in seconds to MM:SS format."""
        if not seconds:
            return "0:00"
        
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"


# Global instances
music_indexer = MusicLibraryIndexer()
music_search = MusicSearchEngine()