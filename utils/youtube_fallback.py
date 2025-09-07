"""YouTube fallback system using yt-dlp for missing songs."""

import os
import asyncio
import subprocess
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import logging
import tempfile
from urllib.parse import quote_plus
from sqlmodel import Session
from database.models import MusicLibrary, get_session
from utils.music_library import music_search

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Handles YouTube audio downloads using yt-dlp."""
    
    def __init__(self, download_dir: str = "./music_library_demo/Downloaded/"):
        self.download_dir = Path(download_dir)
        try:
            self.download_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fallback to a temporary directory
            import tempfile
            self.download_dir = Path(tempfile.gettempdir()) / "pixelparty_music"
            self.download_dir.mkdir(parents=True, exist_ok=True)
        
    async def search_youtube(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search YouTube for songs matching query."""
        try:
            # Use yt-dlp to search YouTube
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-download',
                '--playlist-end', str(max_results),
                f'ytsearch{max_results}:{query}'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"yt-dlp search failed: {stderr.decode()}")
                return []
            
            # Parse results
            results = []
            for line in stdout.decode().strip().split('\n'):
                if line:
                    try:
                        video_info = json.loads(line)
                        results.append({
                            'id': video_info.get('id', ''),
                            'title': video_info.get('title', ''),
                            'uploader': video_info.get('uploader', ''),
                            'duration': video_info.get('duration', 0),
                            'url': video_info.get('webpage_url', ''),
                            'thumbnail': video_info.get('thumbnail', ''),
                            'description': video_info.get('description', '')[:200] + '...' if video_info.get('description', '') else ''
                        })
                    except json.JSONDecodeError:
                        continue
            
            logger.info(f"Found {len(results)} YouTube results for: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            return []
    
    async def download_audio(self, video_id: str, title: str = None, artist: str = None) -> Optional[Dict]:
        """Download audio from YouTube video."""
        try:
            # Generate filename
            if title and artist:
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_artist = "".join(c for c in artist if c.isalnum() or c in (' ', '-', '_')).strip()
                filename = f"{safe_artist} - {safe_title}"
            else:
                filename = f"youtube_{video_id}"
            
            # Ensure unique filename
            counter = 1
            base_filename = filename
            output_path = self.download_dir / f"{filename}.%(ext)s"
            
            while (self.download_dir / f"{filename}.mp3").exists():
                filename = f"{base_filename}_{counter}"
                counter += 1
                output_path = self.download_dir / f"{filename}.%(ext)s"
            
            # Download command
            cmd = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '192K',
                '--output', str(output_path),
                '--no-playlist',
                '--ignore-errors',
                f'https://www.youtube.com/watch?v={video_id}'
            ]
            
            logger.info(f"Downloading: {video_id}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Download failed: {stderr.decode()}")
                return None
            
            # Find the downloaded file
            mp3_file = self.download_dir / f"{filename}.mp3"
            if mp3_file.exists():
                # Add to music library
                await self._add_to_library(mp3_file, title, artist, video_id)
                
                return {
                    'success': True,
                    'file_path': str(mp3_file),
                    'title': title or filename,
                    'artist': artist or 'YouTube',
                    'source': 'youtube'
                }
            else:
                logger.error(f"Downloaded file not found: {mp3_file}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading from YouTube: {e}")
            return None
    
    async def _add_to_library(self, file_path: Path, title: str = None, artist: str = None, youtube_id: str = None):
        """Add downloaded file to music library."""
        try:
            # Extract metadata if not provided
            if not title:
                title = file_path.stem
                
            if not artist:
                artist = "YouTube Download"
            
            file_size = file_path.stat().st_size
            
            # Add to database
            with get_session() as session:
                music_record = MusicLibrary(
                    filename=file_path.name,
                    title=title,
                    artist=artist,
                    album="YouTube Downloads",
                    genre="Downloaded",
                    duration=0,  # Will be updated by indexer
                    file_path=str(file_path),
                    file_size=file_size
                )
                
                session.add(music_record)
                session.commit()
                
            logger.info(f"Added to library: {title} by {artist}")
            
        except Exception as e:
            logger.error(f"Error adding to library: {e}")


class MusicResolver:
    """Resolves music requests using local library first, then YouTube fallback."""
    
    def __init__(self, youtube_downloader: YouTubeDownloader):
        self.youtube_downloader = youtube_downloader
    
    async def find_song(self, title: str, artist: str = None, auto_download: bool = True) -> Optional[Dict]:
        """Find song in local library or YouTube."""
        
        # First, search local library
        local_results = await self._search_local(title, artist)
        if local_results:
            logger.info(f"Found locally: {title} by {artist}")
            return {
                'source': 'local',
                'track': local_results[0],
                'file_path': local_results[0]['file_path']
            }
        
        # If not found locally, search YouTube
        if auto_download:
            return await self._search_and_download_youtube(title, artist)
        else:
            youtube_results = await self.youtube_downloader.search_youtube(
                f"{artist} {title}" if artist else title
            )
            
            if youtube_results:
                return {
                    'source': 'youtube_search',
                    'results': youtube_results[:3],  # Top 3 results
                    'query': f"{artist} {title}" if artist else title
                }
        
        return None
    
    async def _search_local(self, title: str, artist: str = None) -> List[Dict]:
        """Search local music library."""
        try:
            if artist:
                # Search by title and artist
                query = f"{title} {artist}"
                results = music_search.search_all(query, limit=5)
            else:
                # Search by title only
                results = music_search.search_by_title(title, limit=5)
            
            # Filter results for better matches
            if artist:
                # Prefer results where artist matches
                artist_matches = [r for r in results if artist.lower() in r['artist'].lower()]
                if artist_matches:
                    return artist_matches
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching local library: {e}")
            return []
    
    async def _search_and_download_youtube(self, title: str, artist: str = None) -> Optional[Dict]:
        """Search YouTube and download the best match."""
        try:
            query = f"{artist} {title}" if artist else title
            youtube_results = await self.youtube_downloader.search_youtube(query, max_results=3)
            
            if not youtube_results:
                logger.warning(f"No YouTube results for: {query}")
                return None
            
            # Try to find the best match
            best_match = youtube_results[0]  # Start with first result
            
            if artist and title:
                # Look for better matches based on title/artist
                for result in youtube_results:
                    result_title = result['title'].lower()
                    if (title.lower() in result_title and 
                        artist.lower() in result_title):
                        best_match = result
                        break
            
            # Download the best match
            logger.info(f"Downloading from YouTube: {best_match['title']}")
            download_result = await self.youtube_downloader.download_audio(
                best_match['id'], 
                title, 
                artist
            )
            
            if download_result:
                return {
                    'source': 'youtube_downloaded',
                    'track': download_result,
                    'file_path': download_result['file_path'],
                    'youtube_info': best_match
                }
            
        except Exception as e:
            logger.error(f"Error with YouTube fallback: {e}")
        
        return None
    
    async def download_from_youtube_result(self, youtube_result: Dict, title: str = None, artist: str = None) -> Optional[Dict]:
        """Download a specific YouTube result."""
        download_result = await self.youtube_downloader.download_audio(
            youtube_result['id'],
            title or youtube_result['title'],
            artist
        )
        
        if download_result:
            return {
                'source': 'youtube_downloaded',
                'track': download_result,
                'file_path': download_result['file_path'],
                'youtube_info': youtube_result
            }
        
        return None


# Global instances
youtube_downloader = YouTubeDownloader()
music_resolver = MusicResolver(youtube_downloader)