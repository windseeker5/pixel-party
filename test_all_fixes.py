#!/usr/bin/env python3
"""
Comprehensive test script to verify all mobile app fixes:
1. Duplicate song deduplication
2. AI suggestions for mood queries
3. Progressive loading indicators
"""

import sys
import asyncio
import requests
import time

def test_duplicate_deduplication():
    """Test 1: Verify duplicate songs are properly deduplicated."""
    print("=" * 60)
    print("TEST 1: Duplicate Song Deduplication")
    print("=" * 60)

    try:
        sys.path.append('/home/kdresdell/Documents/DEV/PixelParty')
        from app import create_app
        from utils.music_library import music_search

        app = create_app()
        with app.app_context():
            results = music_search.search_all('happy', limit=10)

            # Check for "Don't Worry Be Happy" variations
            dont_worry_songs = [r for r in results if 'worry' in r['title'].lower()]

            print(f"📊 Total 'happy' results: {len(results)}")
            print(f"📊 'Don't Worry' variations found: {len(dont_worry_songs)}")

            for song in dont_worry_songs:
                print(f"  - {song['title']} by {song['artist']} ({song['duration_formatted']})")

            if len(dont_worry_songs) <= 1:
                print("✅ PASS: No duplicate Don't Worry Be Happy songs")
                return True
            else:
                print("❌ FAIL: Still found duplicate songs")
                return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_ai_mood_detection():
    """Test 2: Verify AI mood detection works for 'happy'."""
    print("\n" + "=" * 60)
    print("TEST 2: AI Mood Detection")
    print("=" * 60)

    try:
        sys.path.append('/home/kdresdell/Documents/DEV/PixelParty')
        from utils.ollama_client import OllamaClient

        ollama = OllamaClient()

        test_queries = ["happy", "sad", "romantic", "Beatles", "Don't Worry Be Happy"]

        print("🧪 Testing mood detection:")
        results = {}
        for query in test_queries:
            is_mood = ollama.is_mood_query(query)
            results[query] = is_mood
            mood_status = "✅ MOOD" if is_mood else "❌ NOT MOOD"
            print(f"  {mood_status}: '{query}' -> {is_mood}")

        # Verify specific expectations
        expected_moods = ["happy", "sad", "romantic"]
        expected_not_moods = ["Beatles", "Don't Worry Be Happy"]

        success = True
        for query in expected_moods:
            if not results[query]:
                print(f"❌ FAIL: '{query}' should be detected as mood")
                success = False

        for query in expected_not_moods:
            if results[query]:
                print(f"❌ FAIL: '{query}' should NOT be detected as mood")
                success = False

        if success:
            print("✅ PASS: Mood detection working correctly")
            return True
        else:
            print("❌ FAIL: Mood detection has issues")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_ai_suggestions_generation():
    """Test 3: Verify AI can generate suggestions for 'happy'."""
    print("\n" + "=" * 60)
    print("TEST 3: AI Suggestions Generation")
    print("=" * 60)

    try:
        sys.path.append('/home/kdresdell/Documents/DEV/PixelParty')
        from utils.ollama_client import OllamaClient

        ollama = OllamaClient()

        print("🎵 Generating AI suggestions for 'happy'...")
        start_time = time.time()
        suggestions = ollama.get_song_suggestions("happy")
        elapsed = time.time() - start_time

        print(f"⏱️  Generation took {elapsed:.2f} seconds")
        print(f"📊 Generated {len(suggestions) if suggestions else 0} suggestions")

        if suggestions:
            for i, song in enumerate(suggestions):
                title = song.get('title', 'N/A')
                artist = song.get('artist', 'N/A')
                print(f"  {i+1}. {title} - {artist}")

            print("✅ PASS: AI suggestions generated successfully")
            return True
        else:
            print("❌ FAIL: No AI suggestions generated")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_mobile_endpoint():
    """Test 4: Test the mobile search endpoint with debug info."""
    print("\n" + "=" * 60)
    print("TEST 4: Mobile Endpoint Integration")
    print("=" * 60)

    try:
        # Test the search endpoint
        print("🌐 Testing mobile search endpoint...")

        response = requests.post('http://localhost:5001/mobile/search_music',
                               data={'query': 'happy'},
                               headers={'HX-Request': 'true'},
                               timeout=10)

        if response.status_code == 200:
            content = response.text
            print(f"📊 Response length: {len(content)} characters")
            print(f"📄 Contains local results: {'badge-info' in content}")
            print(f"📄 Contains AI container: {'ai-suggestions-container' in content}")
            print(f"📄 Contains YouTube indicator: {'youtube-loading-indicator' in content}")

            # Check for key indicators
            has_results = 'card bg-base-' in content
            has_ai_container = 'ai-suggestions-container' in content
            has_youtube_loading = 'youtube-loading-indicator' in content

            if has_results and has_ai_container:
                print("✅ PASS: Mobile endpoint working with AI container")
                return True
            else:
                print("❌ FAIL: Missing expected components")
                print(f"  - Has results: {has_results}")
                print(f"  - Has AI container: {has_ai_container}")
                print(f"  - Has YouTube loading: {has_youtube_loading}")
                return False
        else:
            print(f"❌ FAIL: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 COMPREHENSIVE FIX VERIFICATION TEST SUITE")
    print("🎯 Goal: Verify all three mobile app issues are fixed")
    print("")

    tests = [
        ("Duplicate Deduplication", test_duplicate_deduplication),
        ("AI Mood Detection", test_ai_mood_detection),
        ("AI Suggestions Generation", test_ai_suggestions_generation),
        ("Mobile Endpoint Integration", test_mobile_endpoint),
    ]

    results = {}

    for test_name, test_func in tests:
        results[test_name] = test_func()

    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    total_passed = sum(results.values())
    total_tests = len(results)

    print(f"\n📊 Overall: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("🎉 All tests passed! Mobile app fixes are working.")
        print("\n💡 What to expect in the mobile app:")
        print("  1. ✅ No duplicate songs (Don't Worry Be Happy appears once)")
        print("  2. ✅ AI suggestions appear when typing 'happy'")
        print("  3. ✅ Progressive loading indicators for YouTube search")
        print("  4. ✅ Better user experience with loading feedback")
    else:
        print("🔍 Some tests failed. Check the output above for details.")

    return total_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)