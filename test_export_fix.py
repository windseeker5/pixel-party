#!/usr/bin/env python
"""Test script to verify photo-music association fix."""

from app import create_app, db
from app.models import Photo, MusicQueue
from datetime import timedelta

app = create_app()

with app.app_context():
    print("=" * 80)
    print("TESTING PHOTO-MUSIC ASSOCIATION FIX")
    print("=" * 80)

    # Get Ken's submissions (guest_id=4)
    photos = Photo.query.filter_by(guest_id=4).order_by(Photo.uploaded_at.asc()).all()
    music_entries = MusicQueue.query.filter_by(guest_id=4).filter(
        MusicQueue.status.in_(['ready', 'completed'])
    ).order_by(MusicQueue.submitted_at.asc()).all()

    print(f"\nFound {len(photos)} photos and {len(music_entries)} music entries for Ken (guest_id=4)\n")

    # Track used music
    used_music_ids = set()

    for photo in photos:
        print(f"\n{'='*60}")
        print(f"Photo ID: {photo.id}")
        print(f"Uploaded: {photo.uploaded_at}")
        print(f"Wish: {photo.wish_message[:50]}...")

        # Try direct link first
        music = MusicQueue.query.filter_by(photo_id=photo.id)\
            .filter(MusicQueue.status.in_(['ready', 'completed']))\
            .first()

        if music:
            print(f"✅ DIRECT LINK: Music ID {music.id} - {music.song_title} by {music.artist}")
        else:
            print("⚠️  No direct link, trying fallback...")

            # Fallback: time-based matching
            time_window_start = photo.uploaded_at - timedelta(minutes=5)
            time_window_end = photo.uploaded_at + timedelta(minutes=5)

            candidates = MusicQueue.query.filter_by(guest_id=photo.guest_id)\
                .filter(MusicQueue.status.in_(['ready', 'completed']))\
                .filter(MusicQueue.submitted_at >= time_window_start)\
                .filter(MusicQueue.submitted_at <= time_window_end)\
                .filter(~MusicQueue.id.in_(used_music_ids) if used_music_ids else True)\
                .all()

            if candidates:
                best_match = None
                min_diff = None
                for candidate in candidates:
                    time_diff = abs((candidate.submitted_at - photo.uploaded_at).total_seconds())
                    if min_diff is None or time_diff < min_diff:
                        min_diff = time_diff
                        best_match = candidate

                if best_match:
                    music = best_match
                    used_music_ids.add(music.id)
                    print(f"✅ FALLBACK MATCH: Music ID {music.id} - {music.song_title} by {music.artist}")
                    print(f"   Time difference: {min_diff:.2f} seconds")
            else:
                print("❌ No music found in time window")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total photos: {len(photos)}")
    print(f"Total music: {len(music_entries)}")
    print(f"Music matched: {len(used_music_ids)}")
    print(f"Music unmatched: {len(music_entries) - len(used_music_ids)}")
    print("\nUnmatched music:")
    for music in music_entries:
        if music.id not in used_music_ids:
            print(f"  - ID {music.id}: {music.song_title} by {music.artist} (submitted: {music.submitted_at})")
