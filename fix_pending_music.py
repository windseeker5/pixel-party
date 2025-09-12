#!/usr/bin/env python3
"""Fix pending music downloads that completed but didn't update database status."""

import os
import re
from pathlib import Path
from app import create_app, db
from app.models import MusicQueue

def create_safe_filename(title, artist):
    """Create a safe filename from title and artist (matches YouTube service logic)."""
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

def find_matching_file(song, music_dir):
    """Find a downloaded file that matches the song."""
    # Try exact filename match first
    expected_filename = create_safe_filename(song.song_title, song.artist or '')
    expected_path = music_dir / f"{expected_filename}.mp3"
    
    if expected_path.exists():
        return expected_path.name
    
    # Try fuzzy matching based on title
    title_words = re.sub(r'[^\w\s]', '', song.song_title.lower()).split()
    
    # Look for files that contain most of the title words
    best_match = None
    best_score = 0
    
    for file_path in music_dir.glob("*.mp3"):
        filename = file_path.stem.lower()
        
        # Count how many title words appear in the filename
        score = sum(1 for word in title_words if word in filename)
        
        if score > best_score and score >= len(title_words) * 0.5:  # At least 50% match
            best_match = file_path.name
            best_score = score
    
    return best_match

def fix_pending_downloads():
    """Fix pending music downloads by matching with existing files."""
    app = create_app()
    
    with app.app_context():
        # Find pending songs
        pending_songs = MusicQueue.query.filter_by(status='pending', played_at=None).all()
        
        if not pending_songs:
            print("No pending songs found.")
            return
        
        print(f"Found {len(pending_songs)} pending songs:")
        
        music_dir = Path('media/music')
        if not music_dir.exists():
            print("Music directory doesn't exist!")
            return
        
        fixed_count = 0
        
        for song in pending_songs:
            print(f"  - ID {song.id}: '{song.song_title}' by '{song.artist or 'Unknown'}'")
            
            # Try to find matching file
            matching_file = find_matching_file(song, music_dir)
            
            if matching_file:
                print(f"    -> Found matching file: {matching_file}")
                
                # Update database
                song.filename = matching_file
                song.status = 'ready'
                fixed_count += 1
            else:
                print(f"    -> No matching file found, keeping as pending")
        
        if fixed_count > 0:
            try:
                db.session.commit()
                print(f"\n✅ Successfully fixed {fixed_count} songs!")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error updating database: {e}")
        else:
            print("\n🔍 No files could be matched.")

if __name__ == "__main__":
    fix_pending_downloads()