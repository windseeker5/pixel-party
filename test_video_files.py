#!/usr/bin/env python3
# test_video_files.py

import os
from app import create_app, db
from app.models import Photo

def test_video_files():
    """Test that video files and thumbnails exist"""
    app = create_app()
    with app.app_context():
        videos = Photo.query.filter(Photo.file_type == 'video').all()

        results = {
            'total_videos': len(videos),
            'videos_with_files': 0,
            'videos_with_thumbnails': 0,
            'missing_files': [],
            'missing_thumbnails': []
        }

        for video in videos:
            # Check video file exists
            video_path = f"media/photos/{video.filename}"
            if os.path.exists(video_path):
                results['videos_with_files'] += 1
            else:
                results['missing_files'].append(video.filename)

            # Check thumbnail exists
            if video.thumbnail:
                thumb_path = f"media/thumbnails/{video.thumbnail}"
                if os.path.exists(thumb_path):
                    results['videos_with_thumbnails'] += 1
                else:
                    results['missing_thumbnails'].append(video.thumbnail)

        # SUCCESS CRITERIA
        success = (results['videos_with_files'] == results['total_videos'] and
                  results['videos_with_thumbnails'] == results['total_videos'])

        print(f"TEST RESULTS:")
        print(f"✓ Total videos: {results['total_videos']}")
        print(f"{'✓' if results['videos_with_files'] == results['total_videos'] else '✗'} Videos with files: {results['videos_with_files']}/{results['total_videos']}")
        print(f"{'✓' if results['videos_with_thumbnails'] == results['total_videos'] else '✗'} Videos with thumbnails: {results['videos_with_thumbnails']}/{results['total_videos']}")

        if results['missing_files']:
            print(f"✗ MISSING VIDEO FILES: {results['missing_files']}")
        if results['missing_thumbnails']:
            print(f"✗ MISSING THUMBNAIL FILES: {results['missing_thumbnails']}")

        return success

if __name__ == "__main__":
    success = test_video_files()
    exit(0 if success else 1)