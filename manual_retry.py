#!/usr/bin/env python3
"""Manual script to retry failed YouTube downloads directly."""

import os
import sys
import threading
import time
from pathlib import Path

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load debug configuration
from debug_config import setup_debug_environment
setup_debug_environment()

from app import create_app, db
from app.models import MusicQueue
from app.services.youtube_service import get_youtube_service

def retry_youtube_download(music_id):
    """Retry a failed YouTube download manually."""

    app = create_app()

    with app.app_context():
        # Get the music entry
        music = MusicQueue.query.get(music_id)
        if not music:
            print(f"❌ Music ID {music_id} not found")
            return

        print(f"🎵 Found: '{music.song_title}' by '{music.artist}' (Status: {music.status})")

        if music.status not in ['error', 'pending']:
            print(f"⚠️  Music is not in error/pending status, skipping")
            return

        # Update status to pending
        music.status = 'pending'
        db.session.commit()
        print(f"📝 Updated status to 'pending'")

        # Start download
        youtube_service = get_youtube_service()

        # Search for the song
        search_query = f"{music.song_title} {music.artist}".strip()
        print(f"🔍 Searching YouTube for: '{search_query}'")

        try:
            results = youtube_service.search_youtube(search_query, max_results=1)

            if not results:
                print(f"❌ No YouTube results found for: {search_query}")
                music.status = 'error'
                db.session.commit()
                return

            video_url = results[0]['url']
            title = results[0]['title']
            artist = results[0]['artist']

            print(f"✅ Found video: {video_url}")
            print(f"   Title: {title}")
            print(f"   Artist: {artist}")

            # Download the audio
            print(f"⬇️  Starting download...")
            filename = youtube_service.download_audio(video_url, title, artist)

            if filename:
                music.filename = filename
                music.status = 'completed'
                print(f"✅ Download successful: {filename}")
            else:
                music.status = 'error'
                print(f"❌ Download failed")

            db.session.commit()

        except Exception as e:
            print(f"❌ Error during retry: {type(e).__name__}: {e}")
            music.status = 'error'
            db.session.commit()
            import traceback
            traceback.print_exc()


def main():
    """Main function to retry failed downloads."""

    if len(sys.argv) < 2:
        print("Usage: python manual_retry.py <music_id> [music_id2] ...")
        print("\nTo see failed songs:")
        print("sqlite3 data/birthday_party.db \"SELECT id, song_title, artist, status FROM music_queue WHERE status IN ('error', 'pending');\"")
        sys.exit(1)

    music_ids = [int(x) for x in sys.argv[1:]]

    print(f"🔄 Manual retry script starting...")
    print(f"📋 Will retry music IDs: {music_ids}")
    print("=" * 60)

    for music_id in music_ids:
        print(f"\n🎯 Processing Music ID: {music_id}")
        retry_youtube_download(music_id)

        # Small delay between retries
        if len(music_ids) > 1:
            time.sleep(2)

    print("\n" + "=" * 60)
    print("🏁 Manual retry script completed")


if __name__ == "__main__":
    main()