# Music Functionality Complete Fix Plan

## Current Issues Identified

### 1. Database Problems
- **Database file exists but is empty (0 bytes)**
- **No tables created** - `sqlite3 birthday_party.db ".tables"` returns nothing
- **Error: "no such table: music_queue"** when trying to query

### 2. File System Issues  
- **No music files in `media/music/`** - Directory exists but is empty
- **Photos are being saved** - `media/photos/` has files
- **Music files not being copied** from `/mnt/media/MUSIC/` to project folder

### 3. Application Issues
- **Music queue shows "No music requests yet"** even after submissions
- **API endpoints failing** due to missing database tables
- **No music playback** because no files are available

## Comprehensive Fix Plan with Unit Tests

### Phase 1: Database Reset and Initialization

#### 1.1 Create Reset Script
**File:** `test/test_reset_database.py`
```python
# This script will:
- Delete existing database file
- Delete all files in media/photos/
- Delete all files in media/music/  
- Create fresh database with all tables
- Initialize default settings
- Verify tables exist
```

#### 1.2 Fix Database Initialization
**File:** `app.py`
- Add `with app.app_context(): db.create_all()` on startup
- Call `init_default_settings()` after table creation
- Add logging to confirm database initialization

### Phase 2: Create Comprehensive Unit Tests

#### 2.1 Database Test
**File:** `test/test_01_database.py`
```python
# Test cases:
1. Test database creation
2. Test all tables exist (guests, photos, music_queue, music_library, settings)
3. Test inserting records into each table
4. Test relationships between tables
5. Test default settings initialization
```

#### 2.2 Music Library Indexing Test
**File:** `test/test_02_music_indexing.py`
```python
# Test cases:
1. Test music library path exists (/mnt/media/MUSIC)
2. Test indexing finds music files
3. Test metadata extraction (title, artist, album)
4. Test file_path storage in database
5. Test search functionality (by title, artist, album)
6. Verify at least one song is indexed
```

#### 2.3 Music Search Test
**File:** `test/test_03_music_search.py`
```python
# Test cases:
1. Test search returns results with file_path
2. Test search by different criteria (title, artist, album, all)
3. Test search results include all required fields
4. Test empty search handling
5. Test search with special characters
```

#### 2.4 File Copying Test
**File:** `test/test_04_file_copying.py`
```python
# Test cases:
1. Test source file exists in library
2. Test destination directory is created
3. Test file copy operation
4. Test copied file exists and is readable
5. Test filename sanitization (spaces, special chars)
6. Test duplicate file handling
```

#### 2.5 Music Queue Submission Test
**File:** `test/test_05_music_submission.py`
```python
# Test cases:
1. Create mock guest session
2. Submit photo with music selection
3. Verify music file is copied to media/music/
4. Verify MusicQueue entry created in database
5. Verify queue entry has correct filename
6. Test submission without music (should still work)
7. Test multiple submissions
```

#### 2.6 API Endpoints Test
**File:** `test/test_06_api_endpoints.py`
```python
# Test cases:
1. Test /api/music_queue returns queue items
2. Test /api/music/current returns current song
3. Test /api/music/next advances queue
4. Test /api/music/previous goes back
5. Test /media/music/<filename> serves files
6. Test error handling for empty queue
```

#### 2.7 Complete Flow Integration Test
**File:** `test/test_07_integration.py`
```python
# Complete end-to-end test:
1. Reset database and folders
2. Index music library
3. Search for a song
4. Submit photo with music selection
5. Verify file copied
6. Verify queue entry created
7. Test music playback via API
8. Test queue navigation (next/previous)
9. Verify big screen can access music
```

### Phase 3: Fix Implementation

#### 3.1 Database Initialization Fix
**Files to modify:**
- `app.py` - Add proper initialization
- `database/init_db.py` - Create standalone initialization script

#### 3.2 Music Submission Fix
**Files to modify:**
- `app/routes/mobile.py` - Fix selected_song handling
- Ensure file_path is properly passed
- Fix file copying logic
- Add comprehensive logging

#### 3.3 API Endpoint Fixes
**Files to modify:**
- `app/routes/api.py` - Fix /api/music_queue endpoint
- Add proper error handling
- Return empty arrays instead of errors

#### 3.4 Music Service Fix
**Files to modify:**
- `app/services/music_service.py` - Ensure proper path handling
- Fix file_path storage and retrieval

### Phase 4: Testing Strategy

#### Test Execution Order:
```bash
# 1. Reset everything
python test/test_reset_database.py

# 2. Run tests in sequence
python test/test_01_database.py
python test/test_02_music_indexing.py
python test/test_03_music_search.py
python test/test_04_file_copying.py
python test/test_05_music_submission.py
python test/test_06_api_endpoints.py
python test/test_07_integration.py

# 3. Or run all tests
python -m pytest test/ -v
```

#### Test Success Criteria:
- All database tables created ✓
- At least 10 songs indexed from library ✓
- Music search returns results with file paths ✓
- Files successfully copied to media/music/ ✓
- Queue entries saved to database ✓
- API endpoints return valid JSON ✓
- Music player can load and play songs ✓

### Phase 5: Validation

#### Manual Validation Steps (after tests pass):
1. Start Flask app: `python app.py`
2. Visit `/mobile` - Verify page loads
3. Visit `/` - Verify big screen loads
4. Check database: `sqlite3 birthday_party.db ".tables"`
5. Check music folder: `ls media/music/`
6. Check API: `curl http://localhost:5001/api/music_queue`

### Error Handling Improvements

#### Add Logging:
- Log all database operations
- Log file copy operations
- Log API requests and responses
- Log errors with stack traces

#### Add Fallbacks:
- If database empty, create tables
- If music library missing, use demo songs
- If file copy fails, log but continue
- If API fails, return empty data not errors

## Implementation Checklist

- [ ] Save this plan document
- [ ] Create test directory structure
- [ ] Write test_reset_database.py
- [ ] Write test_01_database.py
- [ ] Write test_02_music_indexing.py
- [ ] Write test_03_music_search.py
- [ ] Write test_04_file_copying.py
- [ ] Write test_05_music_submission.py
- [ ] Write test_06_api_endpoints.py
- [ ] Write test_07_integration.py
- [ ] Fix app.py database initialization
- [ ] Fix mobile.py music submission
- [ ] Fix api.py endpoints
- [ ] Run all tests
- [ ] Fix any failing tests
- [ ] Manual validation
- [ ] Document any remaining issues

## Expected Outcome

After completing this plan:
1. **Database will have all tables and data**
2. **Music files will be copied to media/music/**
3. **Music queue will show submitted songs**
4. **Big screen music player will work**
5. **All tests will pass consistently**
6. **No manual testing needed - unit tests verify everything**

## Notes

- Each test file should be independent and runnable on its own
- Tests should clean up after themselves
- Use pytest fixtures for common setup
- Add verbose logging to understand failures
- Keep test data minimal but realistic
- Focus on the critical path first, edge cases later