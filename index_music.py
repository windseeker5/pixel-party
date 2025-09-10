#!/usr/bin/env python3
"""
Music Library Indexer for PixelParty
Usage: python index_music.py [options]
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from tqdm import tqdm
from mutagen import File
from mutagen.id3 import ID3NoHeaderError

# Add the project root to the path so we can import the app
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from app.models import MusicLibrary
from config import Config

# Supported audio formats
SUPPORTED_FORMATS = {'.mp3', '.flac', '.m4a', '.ogg', '.wav', '.aac', '.wma'}

class MusicIndexer:
    def __init__(self, music_path: str = None, verbose: bool = False):
        """Initialize the music indexer."""
        self.music_path = Path(music_path or str(Config.MUSIC_LIBRARY_PATH))
        self.verbose = verbose
        self.stats = {
            'total_files': 0,
            'indexed': 0,
            'errors': 0,
            'skipped': 0,
            'updated': 0
        }
        
        # Initialize Flask app and database context
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create tables if they don't exist
        with self.app.app_context():
            db.create_all()
    
    def __del__(self):
        """Clean up app context."""
        if hasattr(self, 'app_context'):
            self.app_context.pop()
    
    def get_audio_files(self) -> List[Path]:
        """Scan directory recursively for audio files."""
        if not self.music_path.exists():
            print(f"❌ Music library directory does not exist: {self.music_path}")
            return []
        
        print(f"🔍 Scanning {self.music_path} for audio files...")
        audio_files = []
        
        try:
            for file_path in self.music_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
                    audio_files.append(file_path)
                    
        except Exception as e:
            print(f"❌ Error scanning directory: {e}")
            return []
        
        return sorted(audio_files)
    
    def extract_metadata(self, file_path: Path) -> Optional[Dict]:
        """Extract metadata from audio file."""
        try:
            audio_file = File(str(file_path))
            if audio_file is None:
                return None
            
            # Get file modification time
            file_stat = file_path.stat()
            file_modified_at = datetime.fromtimestamp(file_stat.st_mtime)
            
            metadata = {
                'filename': file_path.name,
                'file_path': str(file_path),
                'file_size': file_stat.st_size,
                'file_modified_at': file_modified_at,
                'title': '',
                'artist': '',
                'album': '',
                'genre': '',
                'duration': 0
            }
            
            # Extract common metadata fields with multiple format support
            title = None
            artist = None
            album = None
            genre = None
            
            # Extract metadata with proper handling of different tag formats
            def safe_get_tag(tags, *keys):
                """Safely extract tag value from various formats."""
                for key in keys:
                    if key in tags:
                        value = tags[key]
                        # Handle different types of tag values
                        if hasattr(value, 'text') and value.text:
                            return str(value.text[0]) if value.text else ''
                        elif isinstance(value, str):
                            return value
                        elif hasattr(value, '__iter__') and not isinstance(value, str):
                            try:
                                return str(value[0]) if len(value) > 0 else ''
                            except (IndexError, TypeError):
                                return str(value) if value else ''
                        else:
                            return str(value) if value else ''
                return ''
            
            # Try different tag formats
            if hasattr(audio_file, 'tags') and audio_file.tags:
                tags = audio_file.tags
                
                # Extract tags with proper handling
                title = safe_get_tag(tags, 'TIT2', 'TITLE', '\xa9nam', '©nam')
                artist = safe_get_tag(tags, 'TPE1', 'ARTIST', '\xa9ART', '©ART')
                album = safe_get_tag(tags, 'TALB', 'ALBUM', '\xa9alb', '©alb')
                genre = safe_get_tag(tags, 'TCON', 'GENRE', '\xa9gen', '©gen')
                
                metadata['title'] = title
                metadata['artist'] = artist
                metadata['album'] = album
                metadata['genre'] = genre
            
            # Get duration in seconds
            if hasattr(audio_file, 'info') and audio_file.info and hasattr(audio_file.info, 'length'):
                metadata['duration'] = int(audio_file.info.length)
            
            # Fallback to filename if no title
            if not metadata['title']:
                metadata['title'] = file_path.stem
            
            # Set unknown values for empty fields
            for field in ['artist', 'album', 'genre']:
                if not metadata[field]:
                    metadata[field] = 'Unknown'
            
            return metadata
            
        except (ID3NoHeaderError, Exception) as e:
            if self.verbose:
                print(f"⚠️  Error reading {file_path.name}: {e}")
            return None
    
    def should_update_file(self, file_path: Path, force: bool = False) -> bool:
        """Check if file should be indexed/updated."""
        if force:
            return True
            
        # Check if file exists in database
        existing = MusicLibrary.query.filter_by(file_path=str(file_path)).first()
        if not existing:
            return True
            
        # Check if file has been modified since last index
        file_stat = file_path.stat()
        file_modified_at = datetime.fromtimestamp(file_stat.st_mtime)
        
        if existing.file_modified_at and file_modified_at <= existing.file_modified_at:
            return False
            
        return True
    
    def index_file(self, metadata: Dict, force: bool = False) -> bool:
        """Index or update a single file."""
        try:
            file_path = metadata['file_path']
            
            # Check if record exists
            existing = MusicLibrary.query.filter_by(file_path=file_path).first()
            
            if existing and not force and not self.should_update_file(Path(file_path)):
                self.stats['skipped'] += 1
                return True
            
            # Create or update record
            if existing:
                # Update existing record
                existing.filename = metadata['filename']
                existing.title = metadata['title']
                existing.artist = metadata['artist']
                existing.album = metadata['album']
                existing.genre = metadata['genre']
                existing.duration = metadata['duration']
                existing.file_size = metadata['file_size']
                existing.file_modified_at = metadata['file_modified_at']
                existing.indexed_at = datetime.utcnow()
                existing.index_status = 'indexed'
                existing.index_error = None
                
                # Update lowercase fields
                existing.title_lower = (metadata['title'] or '').lower()
                existing.artist_lower = (metadata['artist'] or '').lower()
                existing.album_lower = (metadata['album'] or '').lower()
                existing.genre_lower = (metadata['genre'] or '').lower()
                
                record = existing
                self.stats['updated'] += 1
                
            else:
                # Create new record
                record = MusicLibrary(
                    filename=metadata['filename'],
                    title=metadata['title'],
                    artist=metadata['artist'],
                    album=metadata['album'],
                    genre=metadata['genre'],
                    duration=metadata['duration'],
                    file_path=file_path,
                    file_size=metadata['file_size'],
                    file_modified_at=metadata['file_modified_at'],
                    indexed_at=datetime.utcnow(),
                    index_status='indexed',
                    
                    # Lowercase fields for case-insensitive search
                    title_lower=(metadata['title'] or '').lower(),
                    artist_lower=(metadata['artist'] or '').lower(),
                    album_lower=(metadata['album'] or '').lower(),
                    genre_lower=(metadata['genre'] or '').lower()
                )
                
                db.session.add(record)
                self.stats['indexed'] += 1
            
            # Commit every 100 records or so to avoid memory issues
            if (self.stats['indexed'] + self.stats['updated']) % 100 == 0:
                db.session.commit()
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Error indexing {metadata.get('filename', 'unknown')}: {e}")
            self.stats['errors'] += 1
            
            # Try to record the error in database
            try:
                existing = MusicLibrary.query.filter_by(file_path=metadata['file_path']).first()
                if existing:
                    existing.index_status = 'error'
                    existing.index_error = str(e)
                    db.session.commit()
            except:
                pass  # Don't let error recording cause more errors
                
            return False
    
    def cleanup_missing_files(self):
        """Remove database entries for files that no longer exist."""
        print("🧹 Cleaning up missing files...")
        
        missing_count = 0
        all_records = MusicLibrary.query.all()
        
        for record in all_records:
            if not Path(record.file_path).exists():
                db.session.delete(record)
                missing_count += 1
                
                if missing_count % 100 == 0:
                    db.session.commit()
        
        if missing_count > 0:
            db.session.commit()
            print(f"🗑️  Removed {missing_count} missing files from database")
    
    def run(self, force: bool = False, cleanup: bool = True) -> Dict:
        """Run the indexing process."""
        start_time = datetime.now()
        
        print("🎵 PixelParty Music Library Indexer")
        print("=" * 50)
        
        # Get all audio files
        audio_files = self.get_audio_files()
        self.stats['total_files'] = len(audio_files)
        
        if self.stats['total_files'] == 0:
            print("ℹ️  No audio files found")
            return self.stats
        
        print(f"📊 Found {self.stats['total_files']} audio files")
        
        # Process files with progress bar
        with tqdm(total=self.stats['total_files'], desc="Indexing", unit="files") as pbar:
            
            for file_path in audio_files:
                
                # Update progress bar with current file
                pbar.set_postfix_str(f"Processing {file_path.name}")
                
                # Skip if not forcing and file doesn't need update
                if not force and not self.should_update_file(file_path):
                    self.stats['skipped'] += 1
                    pbar.update(1)
                    continue
                
                # Extract metadata
                metadata = self.extract_metadata(file_path)
                
                if metadata:
                    # Index the file
                    self.index_file(metadata, force=force)
                else:
                    self.stats['errors'] += 1
                
                pbar.update(1)
        
        # Final commit
        try:
            db.session.commit()
        except Exception as e:
            print(f"❌ Error committing final batch: {e}")
        
        # Cleanup missing files
        if cleanup:
            self.cleanup_missing_files()
        
        # Calculate elapsed time
        elapsed = datetime.now() - start_time
        
        # Print summary
        print("\n" + "=" * 50)
        print("📈 INDEXING COMPLETE")
        print("=" * 50)
        print(f"⏱️  Time taken: {elapsed}")
        print(f"📁 Total files scanned: {self.stats['total_files']}")
        print(f"✅ New files indexed: {self.stats['indexed']}")
        print(f"🔄 Files updated: {self.stats['updated']}")
        print(f"⏭️  Files skipped (unchanged): {self.stats['skipped']}")
        print(f"❌ Errors: {self.stats['errors']}")
        
        if self.stats['indexed'] + self.stats['updated'] > 0:
            rate = (self.stats['indexed'] + self.stats['updated']) / elapsed.total_seconds()
            print(f"🚀 Processing rate: {rate:.2f} files/second")
        
        return self.stats
    
    def show_stats(self) -> Dict:
        """Show current library statistics."""
        print("🎵 PixelParty Music Library Statistics")
        print("=" * 50)
        
        try:
            # Get basic counts
            total_tracks = MusicLibrary.query.count()
            
            if total_tracks == 0:
                print("📭 Library is empty - run indexing first")
                return {'total_tracks': 0}
            
            # Get detailed stats
            tracks = MusicLibrary.query.all()
            
            # Count unique values
            unique_artists = len(set(track.artist for track in tracks if track.artist and track.artist != 'Unknown'))
            unique_albums = len(set(track.album for track in tracks if track.album and track.album != 'Unknown'))
            unique_genres = len(set(track.genre for track in tracks if track.genre and track.genre != 'Unknown'))
            
            # Calculate totals
            total_duration = sum(track.duration or 0 for track in tracks)
            total_size = sum(track.file_size or 0 for track in tracks)
            
            # Format duration
            hours = total_duration // 3600
            minutes = (total_duration % 3600) // 60
            duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            
            # Format file size
            size_gb = total_size / (1024**3)
            size_mb = total_size / (1024**2)
            size_str = f"{size_gb:.2f} GB" if size_gb >= 1 else f"{size_mb:.1f} MB"
            
            # Status counts
            indexed_count = MusicLibrary.query.filter_by(index_status='indexed').count()
            error_count = MusicLibrary.query.filter_by(index_status='error').count()
            
            # Print stats
            print(f"📀 Total tracks: {total_tracks:,}")
            print(f"🎤 Unique artists: {unique_artists:,}")
            print(f"💿 Unique albums: {unique_albums:,}")
            print(f"🎶 Unique genres: {unique_genres:,}")
            print(f"⏰ Total duration: {duration_str}")
            print(f"💾 Total size: {size_str}")
            print(f"✅ Successfully indexed: {indexed_count:,}")
            if error_count > 0:
                print(f"❌ Indexing errors: {error_count:,}")
            
            # Recent activity
            recent = MusicLibrary.query.order_by(MusicLibrary.indexed_at.desc()).first()
            if recent:
                print(f"🕐 Last indexed: {recent.indexed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return {
                'total_tracks': total_tracks,
                'unique_artists': unique_artists,
                'unique_albums': unique_albums,
                'unique_genres': unique_genres,
                'total_duration': total_duration,
                'total_size': total_size,
                'indexed_count': indexed_count,
                'error_count': error_count
            }
            
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return {}


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Index PixelParty music library',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python index_music.py                    # Basic indexing
  python index_music.py --force            # Force full re-index
  python index_music.py --stats            # Show statistics only
  python index_music.py --verbose          # Verbose output
  python index_music.py --path /custom/path # Index custom directory
        """
    )
    
    parser.add_argument('--force', action='store_true', 
                       help='Force full re-index (reprocess all files)')
    parser.add_argument('--stats', action='store_true', 
                       help='Show library statistics only')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output for debugging')
    parser.add_argument('--path', 
                       help='Music library path (default: from config.py)')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Skip cleanup of missing files')
    
    args = parser.parse_args()
    
    try:
        # Create indexer
        indexer = MusicIndexer(
            music_path=args.path,
            verbose=args.verbose
        )
        
        if args.stats:
            # Just show statistics
            indexer.show_stats()
        else:
            # Run indexing
            indexer.run(
                force=args.force,
                cleanup=not args.no_cleanup
            )
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Indexing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()