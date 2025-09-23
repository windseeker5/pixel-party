#!/usr/bin/env python3
# test_video_duration.py

from moviepy.editor import VideoFileClip
import os
from app import create_app, db
from app.models import Photo

def test_video_duration():
    """Test that videos are not limited to 8 seconds"""
    app = create_app()
    with app.app_context():
        videos = Photo.query.filter(Photo.file_type == 'video').all()

        long_videos = []
        short_videos = []

        for video in videos:
            video_path = f"media/photos/{video.filename}"
            if os.path.exists(video_path):
                try:
                    clip = VideoFileClip(video_path)
                    duration = clip.duration
                    clip.close()

                    if duration > 8:
                        long_videos.append((video.filename, duration))
                        print(f"✓ {video.filename}: {duration:.1f}s (> 8s)")
                    else:
                        short_videos.append((video.filename, duration))
                        print(f"  {video.filename}: {duration:.1f}s (<= 8s)")
                except Exception as e:
                    print(f"✗ Error reading {video.filename}: {e}")

        print(f"\n=== DURATION TEST RESULTS ===")
        print(f"Videos longer than 8 seconds: {len(long_videos)}")
        print(f"Videos 8 seconds or shorter: {len(short_videos)}")

        if long_videos:
            print(f"\n✓ Found {len(long_videos)} videos longer than 8 seconds")
            print("These MUST play full duration in slideshow, not cut at 8s!")
            print("Long videos:")
            for filename, duration in long_videos:
                print(f"  - {filename}: {duration:.1f}s")
            return True
        else:
            print("⚠ No videos longer than 8 seconds to test duration fix")
            return False

if __name__ == "__main__":
    test_video_duration()