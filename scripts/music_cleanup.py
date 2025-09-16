#!/usr/bin/env python3
"""
Music Library Cleanup Tool
Organizes and cleans music metadata and file structure
"""

import os
import shutil
import re
import subprocess
from pathlib import Path
from mutagen import File
from mutagen.id3 import ID3NoHeaderError

def clean_filename(filename):
    """Clean filename for proper file system compatibility"""
    # Remove/replace problematic characters
    clean = re.sub(r'[<>:"/\\|?*]', '', filename)
    clean = re.sub(r'\s+', ' ', clean).strip()
    # Remove trailing dots and spaces
    clean = clean.rstrip('. ')
    return clean[:200]  # Limit length

def get_metadata(filepath):
    """Extract metadata from audio file"""
    try:
        audiofile = File(filepath)
        if audiofile is None:
            return None

        metadata = {
            'artist': '',
            'album': '',
            'title': '',
            'tracknumber': '',
            'date': '',
            'albumartist': ''
        }

        # Handle different tag formats
        if hasattr(audiofile, 'tags') and audiofile.tags:
            tags = audiofile.tags

            # Try different tag formats
            for key in ['TPE1', 'ARTIST', '\xa9ART']:
                if key in tags and tags[key]:
                    metadata['artist'] = str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    break

            for key in ['TALB', 'ALBUM', '\xa9alb']:
                if key in tags and tags[key]:
                    metadata['album'] = str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    break

            for key in ['TIT2', 'TITLE', '\xa9nam']:
                if key in tags and tags[key]:
                    metadata['title'] = str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    break

            for key in ['TRCK', 'TRACKNUMBER', 'trkn']:
                if key in tags and tags[key]:
                    track = str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    metadata['tracknumber'] = track.split('/')[0]  # Remove total tracks
                    break

            for key in ['TDRC', 'DATE', '\xa9day']:
                if key in tags and tags[key]:
                    metadata['date'] = str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    break

            for key in ['TPE2', 'ALBUMARTIST', 'aART']:
                if key in tags and tags[key]:
                    metadata['albumartist'] = str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    break

        # Use artist as albumartist if not set
        if not metadata['albumartist'] and metadata['artist']:
            metadata['albumartist'] = metadata['artist']

        # Clean metadata
        for key in metadata:
            if metadata[key]:
                metadata[key] = clean_filename(metadata[key])

        return metadata

    except Exception as e:
        print(f"Error reading metadata from {filepath}: {e}")
        return None

def organize_music_library(source_dir, target_dir):
    """Organize music library with proper folder structure"""
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    target_path.mkdir(exist_ok=True)

    audio_extensions = {'.mp3', '.m4a', '.flac', '.wav', '.ogg', '.aac'}
    processed = 0
    errors = 0

    print(f"Organizing music from {source_dir} to {target_dir}")

    # Walk through all files
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            source_file = Path(root) / filename

            if source_file.suffix.lower() in audio_extensions:
                metadata = get_metadata(source_file)

                if metadata:
                    # Create organized path structure
                    artist = metadata['albumartist'] or metadata['artist'] or 'Unknown Artist'
                    album = metadata['album'] or 'Unknown Album'
                    title = metadata['title'] or source_file.stem

                    # Clean names
                    artist = clean_filename(artist)
                    album = clean_filename(album)
                    title = clean_filename(title)

                    # Create target directory structure
                    artist_dir = target_path / artist
                    album_dir = artist_dir / album
                    album_dir.mkdir(parents=True, exist_ok=True)

                    # Create target filename with track number
                    track_num = metadata['tracknumber']
                    if track_num and track_num.isdigit():
                        track_prefix = f"{int(track_num):02d} "
                    else:
                        track_prefix = ""

                    target_filename = f"{track_prefix}{title}{source_file.suffix}"
                    target_file = album_dir / target_filename

                    # Handle duplicates
                    counter = 1
                    original_target = target_file
                    while target_file.exists():
                        name_part = original_target.stem
                        extension = original_target.suffix
                        target_file = original_target.parent / f"{name_part} ({counter}){extension}"
                        counter += 1

                    try:
                        # Copy file
                        shutil.copy2(source_file, target_file)
                        processed += 1

                        if processed % 100 == 0:
                            print(f"Processed {processed} files...")

                    except Exception as e:
                        print(f"Error copying {source_file} to {target_file}: {e}")
                        errors += 1

                else:
                    # File without readable metadata - copy to Unknown folder
                    unknown_dir = target_path / "Unknown Artist" / "Unknown Album"
                    unknown_dir.mkdir(parents=True, exist_ok=True)

                    try:
                        shutil.copy2(source_file, unknown_dir / filename)
                        processed += 1
                    except Exception as e:
                        print(f"Error copying unknown file {source_file}: {e}")
                        errors += 1

    return processed, errors

def main():
    source_dir = "/home/kdresdell/Music/merged_library"
    target_dir = "/home/kdresdell/Music/cleaned_library"

    if not Path(source_dir).exists():
        print(f"Source directory not found: {source_dir}")
        return 1

    print("=== MUSIC LIBRARY CLEANUP ===")
    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")

    if Path(target_dir).exists():
        response = input(f"Target directory {target_dir} already exists. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Cleanup cancelled")
            return 0

    try:
        processed, errors = organize_music_library(source_dir, target_dir)

        print(f"\n=== CLEANUP COMPLETE ===")
        print(f"✓ Processed: {processed} files")
        print(f"✗ Errors: {errors} files")
        print(f"✓ Organized library: {target_dir}")
        print(f"\nNext step: Run duplicate detection with fdupes")

        return 0

    except Exception as e:
        print(f"Error during cleanup: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())