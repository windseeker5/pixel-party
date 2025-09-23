#!/usr/bin/env python3
# test_video_endpoints.py

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://127.0.0.1:5001"
ADMIN_PASSWORD = "admin2025"

def test_endpoints():
    """Test video display on all endpoints"""
    session = requests.Session()

    # Login to admin
    print("=== LOGGING INTO ADMIN ===")
    login_response = session.post(f"{BASE_URL}/admin/login",
                                  data={"password": ADMIN_PASSWORD})

    if login_response.status_code != 200:
        print(f"✗ Admin login failed: {login_response.status_code}")
        return False

    tests_passed = 0
    tests_failed = 0

    # Test 1: Check manage page has video thumbnails
    print("\n=== TEST 1: Admin Manage Page ===")
    manage_response = session.get(f"{BASE_URL}/admin/manage")
    soup = BeautifulSoup(manage_response.text, 'html.parser')

    # Look for video thumbnails
    video_thumbs = soup.find_all('img', src=lambda x: x and '/media/thumbnails/' in x)
    if video_thumbs:
        print(f"✓ Found {len(video_thumbs)} video thumbnails on manage page")
        tests_passed += 1
    else:
        print("✗ NO VIDEO THUMBNAILS FOUND on manage page!")
        # Look for placeholder text
        video_placeholders = soup.find_all(text=lambda x: x and 'video' in x.lower())
        if video_placeholders:
            print(f"  Found placeholder text: {video_placeholders}")
        tests_failed += 1

    # Test 2: Check export page has video thumbnails
    print("\n=== TEST 2: Admin Export Page ===")
    export_response = session.get(f"{BASE_URL}/admin/export")
    soup = BeautifulSoup(export_response.text, 'html.parser')

    video_thumbs = soup.find_all('img', src=lambda x: x and '/media/thumbnails/' in x)
    if video_thumbs:
        print(f"✓ Found {len(video_thumbs)} video thumbnails on export page")
        tests_passed += 1
    else:
        print("✗ NO VIDEO THUMBNAILS FOUND on export page!")
        # Check for broken images
        broken_imgs = soup.find_all('img', src=lambda x: x and 'thumbnails/' in x and not x.startswith('/media/'))
        if broken_imgs:
            print(f"  Found broken thumbnail paths: {[img.get('src') for img in broken_imgs]}")
        tests_failed += 1

    # Test 3: Check slideshow has VIDEO tags not IMG tags for videos
    print("\n=== TEST 3: Big Screen Slideshow ===")
    slideshow_response = session.get(f"{BASE_URL}/api/current_photo")
    soup = BeautifulSoup(slideshow_response.text, 'html.parser')

    video_tags = soup.find_all('video')
    if video_tags:
        print(f"✓ Found VIDEO tag in slideshow (videos will play)")
        # Check video source
        for video in video_tags:
            src = video.get('src', '')
            if '/media/photos/' in src:
                print(f"  ✓ Video source correct: {src}")
                tests_passed += 1
            else:
                print(f"  ✗ Video source WRONG: {src}")
                tests_failed += 1
    else:
        # Check if it's showing an image instead
        img_tags = soup.find_all('img')
        if img_tags:
            for img in img_tags:
                src = img.get('src', '')
                if '/media/thumbnails/' in src:
                    print(f"✗ CRITICAL: Slideshow showing THUMBNAIL IMAGE instead of VIDEO: {src}")
                    tests_failed += 1
                elif '/media/photos/' in src:
                    print(f"  Found photo image (this is OK): {src}")
        else:
            print("⚠ No media currently in slideshow rotation")

    print(f"\n=== FINAL RESULTS ===")
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")

    return tests_failed == 0

if __name__ == "__main__":
    success = test_endpoints()
    exit(0 if success else 1)