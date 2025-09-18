"""Music library search functionality."""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from app.models import MusicLibrary
from app import db

class MusicSearch:
    """Simple music search functionality for local library."""
    
    def search_all(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search across all fields in the music library (case-insensitive)."""
        try:
            # Convert search term to lowercase for case-insensitive search
            search_term = f"%{query.lower()}%"
            
            # Search using lowercase fields for true case-insensitive matching
            results = MusicLibrary.query.filter(
                db.or_(
                    MusicLibrary.title_lower.like(search_term),
                    MusicLibrary.artist_lower.like(search_term),
                    MusicLibrary.album_lower.like(search_term),
                    MusicLibrary.genre_lower.like(search_term)
                )
            ).all()
            
            # Remove duplicates by creating a unique key (title + duration)
            seen_songs = {}
            unique_results = []

            for result in results:
                # Create unique key using lowercase title and duration
                # This catches artist variations like "R.E.M." vs "REM" for same song
                unique_key = f"{result.title_lower}|||{result.duration}"

                if unique_key not in seen_songs:
                    seen_songs[unique_key] = True
                    unique_results.append(result)
                    
                    # Stop when we have enough unique results
                    if len(unique_results) >= limit:
                        break
            
            return [self._format_result(result) for result in unique_results]
        except Exception as e:
            print(f"Error in search_all: {e}")
            return []
    
    def search_by_title(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search by song title (case-insensitive)."""
        try:
            search_term = f"%{query.lower()}%"
            results = MusicLibrary.query.filter(
                MusicLibrary.title_lower.like(search_term)
            ).limit(limit).all()
            
            return [self._format_result(result) for result in results]
        except Exception as e:
            print(f"Error in search_by_title: {e}")
            return []
    
    def search_by_artist(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search by artist name (case-insensitive)."""
        try:
            search_term = f"%{query.lower()}%"
            results = MusicLibrary.query.filter(
                MusicLibrary.artist_lower.like(search_term)
            ).limit(limit).all()
            
            return [self._format_result(result) for result in results]
        except Exception as e:
            print(f"Error in search_by_artist: {e}")
            return []
    
    def search_by_album(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search by album name (case-insensitive)."""
        try:
            search_term = f"%{query.lower()}%"
            results = MusicLibrary.query.filter(
                MusicLibrary.album_lower.like(search_term)
            ).limit(limit).all()
            
            return [self._format_result(result) for result in results]
        except Exception as e:
            print(f"Error in search_by_album: {e}")
            return []
    
    def get_library_stats(self) -> Dict[str, Any]:
        """Get music library statistics."""
        try:
            total_tracks = MusicLibrary.query.count()
            
            if total_tracks == 0:
                return {
                    'total_tracks': 0,
                    'total_artists': 0,
                    'total_albums': 0,
                    'total_duration': 0,
                    'total_size': 0
                }
            
            # Get all records for detailed stats
            all_tracks = MusicLibrary.query.all()
            
            # Calculate unique counts (excluding 'Unknown' values)
            unique_artists = len(set(track.artist for track in all_tracks 
                                   if track.artist and track.artist != 'Unknown'))
            unique_albums = len(set(track.album for track in all_tracks 
                                  if track.album and track.album != 'Unknown'))
            
            # Calculate totals
            total_duration = sum(track.duration or 0 for track in all_tracks)
            total_size = sum(track.file_size or 0 for track in all_tracks)
            
            return {
                'total_tracks': total_tracks,
                'total_artists': unique_artists,
                'total_albums': unique_albums,
                'total_duration': total_duration,
                'total_size': total_size
            }
            
        except Exception as e:
            print(f"Error getting library stats: {e}")
            return {
                'total_tracks': 0,
                'total_artists': 0,
                'total_albums': 0,
                'total_duration': 0,
                'total_size': 0
            }
    
    def _format_result(self, music_record: MusicLibrary) -> Dict[str, Any]:
        """Format a MusicLibrary record for API response."""
        # Convert duration from seconds to MM:SS format
        duration_str = "0:00"
        if music_record.duration:
            minutes = music_record.duration // 60
            seconds = music_record.duration % 60
            duration_str = f"{minutes}:{seconds:02d}"
        
        return {
            'id': music_record.id,
            'title': music_record.title or 'Unknown Title',
            'artist': music_record.artist or 'Unknown Artist',
            'album': music_record.album or '',
            'genre': music_record.genre or '',
            'duration': music_record.duration or 0,
            'duration_formatted': duration_str,
            'file_path': music_record.file_path,  # Use the correct field name from the model
            'source': 'local'
        }

# Create global instance for easy import
music_search = MusicSearch()