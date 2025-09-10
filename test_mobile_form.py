#!/usr/bin/env python3
"""
Simple test script to verify mobile form functionality
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5001"

def test_music_search():
    """Test music search endpoint"""
    print("🎵 Testing music search...")
    
    # Test searches
    test_queries = ["bob", "bob dy", "dylan", "hurricane"]
    
    for query in test_queries:
        print(f"\n🔍 Searching for: '{query}'")
        
        response = requests.post(
            f"{BASE_URL}/mobile/search_music",
            data={"query": query},
            headers={"HX-Request": "true"}
        )
        
        if response.status_code == 200:
            content = response.text
            if len(content) > 100:
                print(f"✅ SUCCESS: Got {len(content)} chars of results")
                # Count number of Select buttons (updated for new format)
                select_count = content.count('class="btn btn-primary btn-sm ml-3 select-song-btn"')
                print(f"   📀 Found {select_count} songs with Select buttons")
            else:
                print(f"❌ FAIL: Only got {len(content)} chars: {content[:100]}")
        else:
            print(f"❌ ERROR: Status {response.status_code}")

def test_form_submission():
    """Test complete form submission"""
    print("\n📝 Testing form submission...")
    
    # First search for a song
    search_response = requests.post(
        f"{BASE_URL}/mobile/search_music",
        data={"query": "hurricane"},
        headers={"HX-Request": "true"}
    )
    
    if "Hurricane" in search_response.text:
        print("✅ Music search working")
        
        # Create test song selection JSON (simulate user clicking Select)
        selected_song = json.dumps({
            "title": "Hurricane",
            "artist": "Bob Dylan", 
            "source": "local",
            "file_path": "/mnt/media/MUSIC/Bob Dylan/The Essential (disc 2)/2-02 Hurricane.mp3"
        })
        
        # Test form submission
        form_data = {
            "guest_name": "Test User",
            "wish_message": "Happy Birthday! This is a test message.",
            "selected_song": selected_song
        }
        
        # We can't upload a file in this test, but we can verify the endpoint responds
        submit_response = requests.post(
            f"{BASE_URL}/mobile/submit_memory",
            data=form_data
        )
        
        if submit_response.status_code in [200, 302]:
            print("✅ Form submission endpoint accessible")
        else:
            print(f"❌ Form submission failed: {submit_response.status_code}")
    else:
        print("❌ Music search failed - can't test submission")

def main():
    """Run all tests"""
    print("🧪 Testing PixelParty Mobile Form")
    print("=" * 40)
    
    try:
        # Test if server is running
        response = requests.get(f"{BASE_URL}/mobile/main")
        if response.status_code == 200:
            print("✅ Flask server is running")
        else:
            print("❌ Flask server not responding")
            return
            
        test_music_search()
        test_form_submission()
        
        print("\n" + "=" * 40)
        print("✅ Testing complete!")
        print("\n💡 If music search works in tests but not browser:")
        print("   1. Hard refresh browser: Ctrl+F5")
        print("   2. Clear browser cache")
        print("   3. Try incognito/private mode")
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Can't connect to Flask server")
        print("   Make sure Flask is running on port 5001")

if __name__ == "__main__":
    main()