#!/usr/bin/env python3
# test_video_display.py

from app import create_app, db
from app.models import Photo
from flask import render_template

def test_video_display():
    """Test what HTML is generated for a video"""
    app = create_app()
    with app.app_context():
        video = Photo.query.filter(Photo.file_type == 'video').first()

        if not video:
            print("No videos found in database!")
            return False

        print(f"Testing video: {video.filename}")
        print(f"File type: {video.file_type}")
        print(f"Duration: {video.duration}s")
        print(f"Thumbnail: {video.thumbnail}")

        # Render the template with this video
        html = render_template('components/photo_display.html', photo=video)

        print("\n=== GENERATED HTML ===")
        print(html)

        # Check if HTML contains video tag
        if '<video' in html:
            print("\n✓ HTML contains VIDEO tag - videos will play!")
            if '/media/photos/' in html:
                print("✓ Video source uses correct path: /media/photos/")
            else:
                print("✗ Video source path is wrong!")
        else:
            print("\n✗ NO VIDEO TAG FOUND - videos will NOT play!")
            if '<img' in html:
                print("  Found IMG tag instead - showing static image!")

        return '<video' in html and '/media/photos/' in html

if __name__ == "__main__":
    success = test_video_display()
    exit(0 if success else 1)