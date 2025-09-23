#!/usr/bin/env python3
# test_real_scenario.py

import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "http://127.0.0.1:5001"
ADMIN_PASSWORD = "admin2025"

def test_real_scenario():
    """Test the actual user experience"""

    print("🔥 TESTING REAL SCENARIO - WHAT YOU WILL SEE IN BROWSER")
    print("=" * 60)

    session = requests.Session()

    # Test 1: Admin Login and Manage Page
    print("\n📋 TEST 1: ADMIN MANAGE PAGE")
    print("-" * 40)

    # Login
    login_data = {"password": ADMIN_PASSWORD}
    login_response = session.post(f"{BASE_URL}/admin/login", data=login_data, allow_redirects=True)

    # Get manage page
    manage_response = session.get(f"{BASE_URL}/admin/manage")
    soup = BeautifulSoup(manage_response.text, 'html.parser')

    # Check for video thumbnails
    video_rows = soup.find_all('tr', class_='hover')
    videos_with_thumbs = 0
    videos_with_placeholders = 0

    for row in video_rows:
        row_text = row.get_text()
        if 'video' in row_text.lower() or '.mp4' in row_text:
            # Check if row has an img tag with thumbnail
            img = row.find('img')
            if img:
                src = img.get('src', '')
                if '/media/thumbnails/' in src:
                    videos_with_thumbs += 1
                    print(f"✅ Video has thumbnail: {src.split('/')[-1][:30]}...")
                else:
                    videos_with_placeholders += 1
                    print(f"❌ Video has wrong src: {src}")
            else:
                # Check for placeholder text
                if '📹' in row_text or 'Video Thum' in row_text:
                    videos_with_placeholders += 1
                    print(f"❌ Video showing placeholder text/icon")

    if videos_with_thumbs > 0 and videos_with_placeholders == 0:
        print(f"\n✅ MANAGE PAGE: All {videos_with_thumbs} videos show thumbnails!")
    else:
        print(f"\n❌ MANAGE PAGE BROKEN: {videos_with_placeholders} videos missing thumbnails!")

    # Test 2: Export Page
    print("\n📸 TEST 2: EXPORT/MEMORY BOOK PAGE")
    print("-" * 40)

    export_response = session.get(f"{BASE_URL}/admin/export")
    soup = BeautifulSoup(export_response.text, 'html.parser')

    # Check Polaroid cards
    polaroids = soup.find_all('div', class_='polaroid')
    polaroids_with_thumbs = 0
    polaroids_broken = 0

    for polaroid in polaroids:
        img = polaroid.find('img')
        if img:
            src = img.get('src', '')
            if '/media/thumbnails/' in src:
                polaroids_with_thumbs += 1
                print(f"✅ Polaroid has thumbnail: {src.split('/')[-1][:30]}...")
            elif 'thumbnails/' in src and not src.startswith('/media/'):
                polaroids_broken += 1
                print(f"❌ Polaroid has BROKEN path: {src}")

    if polaroids_with_thumbs > 0 and polaroids_broken == 0:
        print(f"\n✅ EXPORT PAGE: All {polaroids_with_thumbs} Polaroids show thumbnails!")
    else:
        print(f"\n❌ EXPORT PAGE BROKEN: {polaroids_broken} Polaroids have broken images!")

    # Test 3: Slideshow - Multiple Calls
    print("\n🎬 TEST 3: BIG SCREEN SLIDESHOW")
    print("-" * 40)

    videos_found = 0
    images_found = 0
    broken_found = 0

    print("Checking slideshow rotation (10 calls)...")
    for i in range(10):
        response = session.get(f"{BASE_URL}/api/current_photo")
        soup = BeautifulSoup(response.text, 'html.parser')

        video = soup.find('video')
        img = soup.find('img')

        if video:
            src = video.get('src', '')
            if '/media/photos/' in src and '.mp4' in src:
                videos_found += 1
                print(f"  Call {i+1}: ✅ VIDEO playing: {src.split('/')[-1][:30]}...")
            else:
                broken_found += 1
                print(f"  Call {i+1}: ❌ VIDEO with wrong src: {src}")
        elif img:
            src = img.get('src', '')
            if '/media/photos/' in src:
                if '.jpg' in src or '.jpeg' in src or '.png' in src:
                    images_found += 1
                    print(f"  Call {i+1}: ✅ Photo showing: {src.split('/')[-1][:30]}...")
                elif '.mp4' in src:
                    broken_found += 1
                    print(f"  Call {i+1}: ❌ VIDEO AS IMAGE (BROKEN!): {src}")
            elif '/media/thumbnails/' in src:
                broken_found += 1
                print(f"  Call {i+1}: ❌ SHOWING THUMBNAIL INSTEAD OF VIDEO!")

        time.sleep(0.5)

    print(f"\nSlideshow Results:")
    print(f"  Videos playing: {videos_found}")
    print(f"  Photos showing: {images_found}")
    print(f"  Broken displays: {broken_found}")

    if videos_found > 0 and broken_found == 0:
        print("\n✅ SLIDESHOW: Videos are PLAYING as videos!")
    else:
        print("\n❌ SLIDESHOW BROKEN: Videos not playing properly!")

    # Final Summary
    print("\n" + "=" * 60)
    print("🎯 FINAL REAL-WORLD TEST RESULTS")
    print("=" * 60)

    all_good = (
        videos_with_thumbs > 0 and videos_with_placeholders == 0 and
        polaroids_with_thumbs > 0 and polaroids_broken == 0 and
        videos_found > 0 and broken_found == 0
    )

    if all_good:
        print("✅✅✅ ALL 3 ISSUES ARE FIXED! ✅✅✅")
        print("\n1. ✅ Manage page shows video thumbnails")
        print("2. ✅ Export page shows video thumbnails in Polaroids")
        print("3. ✅ Videos PLAY in slideshow (not static images)")
    else:
        print("❌❌❌ SOME ISSUES STILL BROKEN! ❌❌❌")
        if videos_with_placeholders > 0:
            print("1. ❌ Manage page still showing placeholders")
        if polaroids_broken > 0:
            print("2. ❌ Export page still has broken Polaroid thumbnails")
        if broken_found > 0:
            print("3. ❌ Slideshow still showing thumbnails instead of videos")

    return all_good

if __name__ == "__main__":
    success = test_real_scenario()
    exit(0 if success else 1)