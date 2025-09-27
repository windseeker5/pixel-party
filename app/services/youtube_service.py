"""YouTube search and download service for music fallback."""

import os
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
import yt_dlp
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2, TDRC, TCON
import re
import traceback
import sys

# Enhanced logging configuration for debugging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler if not exists
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.propagate = False


class YouTubeAudioService:
    """Service for searching and downloading audio from YouTube."""
    
    def __init__(self, output_dir: str = None):
        """Initialize with output directory for downloads."""
        from flask import current_app
        if output_dir is None:
            output_dir = current_app.config.get('MUSIC_COPY_FOLDER', 'media/music')
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure yt-dlp options for audio extraction
        self.ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'noplaylist': True,
            'no_warnings': False,  # Enable warnings to see what's happening
            'quiet': False,        # Disable quiet mode for debugging
            'no_color': True,
            'writethumbnail': False,
            'writeinfojson': False,
            'ignoreerrors': False,  # Don't ignore errors, we want to see them
            'extract_flat': False,
            # Add headers to avoid 403 errors
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                },
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                }
            ]
        }
    
    def search_youtube(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search YouTube for music videos and return metadata.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of dictionaries with video metadata
        """
        logger.info(f"🎵 Starting YouTube search: query='{query}', max_results={max_results}")
        search_results = []

        try:
            # Use proper ytsearch syntax for yt-dlp with "music video" for better results
            search_query = f"ytsearch{max_results * 3}:{query} music video"
            
            search_opts = {
                'quiet': True,
                'no_warnings': True,
                'no_color': True,
                'extract_flat': True,
                'flat_playlist': True,
            }
            
            logger.info(f"Searching YouTube for: {query}")
            
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                search_info = ydl.extract_info(search_query, download=False)
                
                if not search_info:
                    logger.warning(f"No search info for query: {query}")
                    return []
                    
                if 'entries' not in search_info:
                    logger.warning(f"No entries in search results for query: {query}")
                    logger.warning(f"Search info keys: {list(search_info.keys()) if search_info else 'None'}")
                    return []
                
                logger.debug(f"Found {len(search_info['entries'])} raw results")
                
                for entry in search_info['entries'][:max_results * 3]:  # Process more entries
                    if not entry or not entry.get('id'):
                        continue
                    
                    # Get detailed info for each video (but only if needed)
                    try:
                        video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                        
                        # Use the flat extraction data first, only get detailed if needed
                        title = entry.get('title', '')
                        duration = entry.get('duration')
                        
                        # If we don't have duration from flat extraction, get detailed info
                        if duration is None:
                            detailed_opts = search_opts.copy()
                            detailed_opts['extract_flat'] = False
                            
                            with yt_dlp.YoutubeDL(detailed_opts) as detailed_ydl:
                                detailed_info = detailed_ydl.extract_info(video_url, download=False)
                                if detailed_info:
                                    duration = detailed_info.get('duration', 0)
                                    title = detailed_info.get('title', title)
                        
                        # Skip long videos (>5 minutes) 
                        if duration and duration > 300:
                            continue
                        
                        # Parse title to extract artist and song info
                        artist, song_title = self._parse_title(title)
                        
                        # More lenient music detection - accept most results
                        if self._is_likely_music(title, entry.get('description', '')):
                            result = {
                                'id': entry['id'],
                                'title': song_title or title,
                                'artist': artist or entry.get('uploader', 'Unknown Artist'),
                                'album': '',  # YouTube doesn't provide album info
                                'duration': duration or 0,
                                'duration_formatted': self._format_duration(duration or 0),
                                'url': video_url,
                                'thumbnail': entry.get('thumbnail'),
                                'source': 'youtube'
                            }
                            search_results.append(result)
                            
                            # Stop once we have enough good results
                            if len(search_results) >= max_results:
                                break
                                
                    except Exception as e:
                        logger.debug(f"Error processing video {entry.get('id', 'unknown')}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"❌ YouTube search FAILED for query '{query}': {type(e).__name__}: {e}")
            logger.error(f"📍 Full traceback:\n{traceback.format_exc()}")

            # Additional debugging info
            logger.error(f"🔍 Debug info:")
            logger.error(f"   - Query: {repr(query)}")
            logger.error(f"   - Max results: {max_results}")
            logger.error(f"   - yt-dlp version: {yt_dlp.version.__version__ if hasattr(yt_dlp, 'version') else 'unknown'}")
            logger.error(f"   - Output directory: {self.output_dir}")
            logger.error(f"   - Current working directory: {os.getcwd()}")

            return []
        
        logger.info(f"YouTube search for '{query}' returned {len(search_results)} results")
        return search_results
    
    def download_audio(self, video_url: str, title: str, artist: str, max_retries: int = 2) -> Optional[str]:
        """
        Download audio from YouTube video and tag it.

        Args:
            video_url: YouTube video URL
            title: Song title for tagging
            artist: Artist name for tagging
            max_retries: Number of retry attempts (default: 2)

        Returns:
            Filename of downloaded file, or None if failed
        """
        logger.info(f"⬇️ Starting YouTube download: url='{video_url}', title='{title}', artist='{artist}'")

        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"🔄 Retry attempt {attempt}/{max_retries} for: {title}")
                import time
                time.sleep(2)  # Wait 2 seconds between retries

            try:
                # Create safe filename
                safe_filename = self._create_safe_filename(title, artist)
            
                # Update output template with safe filename
                download_opts = self.ydl_opts.copy()
                download_opts['outtmpl'] = str(self.output_dir / f"{safe_filename}.%(ext)s")

                # Download the audio
                with yt_dlp.YoutubeDL(download_opts) as ydl:
                    logger.info(f"Downloading audio from: {video_url}")
                    ydl.download([video_url])

                # Find the downloaded file (yt-dlp might change the extension)
                expected_file = self.output_dir / f"{safe_filename}.mp3"
                if expected_file.exists():
                    downloaded_file = expected_file
                else:
                    # Look for files with the same base name but different extensions
                    pattern = f"{safe_filename}.*"
                    matches = list(self.output_dir.glob(pattern))
                    if matches:
                        downloaded_file = matches[0]
                    else:
                        logger.error(f"Downloaded file not found: {expected_file}")
                        if attempt < max_retries:
                            logger.info(f"🔄 Will retry download (attempt {attempt + 1}/{max_retries})")
                            continue  # Try again
                        else:
                            return None

                # Tag the MP3 file with metadata
                self._tag_mp3_file(downloaded_file, title, artist)

                if attempt > 0:
                    logger.info(f"✅ Download succeeded on retry attempt {attempt}")
                logger.info(f"Successfully downloaded and tagged: {downloaded_file.name}")
                return downloaded_file.name

            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)

                logger.error(f"❌ YouTube download FAILED (attempt {attempt + 1}/{max_retries + 1}) for {video_url}: {error_type}: {error_msg}")

                # Enhanced error classification
                if "HTTP Error 403" in error_msg or "403" in error_msg:
                    logger.error("🚫 Specific issue: HTTP 403 Forbidden - Video may be restricted or need authentication")
                elif "HTTP Error 404" in error_msg or "404" in error_msg:
                    logger.error("🚫 Specific issue: HTTP 404 Not Found - Video may have been deleted or URL is invalid")
                elif "private" in error_msg.lower():
                    logger.error("🚫 Specific issue: Video is private")
                elif "not available" in error_msg.lower():
                    logger.error("🚫 Specific issue: Video not available in this region or deleted")
                elif "age" in error_msg.lower() and "restricted" in error_msg.lower():
                    logger.error("🚫 Specific issue: Age-restricted content")
                elif "ffmpeg" in error_msg.lower():
                    logger.error("🚫 Specific issue: Audio processing failed - FFmpeg error")
                elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                    logger.error("🚫 Specific issue: Network connectivity problem")

                # If this is the last attempt, log full details
                if attempt >= max_retries:
                    logger.error(f"📍 Full traceback:\n{traceback.format_exc()}")
                    logger.error(f"🔍 Download debug info:")
                    logger.error(f"   - Video URL: {repr(video_url)}")
                    logger.error(f"   - Title: {repr(title)}")
                    logger.error(f"   - Artist: {repr(artist)}")
                    logger.error(f"   - Output directory: {self.output_dir}")
                    logger.error(f"   - Output directory exists: {self.output_dir.exists()}")
                    logger.error(f"   - Output directory writable: {os.access(self.output_dir, os.W_OK)}")
                    logger.error(f"   - Safe filename: {repr(self._create_safe_filename(title, artist))}")
                    return None
                else:
                    logger.info(f"🔄 Will retry download (attempt {attempt + 2}/{max_retries + 1})")
                    continue  # Try again

        # If we get here, all retries failed
        logger.error(f"❌ All download attempts failed for: {title} by {artist}")
        return None
    
    def _parse_title(self, title: str) -> tuple[str, str]:
        """
        Parse YouTube video title to extract artist and song name.
        
        Returns:
            (artist, song_title) tuple
        """
        # Common patterns for YouTube music titles
        patterns = [
            r'^(.+?)\s*[-–—]\s*(.+?)(?:\s*\(.*\))?(?:\s*\[.*\])?$',  # "Artist - Song"
            r'^(.+?)\s*:\s*(.+?)(?:\s*\(.*\))?(?:\s*\[.*\])?$',      # "Artist : Song"  
            r'^(.+?)\s*\|\s*(.+?)(?:\s*\(.*\))?(?:\s*\[.*\])?$',     # "Artist | Song"
            r'^(.+?)\s*by\s+(.+?)(?:\s*\(.*\))?(?:\s*\[.*\])?$',     # "Song by Artist"
        ]
        
        for pattern in patterns:
            match = re.match(pattern, title, re.IGNORECASE)
            if match:
                part1, part2 = match.groups()
                
                # For "Song by Artist" pattern, swap the order
                if ' by ' in title.lower():
                    return part2.strip(), part1.strip()  # Artist, Song
                else:
                    return part1.strip(), part2.strip()  # Artist, Song
        
        # If no pattern matches, return empty artist and full title as song
        return '', title
    
    def _is_likely_music(self, title: str, description: str) -> bool:
        """
        Heuristic to determine if a video is likely to be music.
        More lenient than before to capture more results.
        """
        # Keywords that definitely suggest non-music content (exclude these)
        non_music_keywords = [
            'tutorial', 'how to', 'review', 'reaction', 'interview',
            'behind the scenes', 'making of', 'documentary', 'news',
            'podcast', 'talk show', 'discussion', 'vlog', 'gameplay',
            'unboxing', 'trailer', 'movie', 'tv show'
        ]
        
        title_lower = title.lower()
        
        # Check for definite non-music keywords (exclude)
        for keyword in non_music_keywords:
            if keyword in title_lower:
                logger.debug(f"Excluding non-music content: {title}")
                return False
        
        # Be more lenient - include most things that aren't explicitly non-music
        return True
    
    def _create_safe_filename(self, title: str, artist: str) -> str:
        """Create a safe filename from title and artist."""
        # Clean the strings
        safe_title = re.sub(r'[^\w\s-]', '', title).strip()
        safe_artist = re.sub(r'[^\w\s-]', '', artist).strip()
        
        # Create filename
        if safe_artist and safe_title:
            filename = f"{safe_artist} - {safe_title}"
        elif safe_title:
            filename = safe_title
        elif safe_artist:
            filename = safe_artist
        else:
            filename = "unknown_song"
        
        # Replace spaces and limit length
        filename = re.sub(r'\s+', '_', filename)
        filename = filename[:100]  # Limit length
        
        return filename
    
    def _tag_mp3_file(self, file_path: Path, title: str, artist: str, album: str = "YouTube Download"):
        """
        Add ID3 tags to the MP3 file.
        
        Args:
            file_path: Path to MP3 file
            title: Song title
            artist: Artist name
            album: Album name (default: "YouTube Download")
        """
        try:
            audio = MP3(str(file_path), ID3=ID3)
            
            # Add ID3 tag if it doesn't exist
            try:
                audio.add_tags()
            except Exception:
                pass  # Tags already exist
            
            # Set metadata tags
            audio.tags[TIT2] = TIT2(encoding=3, text=title)
            audio.tags[TPE1] = TPE1(encoding=3, text=artist)
            audio.tags[TALB] = TALB(encoding=3, text=album)
            audio.tags[TPE2] = TPE2(encoding=3, text=artist)  # Album artist
            
            # Save the tags
            audio.save()
            logger.debug(f"Tagged MP3 file: {file_path.name}")
            
        except Exception as e:
            logger.warning(f"Error tagging MP3 file {file_path}: {e}")
    
    def _format_duration(self, seconds) -> str:
        """Format duration in seconds to MM:SS format."""
        if not seconds:
            return "0:00"
        
        # Convert to int if it's a float
        seconds = int(float(seconds))
        
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"


# Global instance
_youtube_service = None

def get_youtube_service():
    """Get or create YouTube service instance."""
    global _youtube_service
    if _youtube_service is None:
        _youtube_service = YouTubeAudioService()
    return _youtube_service