# Music Library Indexing Guide

This guide explains how to use the PixelParty music library indexing system to make your 20GB music collection searchable for party guests.

## Overview

The music indexing system allows you to:
- Index your entire music library for fast searching
- Enable case-insensitive search (guests can search "bob dylan" or "BOB DYLAN" and get the same results)
- Monitor indexing progress with beautiful progress bars
- Manage your music library through a web admin interface

## Quick Start

### 1. Index Your Music Library

```bash
# Basic indexing (recommended for first time)
python index_music.py

# This will scan /mnt/media/MUSIC and index all audio files
# Shows progress bar and completion statistics
```

### 2. Check Results

```bash
# View library statistics
python index_music.py --stats
```

### 3. Test Search

Visit the admin interface at `http://localhost:5001/admin/music/` to test search functionality.

## Command Line Usage

### Basic Commands

```bash
# Index the music library (incremental - only new/modified files)
python index_music.py

# Show help and all available options
python index_music.py --help

# Show current library statistics without indexing
python index_music.py --stats
```

### Advanced Options

```bash
# Force full re-index (re-process ALL files, takes longer)
python index_music.py --force

# Verbose output for debugging
python index_music.py --verbose

# Index a custom directory instead of default /mnt/media/MUSIC
python index_music.py --path /path/to/your/music

# Combine options
python index_music.py --force --verbose
```

### Skip Cleanup

```bash
# Skip cleanup of missing files (faster, but may leave orphaned records)
python index_music.py --no-cleanup
```

## Example Usage Scenarios

### Scenario 1: First Time Setup

```bash
# 1. Index your entire music library
python index_music.py --verbose

# Expected output:
# 🎵 PixelParty Music Library Indexer
# ==================================================
# 🔍 Scanning /mnt/media/MUSIC for audio files...
# 📊 Found 5,234 audio files
# Indexing: 100%|████████████| 5234/5234 [03:45<00:00, 184.72files/s]
# 
# ==================================================
# 📈 INDEXING COMPLETE
# ==================================================
# ⏱️  Time taken: 0:03:45
# 📁 Total files scanned: 5,234
# ✅ New files indexed: 5,234
# 🔄 Files updated: 0
# ⏭️  Files skipped (unchanged): 0
# ❌ Errors: 12
# 🚀 Processing rate: 184.72 files/second

# 2. Check the results
python index_music.py --stats

# Expected output:
# 🎵 PixelParty Music Library Statistics
# ==================================================
# 📀 Total tracks: 5,234
# 🎤 Unique artists: 247
# 💿 Unique albums: 892
# 🎶 Unique genres: 15
# ⏰ Total duration: 342h 15m
# 💾 Total size: 19.8 GB
# ✅ Successfully indexed: 5,222
# ❌ Indexing errors: 12
# 🕐 Last indexed: 2025-09-09 23:45:30
```

### Scenario 2: Adding New Music

```bash
# After adding new songs to your music folder, run incremental update
python index_music.py

# This will only process new or modified files
# Expected output:
# 🎵 PixelParty Music Library Indexer
# ==================================================
# 🔍 Scanning /mnt/media/MUSIC for audio files...
# 📊 Found 5,267 audio files
# Indexing: 100%|████████████| 33/5267 [00:05<00:00, 165.23files/s]
# 
# ==================================================
# 📈 INDEXING COMPLETE
# ==================================================
# ⏱️  Time taken: 0:00:05
# 📁 Total files scanned: 5,267
# ✅ New files indexed: 33
# 🔄 Files updated: 0
# ⏭️  Files skipped (unchanged): 5,234
# ❌ Errors: 0
# 🚀 Processing rate: 165.23 files/second
```

### Scenario 3: Fixing Issues

```bash
# If you suspect some files weren't indexed correctly, force re-index
python index_music.py --force --verbose

# This will re-process every single file (takes much longer)
# Use only when necessary
```

### Scenario 4: Custom Music Directory

```bash
# Index music from a different location
python index_music.py --path "/home/user/MyMusic" --verbose

# Index multiple directories (run separately)
python index_music.py --path "/media/usb/party-music"
python index_music.py --path "/backup/more-music"
```

## Web Admin Interface

### Accessing the Admin Panel

1. Start the Flask app: `python app.py`
2. Open browser: `http://localhost:5001/admin/music/`

### Admin Features

#### Statistics Dashboard
- **Total Tracks**: Number of indexed songs
- **Artists**: Number of unique artists
- **Albums**: Number of unique albums  
- **Duration**: Total playtime of your library

#### Indexing Controls
- **Start Indexing**: Begin incremental indexing
- **Force Re-index**: Re-process all files (use if database seems corrupted)
- **Clear Index**: Remove all indexed music from database

#### Search Testing
- Test search functionality in real-time
- Verify case-insensitive search works
- Try different search terms:
  - "bob dylan" vs "BOB DYLAN" vs "Bob Dylan"
  - "rolling stone" vs "ROLLING STONE"
  - Artist names, song titles, album names

#### Real-time Progress
- Watch indexing progress live
- See current file being processed
- Monitor processing speed and estimated completion time

## Understanding the Output

### Progress Bar
```
Indexing: 45%|████▌     | 2345/5234 [01:30<02:15, 184.72files/s, Processing Artist - Song.mp3]
```

- **45%**: Percentage complete
- **2345/5234**: Current file / Total files
- **[01:30<02:15]**: Time elapsed < Time remaining
- **184.72files/s**: Processing speed
- **Processing Artist - Song.mp3**: Current file being indexed

### Statistics Explanation

- **New files indexed**: Songs added to database for the first time
- **Files updated**: Existing songs that were re-processed due to changes
- **Files skipped**: Unchanged songs that were not re-processed
- **Errors**: Files that couldn't be processed (corrupted, unsupported format, etc.)

## Supported Audio Formats

The indexer supports these audio formats:
- `.mp3` (most common)
- `.flac` (high quality)
- `.m4a` (iTunes/AAC)
- `.ogg` (open source)
- `.wav` (uncompressed)
- `.aac` (Advanced Audio Coding)
- `.wma` (Windows Media Audio)

## Troubleshooting

### Common Issues

#### 1. "Music library directory does not exist"
```bash
# Check if your music path is correct
ls -la /mnt/media/MUSIC

# If using custom path, specify it
python index_music.py --path "/correct/path/to/music"
```

#### 2. "No audio files found"
```bash
# Check if you have supported audio files
find /mnt/media/MUSIC -name "*.mp3" | head -5

# Use verbose mode to see what's happening
python index_music.py --verbose
```

#### 3. Database Errors
```bash
# If you get database errors, recreate the database
# WARNING: This removes all indexed data
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.drop_all(); db.create_all()"

# Then re-index
python index_music.py --force
```

#### 4. Search Not Working
- Check that indexing completed successfully
- Verify the Flask app is running: `python app.py`
- Test search in admin interface: `http://localhost:5001/admin/music/`

#### 5. Slow Indexing
- Normal speed is 100-200 files/second
- If slower, check disk space and system resources
- Large files (FLAC) take longer to process

### Performance Tips

1. **Initial indexing**: Run overnight for large libraries (20GB+ = 1-4 hours)
2. **Incremental updates**: Run weekly to catch new music (1-5 minutes)
3. **Force re-index**: Only when necessary (corrupted database, format changes)

## Integration with PixelParty

Once indexed, your music becomes searchable in the party interface:

1. **Mobile Interface** (`/mobile/music`): Guests can search for songs
2. **Big Screen** (`/display/music`): Shows queue and current playing
3. **Case-insensitive**: "beatles", "BEATLES", "Beatles" all work
4. **Fast search**: Results appear instantly as guests type

## File Locations

- **Indexing Script**: `index_music.py` (run from project root)
- **Admin Interface**: `http://localhost:5001/admin/music/`
- **Database**: `birthday_party.db` (SQLite database)
- **Music Source**: `/mnt/media/MUSIC` (configurable in `config.py`)
- **Configuration**: `config.py` (change `MUSIC_LIBRARY_PATH` if needed)

## Best Practices

1. **Before the party**: Run full indexing at least 24 hours before
2. **Test search**: Use admin interface to verify search works
3. **Backup database**: Copy `birthday_party.db` as backup
4. **Monitor errors**: Check error count and investigate if high
5. **Keep updated**: Run incremental indexing if you add new music

## Support

If you encounter issues:
1. Run with `--verbose` flag to see detailed output
2. Check the Flask app logs for error messages
3. Verify file permissions on music directory
4. Ensure database file is writable

Remember: The goal is to make your 20GB music library searchable for party guests so they can easily find and request their favorite songs! 🎵🎉