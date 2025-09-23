#!/usr/bin/env python3
# test_simple_endpoints.py

import requests

BASE_URL = "http://127.0.0.1:5001"

def test_basic_endpoints():
    """Test basic endpoints without admin login"""

    tests_passed = 0
    tests_failed = 0

    # Test 1: Check current photo API works
    print("=== TEST 1: Current Photo API ===")
    try:
        response = requests.get(f"{BASE_URL}/api/current_photo", timeout=5)
        if response.status_code == 200:
            html = response.text
            if '<video' in html and '/media/photos/' in html:
                print("✓ API returns VIDEO tag with correct path")
                tests_passed += 1
            elif '<img' in html and '/media/photos/' in html:
                print("✓ API returns IMAGE tag with correct path (photo in rotation)")
                tests_passed += 1
            else:
                print("✗ API returns unexpected content")
                tests_failed += 1
        else:
            print(f"✗ API failed with status: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"✗ API request failed: {e}")
        tests_failed += 1

    # Test 2: Check thumbnail files are accessible
    print("\n=== TEST 2: Thumbnail File Access ===")
    try:
        # Test a known thumbnail from our database
        test_thumb = "20250922_192322_TestUser_5dd035c4_thumb.jpg"
        response = requests.get(f"{BASE_URL}/media/thumbnails/{test_thumb}", timeout=5)
        if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
            print("✓ Thumbnail files are accessible via HTTP")
            tests_passed += 1
        else:
            print(f"✗ Thumbnail not accessible: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"✗ Thumbnail request failed: {e}")
        tests_failed += 1

    # Test 3: Check video files are accessible
    print("\n=== TEST 3: Video File Access ===")
    try:
        # Test a known video from our database
        test_video = "20250922_192322_TestUser_5dd035c4.mp4"
        response = requests.head(f"{BASE_URL}/media/photos/{test_video}", timeout=5)
        if response.status_code == 200:
            print("✓ Video files are accessible via HTTP")
            tests_passed += 1
        else:
            print(f"✗ Video not accessible: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"✗ Video request failed: {e}")
        tests_failed += 1

    print(f"\n=== SIMPLE TEST RESULTS ===")
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")

    return tests_failed == 0

if __name__ == "__main__":
    success = test_basic_endpoints()
    exit(0 if success else 1)