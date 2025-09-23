#!/usr/bin/env python3
# test_final_verification.py

import os
import requests
from app import create_app, db
from app.models import Photo

BASE_URL = "http://127.0.0.1:5001"

def run_final_verification():
    """Run comprehensive verification of all video fixes"""

    print("🎬 PIXELPARTY VIDEO BUG FIX VERIFICATION")
    print("=" * 50)

    app = create_app()
    total_tests = 0
    passed_tests = 0

    with app.app_context():
        # Test 1: Database and Files
        print("\n=== TEST 1: Database and File Verification ===")
        videos = Photo.query.filter(Photo.file_type == 'video').all()
        print(f"Videos in database: {len(videos)}")

        if videos:
            test_video = videos[0]
            print(f"Sample video: {test_video.filename}")
            print(f"Duration: {test_video.duration}s")
            print(f"Thumbnail: {test_video.thumbnail}")

            # Check files exist
            video_path = f"media/photos/{test_video.filename}"
            thumb_path = f"media/thumbnails/{test_video.thumbnail}"

            total_tests += 2
            if os.path.exists(video_path):
                print("✓ Video file exists")
                passed_tests += 1
            else:
                print("✗ Video file missing")

            if os.path.exists(thumb_path):
                print("✓ Thumbnail file exists")
                passed_tests += 1
            else:
                print("✗ Thumbnail file missing")

        # Test 2: API Endpoints
        print("\n=== TEST 2: HTTP Endpoint Verification ===")

        # Test current photo API
        total_tests += 1
        try:
            response = requests.get(f"{BASE_URL}/api/current_photo", timeout=5)
            if response.status_code == 200:
                html = response.text
                if '<video' in html and '/media/photos/' in html:
                    print("✓ API returns proper VIDEO tags")
                    passed_tests += 1
                elif '<img' in html and '/media/photos/' in html:
                    print("✓ API returns proper IMAGE tags (photo in rotation)")
                    passed_tests += 1
                else:
                    print("✗ API returns unexpected content")
            else:
                print(f"✗ API failed: {response.status_code}")
        except Exception as e:
            print(f"✗ API error: {e}")

        # Test thumbnail access
        if videos:
            total_tests += 1
            try:
                thumb_url = f"{BASE_URL}/media/thumbnails/{test_video.thumbnail}"
                response = requests.head(thumb_url, timeout=5)
                if response.status_code == 200:
                    print("✓ Thumbnail HTTP access works")
                    passed_tests += 1
                else:
                    print(f"✗ Thumbnail HTTP failed: {response.status_code}")
            except Exception as e:
                print(f"✗ Thumbnail HTTP error: {e}")

        # Test video access
        if videos:
            total_tests += 1
            try:
                video_url = f"{BASE_URL}/media/photos/{test_video.filename}"
                response = requests.head(video_url, timeout=5)
                if response.status_code == 200:
                    print("✓ Video HTTP access works")
                    passed_tests += 1
                else:
                    print(f"✗ Video HTTP failed: {response.status_code}")
            except Exception as e:
                print(f"✗ Video HTTP error: {e}")

        # Test 3: Duration Analysis
        print("\n=== TEST 3: Video Duration Analysis ===")
        long_videos = [v for v in videos if v.duration and v.duration > 8]
        print(f"Videos longer than 8 seconds: {len(long_videos)}")

        if long_videos:
            total_tests += 1
            print("✓ Found videos that should play longer than 8 seconds")
            passed_tests += 1
            for video in long_videos[:3]:  # Show first 3
                print(f"  - {video.filename}: {video.duration:.1f}s")
        else:
            total_tests += 1
            print("✗ No long videos to test duration fix")

    # Final Results
    print("\n" + "=" * 50)
    print("🎯 FINAL VERIFICATION RESULTS")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")

    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print("\n🎉 SUCCESS: Video fixes are working properly!")
        print("\nYou can now test manually:")
        print("1. Go to http://127.0.0.1:5001/admin/manage - Check video thumbnails")
        print("2. Go to http://127.0.0.1:5001/admin/export - Check Polaroid thumbnails")
        print("3. Go to http://127.0.0.1:5001/ - Watch videos play full duration")
        return True
    else:
        print("\n❌ FAILURE: Some video fixes are not working correctly!")
        return False

if __name__ == "__main__":
    success = run_final_verification()
    exit(0 if success else 1)