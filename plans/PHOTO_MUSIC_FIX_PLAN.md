# Photo Display and Music Fix Plan with Testing Tools

## Date: 2025-01-08
## Status: Ready to Execute

## Issues Found

### 1. Photo Serving Path Error
- **Problem**: Photos are saved to `media/photos/` but Flask looks for them in `app/media/photos/`
- **Error**: `[Errno 2] No such file or directory: '/home/kdresdell/Documents/DEV/PixelParty/app/media/photos/...'`
- **Root Cause**: Config uses relative paths that resolve differently in different parts of the app

### 2. Music Files Not Copying
- **Problem**: Music files are not being copied from `/mnt/media/MUSIC/` to `media/music/`
- **Impact**: Music playback fails even though songs are in queue

### 3. Path Resolution Conflicts
- **Problem**: Multiple conflicting route handlers for media files
- **Locations**:
  - `app/__init__.py`: Generic `/media/<path:filename>` route
  - `app/routes/__init__.py`: Specific `/media/photos/<filename>` and `/media/music/<filename>` routes

## Fixes to Apply

### 1. Fix config.py - Make Paths Absolute
```python
# Change from relative to absolute paths
import os
from pathlib import Path

# Get project root directory
BASE_DIR = Path(__file__).resolve().parent

# Update paths to be absolute
UPLOAD_FOLDER = BASE_DIR / 'media' / 'photos'
VIDEO_FOLDER = BASE_DIR / 'media' / 'videos'
MUSIC_COPY_FOLDER = BASE_DIR / 'media' / 'music'
EXPORT_FOLDER = BASE_DIR / 'export'
```

### 2. Remove Conflicting Routes in app/__init__.py
- Remove lines 43-46 (the generic `/media/<path:filename>` route)
- This eliminates path resolution conflicts

### 3. Fix Photo/Music Serving Routes in app/routes/__init__.py
- Ensure routes use absolute paths from config
- Both `/media/photos/<filename>` and `/media/music/<filename>` should work correctly

### 4. Verify Music File Copying in app/routes/mobile.py
- Ensure file copy operations use absolute paths
- Add debug logging for file operations
- Check permissions and path existence

## Testing Strategy

### 5. Create test_with_curl.sh - Rapid Bash Testing Script
```bash
#!/bin/bash
# Quick endpoint testing with curl

BASE_URL="http://127.0.0.1:5001"
TEST_PHOTO="test_photo.jpg"
TEST_RESULTS="test_results.log"

echo "=== PixelParty Endpoint Testing ===" | tee $TEST_RESULTS

# 1. Test photo upload with music
echo "Testing photo upload with music..." | tee -a $TEST_RESULTS
curl -X POST "$BASE_URL/mobile/submit_memory" \
  -F "guest_name=Test User" \
  -F "wish_message=Test message from curl" \
  -F "photo=@$TEST_PHOTO" \
  -F 'selected_song={"title":"Test Song","artist":"Test Artist","file_path":"test/song.mp3"}' \
  -w "\nHTTP Status: %{http_code}\n" | tee -a $TEST_RESULTS

# 2. Check if photo was saved
echo "Checking if photo exists..." | tee -a $TEST_RESULTS
ls -la media/photos/ | tee -a $TEST_RESULTS

# 3. Check if music was copied
echo "Checking if music was copied..." | tee -a $TEST_RESULTS
ls -la media/music/ | tee -a $TEST_RESULTS

# 4. Test photo serving endpoint
PHOTO_FILE=$(ls media/photos/ | head -1)
echo "Testing photo serving: $PHOTO_FILE" | tee -a $TEST_RESULTS
curl -I "$BASE_URL/media/photos/$PHOTO_FILE" | tee -a $TEST_RESULTS

# 5. Test API endpoints
echo "Testing API endpoints..." | tee -a $TEST_RESULTS
curl -s "$BASE_URL/api/stats" | python -m json.tool | tee -a $TEST_RESULTS
curl -s "$BASE_URL/api/photos/queue" | python -m json.tool | tee -a $TEST_RESULTS
curl -s "$BASE_URL/api/music/current" | python -m json.tool | tee -a $TEST_RESULTS

echo "=== Testing Complete ===" | tee -a $TEST_RESULTS
```

### 6. Create test_endpoints.py - Python Testing Script
```python
#!/usr/bin/env python3
"""
Rapid endpoint testing for PixelParty
Tests all critical functionality without UI interaction
"""

import requests
import json
import os
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:5001"
TEST_PHOTO = "test_photo.jpg"

class PixelPartyTester:
    def __init__(self):
        self.session = requests.Session()
        self.results = []
        
    def test_photo_upload(self):
        """Test photo upload with music selection"""
        print("📸 Testing photo upload with music...")
        
        # Create test photo if doesn't exist
        if not os.path.exists(TEST_PHOTO):
            with open(TEST_PHOTO, 'wb') as f:
                f.write(b'FAKE_JPEG_DATA')
        
        with open(TEST_PHOTO, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'guest_name': 'Python Test User',
                'wish_message': 'Test from Python script!',
                'selected_song': json.dumps({
                    'title': 'Test Song',
                    'artist': 'Test Artist',
                    'file_path': 'rock/test.mp3',
                    'source': 'local'
                })
            }
            
            response = self.session.post(f"{BASE_URL}/mobile/submit_memory", 
                                        files=files, data=data)
            
            self.results.append({
                'test': 'photo_upload',
                'status': response.status_code,
                'success': response.status_code in [200, 302]
            })
            
            return response.status_code in [200, 302]
    
    def test_file_existence(self):
        """Check if files were created in correct directories"""
        print("📁 Checking file existence...")
        
        photos_exist = len(list(Path('media/photos').glob('*'))) > 0
        music_exist = len(list(Path('media/music').glob('*'))) > 0
        
        self.results.append({
            'test': 'photos_saved',
            'success': photos_exist
        })
        
        self.results.append({
            'test': 'music_copied',
            'success': music_exist
        })
        
        return photos_exist
    
    def test_photo_serving(self):
        """Test if photos are served correctly"""
        print("🖼️ Testing photo serving...")
        
        # Get first photo from directory
        photos = list(Path('media/photos').glob('*'))
        if not photos:
            print("  ❌ No photos to test")
            return False
            
        photo_name = photos[0].name
        response = self.session.get(f"{BASE_URL}/media/photos/{photo_name}")
        
        self.results.append({
            'test': 'photo_serving',
            'status': response.status_code,
            'success': response.status_code == 200
        })
        
        return response.status_code == 200
    
    def test_api_endpoints(self):
        """Test all API endpoints"""
        print("🔌 Testing API endpoints...")
        
        endpoints = [
            '/api/stats',
            '/api/photos/queue',
            '/api/music/current',
            '/api/music_queue'
        ]
        
        all_success = True
        for endpoint in endpoints:
            response = self.session.get(f"{BASE_URL}{endpoint}")
            success = response.status_code == 200
            all_success = all_success and success
            
            self.results.append({
                'test': f'api_{endpoint}',
                'status': response.status_code,
                'success': success
            })
            
            if success and endpoint == '/api/stats':
                stats = response.json()
                print(f"  📊 Stats: {stats}")
        
        return all_success
    
    def test_music_search(self):
        """Test music search functionality"""
        print("🎵 Testing music search...")
        
        response = self.session.post(f"{BASE_URL}/mobile/search_music",
                                    json={'query': 'rock'})
        
        success = response.status_code == 200
        if success:
            results = response.json().get('results', [])
            print(f"  Found {len(results)} songs")
        
        self.results.append({
            'test': 'music_search',
            'status': response.status_code,
            'success': success
        })
        
        return success
    
    def run_all_tests(self):
        """Run all tests and report results"""
        print("\n" + "="*50)
        print("🚀 Starting PixelParty Endpoint Tests")
        print("="*50 + "\n")
        
        # Run tests
        self.test_photo_upload()
        time.sleep(1)  # Give server time to process
        self.test_file_existence()
        self.test_photo_serving()
        self.test_api_endpoints()
        self.test_music_search()
        
        # Report results
        print("\n" + "="*50)
        print("📋 Test Results Summary")
        print("="*50)
        
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result.get('status', 'N/A')}")
        
        print(f"\n🏁 Tests Passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 All tests passed!")
        else:
            print("⚠️ Some tests failed. Check logs above.")
        
        return passed == total

if __name__ == "__main__":
    tester = PixelPartyTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
```

## Expected Outcomes

After implementing these fixes:

1. ✅ Photos will display correctly on the big screen
2. ✅ Thumbnails will show in the photo queue
3. ✅ Music files will copy to `media/music/` folder
4. ✅ Music playback will work on the big screen
5. ✅ All API endpoints will return correct data
6. ✅ Testing can be done in seconds instead of minutes

## Testing Procedure

1. Apply all fixes
2. Restart Flask server
3. Run `python test_endpoints.py` for comprehensive testing
4. Or run `./test_with_curl.sh` for quick bash testing
5. Verify all tests pass
6. Do one manual test to confirm UI works

## Risk Assessment

- **Low Risk**: Path fixes are straightforward
- **Medium Risk**: Music file copying may have permission issues
- **Mitigation**: Test scripts will quickly identify any remaining issues

## Time Estimate

- Fixes: 5-10 minutes
- Testing: 2-3 minutes
- Total: < 15 minutes

## Notes

- Tests are designed to be fast and repeatable
- No Playwright or manual testing required
- Clear pass/fail indicators
- Can be run after any code change for quick validation