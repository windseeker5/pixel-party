#!/usr/bin/env python3
"""
Comprehensive test script for Ollama AI suggestions debugging.
This will help us identify exactly why AI suggestions aren't working.
"""

import asyncio
import aiohttp
import json
import sys
import time
import traceback

def test_ollama_basic_connection():
    """Test basic Ollama server connection."""
    print("=" * 60)
    print("TEST 1: Basic Ollama Connection")
    print("=" * 60)

    import requests
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            print(f"✅ Ollama server is running")
            print(f"📦 Available models: {models}")
            return True, models
        else:
            print(f"❌ Ollama server returned status code: {response.status_code}")
            return False, []
    except Exception as e:
        print(f"❌ Failed to connect to Ollama: {e}")
        return False, []

def test_mood_detection():
    """Test mood detection function."""
    print("\n" + "=" * 60)
    print("TEST 2: Mood Detection")
    print("=" * 60)

    # Import the mood detection function
    sys.path.append('/home/kdresdell/Documents/DEV/PixelParty')
    from utils.ollama_client import OllamaClient

    ollama = OllamaClient()

    test_queries = [
        "happy",
        "romantic songs",
        "upbeat music",
        "Beatles",
        "Let It Be",
        "party vibes",
        "sad music"
    ]

    for query in test_queries:
        is_mood = ollama.is_mood_query(query)
        status = "✅ MOOD" if is_mood else "❌ NOT MOOD"
        print(f"{status}: '{query}' -> {is_mood}")

    return True

async def test_ollama_direct_api():
    """Test direct Ollama API call for song suggestions."""
    print("\n" + "=" * 60)
    print("TEST 3: Direct Ollama API Call")
    print("=" * 60)

    prompt = """Suggest 5 songs that match this mood: "happy"

Return ONLY a JSON array with this exact format:
[
  {"title": "Song Title", "artist": "Artist Name", "album": "Album Name"},
  {"title": "Song Title", "artist": "Artist Name", "album": "Album Name"},
  {"title": "Song Title", "artist": "Artist Name", "album": "Album Name"},
  {"title": "Song Title", "artist": "Artist Name", "album": "Album Name"},
  {"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}
]

No other text, just the JSON array."""

    payload = {
        "model": "llama3.2:1b",
        "prompt": prompt,
        "stream": False,
        "temperature": 0.7
    }

    try:
        timeout = aiohttp.ClientTimeout(total=30)  # Longer timeout for testing
        async with aiohttp.ClientSession(timeout=timeout) as session:
            print(f"🔄 Sending request to Ollama...")
            print(f"📝 Prompt length: {len(prompt)} chars")

            start_time = time.time()
            async with session.post("http://127.0.0.1:11434/api/generate", json=payload) as response:
                elapsed = time.time() - start_time
                print(f"⏱️  Response received in {elapsed:.2f} seconds")
                print(f"📊 HTTP Status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    response_text = data.get('response', '').strip()

                    print(f"📝 Raw response length: {len(response_text)} chars")
                    print(f"📄 First 200 chars: {response_text[:200]}...")
                    print(f"📄 Last 200 chars: ...{response_text[-200:]}")

                    # Try to parse JSON
                    try:
                        suggestions = json.loads(response_text)
                        print(f"✅ JSON parsing successful!")
                        print(f"📋 Suggestions count: {len(suggestions)}")
                        for i, song in enumerate(suggestions):
                            print(f"  {i+1}. {song.get('title', 'N/A')} - {song.get('artist', 'N/A')}")
                        return True, suggestions
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON parsing failed: {e}")
                        print(f"🔧 Trying to extract JSON from markdown...")

                        # Try markdown extraction
                        import re
                        json_pattern = r'```(?:json)?\s*(\[.*?\])\s*```'
                        match = re.search(json_pattern, response_text, re.DOTALL)
                        if match:
                            json_str = match.group(1)
                            try:
                                suggestions = json.loads(json_str)
                                print(f"✅ Markdown JSON extraction successful!")
                                print(f"📋 Suggestions count: {len(suggestions)}")
                                return True, suggestions
                            except json.JSONDecodeError:
                                print(f"❌ Markdown JSON extraction also failed")

                        print(f"🔍 Raw response for debugging:")
                        print(f"'{response_text}'")
                        return False, []
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    return False, []

    except asyncio.TimeoutError:
        print(f"❌ Request timed out after 30 seconds")
        return False, []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False, []

def test_ollama_client_sync():
    """Test the OllamaClient sync wrapper."""
    print("\n" + "=" * 60)
    print("TEST 4: OllamaClient Sync Wrapper")
    print("=" * 60)

    sys.path.append('/home/kdresdell/Documents/DEV/PixelParty')
    from utils.ollama_client import OllamaClient

    ollama = OllamaClient()

    try:
        print(f"🔄 Testing mood detection...")
        is_mood = ollama.is_mood_query("happy")
        print(f"✅ Mood detection: 'happy' -> {is_mood}")

        if is_mood:
            print(f"🔄 Getting song suggestions...")
            start_time = time.time()
            suggestions = ollama.get_song_suggestions("happy")
            elapsed = time.time() - start_time

            print(f"⏱️  Sync call completed in {elapsed:.2f} seconds")
            print(f"📋 Suggestions count: {len(suggestions) if suggestions else 0}")

            if suggestions:
                print(f"✅ Sync wrapper working!")
                for i, song in enumerate(suggestions):
                    print(f"  {i+1}. {song.get('title', 'N/A')} - {song.get('artist', 'N/A')}")
                return True, suggestions
            else:
                print(f"❌ No suggestions returned")
                return False, []
        else:
            print(f"❌ Mood detection failed")
            return False, []

    except Exception as e:
        print(f"❌ OllamaClient error: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False, []

def test_flask_route_simulation():
    """Test the Flask route logic simulation."""
    print("\n" + "=" * 60)
    print("TEST 5: Flask Route Logic Simulation")
    print("=" * 60)

    # Simulate the Flask route logic
    search_query = "happy"

    # Mock Flask app logger
    class MockLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")

    class MockCurrentApp:
        logger = MockLogger()

    # Mock the current_app
    import sys
    sys.path.append('/home/kdresdell/Documents/DEV/PixelParty')

    try:
        from utils.ollama_client import OllamaClient
        ollama = OllamaClient()

        current_app = MockCurrentApp()  # Mock current_app

        current_app.logger.info(f"Getting AI suggestions for: '{search_query}'")

        # First check if this is actually a mood query
        is_mood = ollama.is_mood_query(search_query)
        current_app.logger.info(f"Is mood query: {is_mood}")

        if not is_mood:
            current_app.logger.info(f"'{search_query}' not detected as mood query, skipping AI suggestions")
            return False, "Not a mood query"

        ai_suggestions = ollama.get_song_suggestions(search_query)
        current_app.logger.info(f"Got {len(ai_suggestions) if ai_suggestions else 0} AI suggestions")

        if ai_suggestions:
            print(f"✅ Flask route simulation successful!")
            return True, ai_suggestions
        else:
            print(f"❌ No AI suggestions generated")
            return False, "No suggestions"

    except Exception as e:
        print(f"❌ Flask simulation error: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False, str(e)

async def main():
    """Run all tests."""
    print("🧪 OLLAMA AI SUGGESTIONS COMPREHENSIVE TEST SUITE")
    print("🎯 Goal: Debug why AI suggestions show 'temporarily unavailable'")
    print("")

    results = {}

    # Test 1: Basic connection
    results['connection'], models = test_ollama_basic_connection()

    # Test 2: Mood detection
    results['mood_detection'] = test_mood_detection()

    # Test 3: Direct API call
    results['direct_api'], direct_suggestions = await test_ollama_direct_api()

    # Test 4: Sync wrapper
    results['sync_wrapper'], sync_suggestions = test_ollama_client_sync()

    # Test 5: Flask route simulation
    results['flask_simulation'], flask_result = test_flask_route_simulation()

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
        print("🎉 All tests passed! AI suggestions should be working.")
    else:
        print("🔍 Some tests failed. Check the output above for debugging info.")

        # Specific debugging advice
        if not results['connection']:
            print("💡 Fix: Ensure Ollama server is running on port 11434")
        elif not results['direct_api']:
            print("💡 Fix: Check Ollama model response format or increase timeout")
        elif not results['sync_wrapper']:
            print("💡 Fix: Debug the async/sync conversion in OllamaClient")
        elif not results['flask_simulation']:
            print("💡 Fix: Check Flask integration and error handling")

if __name__ == "__main__":
    asyncio.run(main())