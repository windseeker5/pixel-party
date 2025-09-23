#!/usr/bin/env python3
"""
Check if thumbnail files exist for videos in the database.
"""

import os
from app import create_app, db
from app.models import Photo
from app.services.file_handler import FileHandler

def check_thumbnail_files():
    """Check which videos have thumbnail records but missing files."""
    app = create_app()
    file_handler = FileHandler()

    with app.app_context():
        # Find all videos
        videos = Photo.query.filter(Photo.file_type == 'video').all()
        print(f"Found {len(videos)} videos in database")

        missing_thumbnails = []
        existing_thumbnails = []

        for video in videos:
            print(f"\nVideo: {video.filename}")
            print(f"  Guest: {video.guest_name}")
            print(f"  Thumbnail DB record: {video.thumbnail}")

            if video.thumbnail:
                thumbnail_path = os.path.join(file_handler.THUMBNAIL_DIR, video.thumbnail)
                if os.path.exists(thumbnail_path):
                    print(f"  ✅ Thumbnail file exists: {thumbnail_path}")
                    existing_thumbnails.append(video)
                else:
                    print(f"  ❌ Thumbnail file MISSING: {thumbnail_path}")
                    missing_thumbnails.append(video)
            else:
                print(f"  ❌ No thumbnail record in database")
                missing_thumbnails.append(video)

        print(f"\nSummary:")
        print(f"  Videos with working thumbnails: {len(existing_thumbnails)}")
        print(f"  Videos with missing thumbnails: {len(missing_thumbnails)}")

        if missing_thumbnails:
            print(f"\nVideos needing thumbnail regeneration:")
            for video in missing_thumbnails:
                print(f"  - {video.filename}")

if __name__ == "__main__":
    check_thumbnail_files()