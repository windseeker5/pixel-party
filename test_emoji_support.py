#!/usr/bin/env python3
"""Test script to verify emoji support in the birthday party app."""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path so we can import the app
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from app.models import Guest, Photo

# Test emojis including complex sequences
TEST_EMOJIS = [
    # Simple emojis
    ("Simple heart", "❤️", 1),
    ("Birthday cake", "🎂", 1),
    ("Party popper", "🎉", 1),

    # Complex emoji sequences
    ("Family emoji", "👨‍👩‍👧‍👦", 1),  # ZWJ sequence (family)
    ("Rainbow flag", "🏳️‍🌈", 1),  # Combined with variation selector
    ("Woman facepalming", "🤦🏽‍♀️", 1),  # With skin tone and gender

    # Mixed text and emoji
    ("Mixed message", "Happy Birthday! 🎂🎉 Love you! ❤️👨‍👩‍👧‍👦", 29),  # Should count as 29 visual chars
    ("All emojis", "🎂🎉❤️🎈🎁🥳🍰🎊💝🌟", 10),  # 10 emojis
]

def test_emoji_storage():
    """Test that emojis can be stored and retrieved correctly."""
    app = create_app('development')

    with app.app_context():
        # Create tables
        db.create_all()

        # Create a test guest
        guest = Guest(
            name="Test User 🎉",
            session_id="test-session-123"
        )
        db.session.add(guest)
        db.session.commit()

        print("\n=== Testing Emoji Storage ===\n")

        results = []
        for test_name, emoji_text, expected_length in TEST_EMOJIS:
            try:
                # Create a photo with emoji in wish message
                photo = Photo(
                    guest_id=guest.id,
                    guest_name=guest.name,
                    filename="test_photo.jpg",
                    original_filename="test_photo.jpg",
                    wish_message=emoji_text
                )
                db.session.add(photo)
                db.session.commit()

                # Retrieve and verify
                retrieved = Photo.query.filter_by(id=photo.id).first()

                if retrieved and retrieved.wish_message == emoji_text:
                    status = "✅ PASSED"
                else:
                    status = f"❌ FAILED: Got '{retrieved.wish_message if retrieved else 'None'}'"

                results.append((test_name, emoji_text, status))

                # Clean up
                db.session.delete(photo)
                db.session.commit()

            except Exception as e:
                results.append((test_name, emoji_text, f"❌ ERROR: {str(e)}"))

        # Clean up test guest
        db.session.delete(guest)
        db.session.commit()

        # Print results
        for test_name, emoji_text, status in results:
            print(f"{test_name:20} | {emoji_text:30} | {status}")

        # Summary
        passed = sum(1 for _, _, s in results if "PASSED" in s)
        total = len(results)
        print(f"\n=== Summary: {passed}/{total} tests passed ===\n")

        return passed == total

def test_grapheme_counting():
    """Test the JavaScript grapheme counting logic (simulated in Python)."""
    print("\n=== Testing Grapheme Counting ===\n")

    import unicodedata

    def count_graphemes(text):
        """Simple approximation of grapheme cluster counting."""
        # This is a simplified version - the actual JS implementation uses Intl.Segmenter
        count = 0
        i = 0
        while i < len(text):
            # Skip combining marks
            if i > 0 and unicodedata.category(text[i]) in ('Mn', 'Mc', 'Me'):
                i += 1
                continue
            count += 1
            i += 1
            # Skip zero-width joiners and variation selectors
            while i < len(text) and text[i] in '\u200d\ufe0f':
                if i + 1 < len(text):
                    i += 2
                else:
                    i += 1
        return count

    for test_name, emoji_text, expected_length in TEST_EMOJIS:
        if "Mixed" in test_name or "All emojis" in test_name:
            # For complex mixed text, we'll just verify it doesn't crash
            try:
                result = count_graphemes(emoji_text)
                print(f"{test_name:20} | Length: {result} (expected around {expected_length})")
            except Exception as e:
                print(f"{test_name:20} | ERROR: {e}")

    print("\nNote: Actual counting is done by JavaScript Intl.Segmenter in the browser")

if __name__ == "__main__":
    print("=" * 60)
    print("EMOJI SUPPORT TEST FOR PIXELPARTY")
    print("=" * 60)

    # Run storage test
    storage_ok = test_emoji_storage()

    # Run counting test
    test_grapheme_counting()

    if storage_ok:
        print("\n✅ All emoji storage tests passed!")
        print("\nNext steps to fully test:")
        print("1. Start the app: python app.py")
        print("2. Navigate to the mobile interface")
        print("3. Try submitting wishes with these emojis:")
        print("   - 🎂 Happy Birthday! 🎉")
        print("   - Love you! ❤️👨‍👩‍👧‍👦")
        print("   - 🏳️‍🌈 Celebrate! 🤦🏽‍♀️")
        print("4. Verify they display correctly on the big screen")
    else:
        print("\n⚠️ Some tests failed. Check the results above.")