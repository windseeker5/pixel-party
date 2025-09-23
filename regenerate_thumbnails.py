#!/usr/bin/env python3
"""
Utility script to regenerate thumbnails for videos that don't have them.
"""

import os
import sys
from app import create_app, db
from app.models import Photo
from app.services.file_handler import FileHandler

def regenerate_missing_thumbnails():
    """Find videos without thumbnails and generate them."""
    app = create_app()
    file_handler = FileHandler()

    with app.app_context():
        # Find videos without thumbnails
        videos_without_thumbnails = Photo.query.filter(
            Photo.file_type == 'video',
            Photo.thumbnail == None
        ).all()

        print(f"Found {len(videos_without_thumbnails)} videos without thumbnails")

        if not videos_without_thumbnails:
            print("All videos already have thumbnails!")
            return

        for video in videos_without_thumbnails:
            print(f"\nProcessing: {video.filename} (uploaded by {video.guest_name})")

            # Check if video file exists
            video_path = os.path.join(file_handler.UPLOAD_DIR, video.filename)
            if not os.path.exists(video_path):
                print(f"  ❌ Video file not found: {video_path}")
                continue

            # Generate thumbnail
            try:
                thumbnail_name = file_handler.generate_video_thumbnail(video_path)
                if thumbnail_name:
                    # Update database record
                    video.thumbnail = thumbnail_name
                    db.session.commit()
                    print(f"  ✅ Generated thumbnail: {thumbnail_name}")
                else:
                    print(f"  ❌ Failed to generate thumbnail")
            except Exception as e:
                print(f"  ❌ Error generating thumbnail: {e}")

        print(f"\nThumbnail regeneration complete!")

if __name__ == "__main__":
    regenerate_missing_thumbnails()