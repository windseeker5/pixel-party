#!/usr/bin/env python3
"""Test script to verify video fixes are working correctly."""

import requests
import time
import os
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:5001"
ADMIN_PASSWORD = "admin2025"

def test_admin_login():
    """Test admin login and access to manage page."""
    print("🔐 Testing admin login...")

    # Login to admin
    login_data = {"password": ADMIN_PASSWORD}
    session = requests.Session()

    try:
        response = session.post(f"{BASE_URL}/admin/login", data=login_data)
        if response.status_code == 200:
            print("✅ Admin login successful")
            return session
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Admin login error: {e}")
        return None

def test_admin_manage_page(session):
    """Test admin manage page loads and check for video entries."""
    print("📊 Testing admin manage page...")

    try:
        response = session.get(f"{BASE_URL}/admin/manage")
        if response.status_code == 200:
            print("✅ Admin manage page loads successfully")

            # Check if page contains video-related content
            if "video" in response.text.lower():
                print("✅ Page contains video-related content")
            else:
                print("ℹ️  No video content found on page")

            # Check for thumbnail handling code
            if "video.thumbnail" in response.text or "/media/photos/" in response.text:
                print("✅ Video thumbnail handling code present")
            else:
                print("⚠️  Video thumbnail handling code not found")

            return True
        else:
            print(f"❌ Admin manage page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Admin manage page error: {e}")
        return False

def test_slideshow_page():
    """Test slideshow page for video duration fixes."""
    print("🎬 Testing slideshow page for video duration fixes...")

    try:
        response = requests.get(f"{BASE_URL}/display")
        if response.status_code == 200:
            print("✅ Slideshow page loads successfully")

            # Check if Math.max removal is in place
            content = response.text
            if "Math.max(event.data.duration, defaultSlideshowDuration)" in content:
                print("❌ Video duration is still being forced to minimum (fix not applied)")
                return False
            elif "event.data.duration" in content:
                print("✅ Video duration fix appears to be applied")
                return True
            else:
                print("ℹ️  Video duration handling code not found")
                return True
        else:
            print(f"❌ Slideshow page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Slideshow page error: {e}")
        return False

def test_memory_book_export(session):
    """Test memory book export functionality."""
    print("📚 Testing memory book export...")

    try:
        # Check if export endpoint exists
        response = session.get(f"{BASE_URL}/admin/memory_book")
        if response.status_code == 200:
            print("✅ Memory book page loads successfully")

            # Check for video thumbnail handling in template
            if "photo.file_type == 'video'" in response.text:
                print("✅ Video file type handling found in memory book")
            else:
                print("ℹ️  Video file type handling not found")

            if "photo.thumbnail" in response.text:
                print("✅ Video thumbnail handling found in memory book")
            else:
                print("ℹ️  Video thumbnail handling not found")

            return True
        else:
            print(f"❌ Memory book page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Memory book page error: {e}")
        return False

def check_file_changes():
    """Check if the file changes were actually applied."""
    print("📁 Checking file modifications...")

    # Check slideshow.html for duration fix
    slideshow_path = Path("templates/big_screen/slideshow.html")
    if slideshow_path.exists():
        with open(slideshow_path, 'r') as f:
            content = f.read()
            if "Math.max(event.data.duration, defaultSlideshowDuration)" not in content:
                print("✅ Slideshow duration fix confirmed in file")
            else:
                print("❌ Slideshow duration fix NOT applied in file")
    else:
        print("⚠️  Slideshow file not found")

    # Check manage.html for thumbnail fix
    manage_path = Path("templates/admin/manage.html")
    if manage_path.exists():
        with open(manage_path, 'r') as f:
            content = f.read()
            if "/media/photos/{{ photo.thumbnail }}" in content:
                print("✅ Admin thumbnail fix confirmed in file")
            else:
                print("❌ Admin thumbnail fix NOT applied in file")
    else:
        print("⚠️  Admin manage file not found")

    # Check memory book template for video handling
    memory_book_path = Path("templates/admin/memory_book_standalone.html")
    if memory_book_path.exists():
        with open(memory_book_path, 'r') as f:
            content = f.read()
            if "photo.file_type == 'video'" in content:
                print("✅ Memory book video handling confirmed in file")
            else:
                print("❌ Memory book video handling NOT applied in file")
    else:
        print("⚠️  Memory book template not found")

def main():
    """Run all tests."""
    print("🧪 Starting Video Fixes Test Suite")
    print("=" * 50)

    # First check if files were modified
    check_file_changes()
    print()

    # Test admin access
    session = test_admin_login()
    if not session:
        print("❌ Cannot proceed with admin tests - login failed")
        return

    print()

    # Test admin manage page
    test_admin_manage_page(session)
    print()

    # Test slideshow page
    test_slideshow_page()
    print()

    # Test memory book
    test_memory_book_export(session)
    print()

    print("=" * 50)
    print("🏁 Test suite completed!")

if __name__ == "__main__":
    main()