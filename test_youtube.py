#!/usr/bin/env python3
"""
YouTube functionality test script for PixelParty debugging.
Tests the YouTube search and download functionality in isolation.
"""

import os
import sys
import json
import logging
from pathlib import Path
from debug_config import setup_debug_environment

def test_imports():
    """Test if all required imports work."""
    print("🔍 Testing imports...")

    try:
        import yt_dlp
        print(f"✅ yt-dlp version: {yt_dlp.version.__version__ if hasattr(yt_dlp, 'version') else 'unknown'}")
    except ImportError as e:
        print(f"❌ yt-dlp import failed: {e}")
        return False

    try:
        import mutagen
        print(f"✅ mutagen version: {mutagen.version}")
    except ImportError as e:
        print(f"❌ mutagen import failed: {e}")
        return False

    try:
        from app.services.youtube_service import YouTubeAudioService
        print("✅ YouTubeAudioService import successful")
    except ImportError as e:
        print(f"❌ YouTubeAudioService import failed: {e}")
        return False

    return True

def test_yt_dlp_basic():
    """Test basic yt-dlp functionality."""
    print("\n🎵 Testing basic yt-dlp functionality...")

    try:
        import yt_dlp

        # Test basic search without download
        search_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        test_query = "ytsearch3:happy birthday song"

        with yt_dlp.YoutubeDL(search_opts) as ydl:
            info = ydl.extract_info(test_query, download=False)

            if info and 'entries' in info:
                print(f"✅ Found {len(info['entries'])} results for test search")
                for i, entry in enumerate(info['entries'][:2]):
                    if entry:
                        print(f"   {i+1}. {entry.get('title', 'No title')} ({entry.get('id', 'No ID')})")
                return True
            else:
                print("❌ No search results returned")
                return False

    except Exception as e:
        print(f"❌ yt-dlp basic test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_youtube_service():
    """Test the YouTubeAudioService class."""
    print("\n🎵 Testing YouTubeAudioService...")

    try:
        # Setup Flask app context for the service
        from app import create_app
        app = create_app('development')

        with app.app_context():
            from app.services.youtube_service import YouTubeAudioService

            # Create service instance
            youtube_service = YouTubeAudioService()
            print(f"✅ Service created. Output dir: {youtube_service.output_dir}")

            # Test search functionality
            print("\n🔍 Testing search functionality...")
            test_queries = [
                "happy birthday song",
                "Beatles Let It Be",
                "Ed Sheeran Perfect"
            ]

            for query in test_queries:
                print(f"\n   Testing query: '{query}'")
                try:
                    results = youtube_service.search_youtube(query, max_results=2)
                    if results:
                        print(f"   ✅ Found {len(results)} results")
                        for i, result in enumerate(results):
                            print(f"      {i+1}. {result.get('title', 'No title')} by {result.get('artist', 'Unknown')}")
                            print(f"         Duration: {result.get('duration_formatted', 'Unknown')}")
                    else:
                        print(f"   ⚠️  No results for '{query}'")
                except Exception as e:
                    print(f"   ❌ Search failed for '{query}': {e}")

            return True

    except Exception as e:
        print(f"❌ YouTubeAudioService test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_download_functionality():
    """Test YouTube download functionality with a short video."""
    print("\n⬇️ Testing download functionality...")

    try:
        from app import create_app
        app = create_app('development')

        with app.app_context():
            from app.services.youtube_service import YouTubeAudioService

            youtube_service = YouTubeAudioService()

            # Use a very short video for testing (YouTube audio library)
            test_video_url = "https://www.youtube.com/watch?v=4fkYIO6Hlqs"  # Short happy birthday
            test_title = "Happy Birthday Test"
            test_artist = "Test Artist"

            print(f"   Testing download of: {test_video_url}")
            print(f"   Title: {test_title}, Artist: {test_artist}")

            filename = youtube_service.download_audio(test_video_url, test_title, test_artist)

            if filename:
                output_file = youtube_service.output_dir / filename
                if output_file.exists():
                    print(f"   ✅ Download successful: {filename}")
                    print(f"   File size: {output_file.stat().st_size / 1024:.1f} KB")

                    # Test metadata
                    try:
                        from mutagen.mp3 import MP3
                        audio = MP3(str(output_file))
                        if audio.info:
                            print(f"   Duration: {int(audio.info.length)} seconds")
                        if audio.tags:
                            print(f"   Tags: {dict(audio.tags)}")
                    except Exception as e:
                        print(f"   ⚠️  Could not read metadata: {e}")

                    # Clean up test file
                    try:
                        output_file.unlink()
                        print(f"   🧹 Cleaned up test file")
                    except Exception as e:
                        print(f"   ⚠️  Could not clean up test file: {e}")

                    return True
                else:
                    print(f"   ❌ Downloaded file not found: {filename}")
                    return False
            else:
                print(f"   ❌ Download failed")
                return False

    except Exception as e:
        print(f"❌ Download test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_ollama_connection():
    """Test Ollama connection for music suggestions."""
    print("\n🤖 Testing Ollama connection...")

    try:
        import requests

        ollama_url = os.environ.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')

        # Test basic connection
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)

        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"✅ Ollama connected. Available models: {len(models)}")

            # Check for the preferred model
            preferred_model = 'deepseek-r1:8b'
            model_names = [model.get('name', '') for model in models]
            if preferred_model in model_names:
                print(f"✅ Preferred model '{preferred_model}' is available")
            else:
                print(f"⚠️  Preferred model '{preferred_model}' not found")
                print(f"   Available models: {model_names}")

            return True
        else:
            print(f"❌ Ollama connection failed: HTTP {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False

def test_directory_permissions():
    """Test if the output directory has proper permissions."""
    print("\n📁 Testing directory permissions...")

    try:
        from app import create_app
        app = create_app('development')

        with app.app_context():
            music_dir = Path(app.config.get('MUSIC_COPY_FOLDER', 'media/music'))

            print(f"   Music directory: {music_dir}")
            print(f"   Exists: {music_dir.exists()}")

            if music_dir.exists():
                print(f"   Readable: {os.access(music_dir, os.R_OK)}")
                print(f"   Writable: {os.access(music_dir, os.W_OK)}")

                # Test write permission
                test_file = music_dir / "test_write.txt"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                    print(f"   ✅ Write test successful")
                    return True
                except Exception as e:
                    print(f"   ❌ Write test failed: {e}")
                    return False
            else:
                print(f"   ❌ Directory does not exist")
                return False

    except Exception as e:
        print(f"❌ Directory permissions test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 PixelParty YouTube Functionality Tests")
    print("=" * 50)

    # Setup environment
    setup_debug_environment()

    # Setup logging for tests
    logging.basicConfig(level=logging.INFO)

    # Run tests
    tests = [
        ("Import Tests", test_imports),
        ("yt-dlp Basic Test", test_yt_dlp_basic),
        ("Directory Permissions", test_directory_permissions),
        ("Ollama Connection", test_ollama_connection),
        ("YouTube Service Search", test_youtube_service),
        ("YouTube Download", test_download_functionality),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{'='*50}")
    print("📊 Test Summary:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All tests passed! YouTube functionality should work.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    return passed == len(results)

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)