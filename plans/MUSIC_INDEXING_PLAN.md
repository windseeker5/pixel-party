# Music Library Indexing & Search Fix Plan

## Current Issues

### 1. No Indexed Music
- Your music library database table is empty
- The 20GB music collection at `/mnt/media/MUSIC` hasn't been indexed
- Need a way to easily index and re-index music

### 2. Case-Sensitive Search Problem
- **Current behavior**: "Bob Dylan" returns results, but "bob dylan" returns nothing
- **Expected behavior**: Search should be case-insensitive
- This is unacceptable for a music search feature

### 3. Missing Indexing Tool
- No standalone script to index music library
- Need ability to update index when adding new music

## Implementation Plan

### 1. Create Standalone Music Indexing Script

**File: `index_music.py`**

A standalone Python script that can be run independently to index or re-index the music library.

**Features:**
- Scan `/mnt/media/MUSIC` directory recursively
- Extract metadata using mutagen library
- Show progress bar during indexing
- Handle errors gracefully
- Support incremental updates
- Provide statistics after completion

**Usage Examples:**
```bash
# Basic indexing
python index_music.py

# Force full re-index (clear and rebuild)
python index_music.py --force

# Show statistics only
python index_music.py --stats

# Verbose output for debugging
python index_music.py --verbose

# Index specific directory
python index_music.py --path /path/to/music
```

### 2. Fix Case-Insensitive Search

**Current Problem:**
- SQLite's `ilike` operator isn't working as expected
- Searches are case-sensitive when they shouldn't be

**Solutions to Implement:**

#### Option A: Database Schema Fix
- Add `COLLATE NOCASE` to text columns in database schema
- This makes all text comparisons case-insensitive by default

#### Option B: Query Fix
- Use `LOWER()` function in SQL queries
- Convert both search term and database fields to lowercase for comparison

#### Option C: Dual Storage (Best Performance)
- Store both original and lowercase versions of text fields
- Use lowercase fields for searching
- Display original fields in results

### 3. Database Schema Improvements

**Modifications to `app/models.py`:**
```python
class MusicLibrary(db.Model):
    # ... existing fields ...
    
    # Add lowercase fields for searching
    title_lower = db.Column(db.String(200), index=True)
    artist_lower = db.Column(db.String(200), index=True)
    album_lower = db.Column(db.String(200), index=True)
    
    # Add file tracking
    file_modified = db.Column(db.DateTime)
    last_indexed = db.Column(db.DateTime)
    
    # Add indexes for performance
    __table_args__ = (
        db.Index('idx_music_search', 'title_lower', 'artist_lower', 'album_lower'),
    )
```

### 4. Indexing Script Structure

```python
#!/usr/bin/env python3
"""
Music Library Indexer for PixelParty
Usage: python index_music.py [options]
"""

import argparse
import sys
from pathlib import Path
from tqdm import tqdm
from mutagen import File
from sqlalchemy import create_engine
from datetime import datetime

class MusicIndexer:
    def __init__(self, db_path, music_path):
        self.db_path = db_path
        self.music_path = Path(music_path)
        self.stats = {
            'total_files': 0,
            'indexed': 0,
            'errors': 0,
            'skipped': 0
        }
    
    def scan_library(self):
        """Scan music directory for audio files"""
        pass
    
    def extract_metadata(self, file_path):
        """Extract metadata from audio file"""
        pass
    
    def index_file(self, file_path):
        """Index single audio file"""
        pass
    
    def run(self, force=False, verbose=False):
        """Run the indexing process"""
        pass
    
    def show_stats(self):
        """Display indexing statistics"""
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Index music library')
    parser.add_argument('--force', action='store_true', help='Force full re-index')
    parser.add_argument('--stats', action='store_true', help='Show statistics only')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--path', help='Music library path', default='/mnt/media/MUSIC')
    
    args = parser.parse_args()
    
    indexer = MusicIndexer(
        db_path='birthday_party.db',
        music_path=args.path
    )
    
    if args.stats:
        indexer.show_stats()
    else:
        indexer.run(force=args.force, verbose=args.verbose)
```

### 5. Search Function Improvements

**Updates to `utils/music_library.py`:**

```python
def search_all(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search across all fields (case-insensitive)."""
    try:
        # Convert search term to lowercase
        search_term = f"%{query.lower()}%"
        
        # Search using lowercase fields
        results = MusicLibrary.query.filter(
            db.or_(
                MusicLibrary.title_lower.like(search_term),
                MusicLibrary.artist_lower.like(search_term),
                MusicLibrary.album_lower.like(search_term)
            )
        ).limit(limit).all()
        
        return [self._format_result(result) for result in results]
    except Exception as e:
        print(f"Error in search_all: {e}")
        return []
```

## Files to Create/Modify

1. **NEW: `index_music.py`**
   - Standalone indexing script
   - Can be run independently
   - Handles all indexing logic

2. **MODIFY: `utils/music_library.py`**
   - Fix case-insensitive search
   - Use lowercase fields for searching

3. **MODIFY: `app/models.py`**
   - Add lowercase fields
   - Add proper indexes
   - Add file tracking fields

4. **OPTIONAL: `requirements.txt`**
   - Add `tqdm` for progress bars
   - Ensure `mutagen` is included

## Expected Results

1. **Indexing Process:**
   - Run `python index_music.py` to index entire library
   - See progress bar showing files being processed
   - Get statistics at the end (e.g., "Indexed 5,234 songs from 20GB")

2. **Search Improvements:**
   - Search for "bob dylan" - ✅ Works
   - Search for "Bob Dylan" - ✅ Works  
   - Search for "BOB DYLAN" - ✅ Works
   - Search for "BoB dYlAn" - ✅ Works

3. **Maintenance:**
   - Run script weekly/daily to index new music
   - Use `--force` to rebuild if database gets corrupted
   - Use `--stats` to check library statistics

## Testing Plan

1. **Index Small Test Directory First:**
   ```bash
   python index_music.py --path /mnt/media/MUSIC/test_folder --verbose
   ```

2. **Test Case-Insensitive Search:**
   - Index a few songs
   - Test various case combinations
   - Verify all return same results

3. **Performance Testing:**
   - Time the indexing of full library
   - Test search speed with indexed data
   - Monitor memory usage during indexing

## Future Enhancements

1. **Incremental Updates:**
   - Only index new/modified files
   - Skip files already in database with same modification time

2. **Duplicate Detection:**
   - Identify duplicate songs
   - Show warnings for duplicates

3. **Advanced Search:**
   - Fuzzy matching for typos
   - Search by year, genre, etc.
   - Smart playlists based on mood

4. **Web Interface:**
   - Admin page to trigger indexing
   - View indexing progress in real-time
   - Search statistics dashboard

## Notes

- The indexing script should be run before the party to ensure all music is searchable
- Consider setting up a cron job for automatic daily/weekly indexing
- Make sure the script handles large libraries efficiently (20GB = ~5000+ songs)
- The script should be resilient to corrupted audio files or missing metadata