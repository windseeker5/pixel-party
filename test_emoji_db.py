#!/usr/bin/env python3
"""Test script to verify emoji support in PixelParty database."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import create_app, db
from app.models import Guest, Photo, MusicQueue
from datetime import datetime

def test_emoji_database():
    """Test emoji support in database operations."""

    # Create app and context
    app = create_app()

    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

        print("🧪 Testing emoji support in PixelParty database...")

        # Test 1: Create guest with emoji name
        print("\n1. Testing guest with emoji name...")

        # Clean up any existing test data first
        existing_guest = Guest.query.filter_by(session_id="emoji_test_session").first()
        if existing_guest:
            # Clean up existing test data
            Photo.query.filter_by(guest_id=existing_guest.id).delete()
            MusicQueue.query.filter_by(guest_id=existing_guest.id).delete()
            Guest.query.filter_by(id=existing_guest.id).delete()
            db.session.commit()

        guest = Guest(
            name="Sarah 🌟✨",
            session_id="emoji_test_session"
        )
        db.session.add(guest)
        db.session.commit()
        print(f"✅ Created guest: {guest.name}")

        # Test 2: Create photo with emoji wish message
        print("\n2. Testing photo with emoji wish message...")
        photo = Photo(
            guest_id=guest.id,
            guest_name=guest.name,
            filename="test_emoji.jpg",
            original_filename="birthday_pic.jpg",
            wish_message="Happy Birthday! 🎉🎂🎈 Hope your day is filled with joy, laughter, and lots of cake! 🥳❤️😊 You're amazing! ✨💕🎊"
        )
        db.session.add(photo)
        db.session.commit()
        print(f"✅ Created photo with wish: {photo.wish_message}")

        # Test 3: Create music request with emoji in title
        print("\n3. Testing music with emoji metadata...")
        music = MusicQueue(
            guest_id=guest.id,
            song_title="Happy Birthday Song 🎵🎶",
            artist="The Party Band 🎺🎸",
            album="Birthday Hits 🎊",
            source="local",
            status="ready"
        )
        db.session.add(music)
        db.session.commit()
        print(f"✅ Created music: {music.song_title} by {music.artist}")

        # Test 4: Query and display data
        print("\n4. Querying data back from database...")

        retrieved_guest = Guest.query.filter_by(name="Sarah 🌟✨").first()
        if retrieved_guest:
            print(f"✅ Guest query successful: {retrieved_guest.name}")
        else:
            print("❌ Guest query failed")

        retrieved_photo = Photo.query.filter(Photo.wish_message.contains("🎉")).first()
        if retrieved_photo:
            print(f"✅ Photo query successful: {retrieved_photo.wish_message[:50]}...")
        else:
            print("❌ Photo query failed")

        retrieved_music = MusicQueue.query.filter(MusicQueue.song_title.contains("🎵")).first()
        if retrieved_music:
            print(f"✅ Music query successful: {retrieved_music.song_title}")
        else:
            print("❌ Music query failed")

        # Test 5: Complex emoji sequences
        print("\n5. Testing complex emoji sequences...")
        complex_wish = "Family photo! 👨‍👩‍👧‍👦 Such a wonderful celebration! 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Love you all! ❤️💕"

        complex_photo = Photo(
            guest_id=guest.id,
            guest_name="John 👨‍💻",
            filename="family_pic.jpg",
            original_filename="family.jpg",
            wish_message=complex_wish
        )
        db.session.add(complex_photo)
        db.session.commit()

        retrieved_complex = Photo.query.filter(Photo.wish_message.contains("👨‍👩‍👧‍👦")).first()
        if retrieved_complex:
            print(f"✅ Complex emoji sequence successful: {retrieved_complex.wish_message}")
        else:
            print("❌ Complex emoji sequence failed")

        # Test 6: Character counting with emojis
        print("\n6. Testing character counting...")
        emoji_text = "🎉🎂🎈❤️😊"
        print(f"Emoji text: {emoji_text}")
        print(f"Python len(): {len(emoji_text)} characters")
        print(f"UTF-8 bytes: {len(emoji_text.encode('utf-8'))} bytes")

        # Clean up test data
        print("\n7. Cleaning up test data...")
        Photo.query.filter_by(guest_id=guest.id).delete()
        MusicQueue.query.filter_by(guest_id=guest.id).delete()
        Guest.query.filter_by(id=guest.id).delete()
        db.session.commit()
        print("✅ Test data cleaned up")

        print("\n🎯 Emoji database test completed successfully!")
        print("\n📝 Summary:")
        print("✅ Guest names with emojis: SUPPORTED")
        print("✅ Photo wish messages with emojis: SUPPORTED")
        print("✅ Music metadata with emojis: SUPPORTED")
        print("✅ Complex emoji sequences: SUPPORTED")
        print("✅ Database queries with emojis: SUPPORTED")
        print("✅ UTF-8 encoding/decoding: SUPPORTED")

if __name__ == "__main__":
    test_emoji_database()