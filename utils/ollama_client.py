"""Ollama client for AI music suggestions."""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any
import logging
# Remove Flask dependency to make it testable outside Flask context

class OllamaClient:
    """Simple Ollama client for music suggestions."""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:11434"
        self.model = "llama3.2:1b"
        self.session = None
        self.logger = logging.getLogger(__name__)
    
    async def _get_session(self):
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def list_models(self) -> List[str]:
        """List available models."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return [model['name'] for model in data.get('models', [])]
                return []
        except Exception as e:
            self.logger.error(f"Error listing Ollama models: {e}")
            return []
    
    def is_mood_query(self, query: str) -> bool:
        """Check if the query is a mood-based search."""
        query_lower = query.lower().strip()

        # If query contains specific song/artist indicators, it's NOT a mood query
        song_indicators = [
            'by ', ' - ', "'", '"', 'song', 'track', 'album',
            'don\'t', 'can\'t', 'won\'t', 'i\'m', 'it\'s', 'he\'s', 'she\'s'
        ]

        for indicator in song_indicators:
            if indicator in query_lower:
                return False

        # Check for mood words only if it's not a specific song reference
        mood_words = [
            # Basic emotions (only standalone or with music descriptors)
            'romantic', 'party', 'chill', 'upbeat', 'slow', 'dance', 'happy', 'sad', 'energetic', 'relaxing',
            # Additional feelings
            'melancholic', 'nostalgic', 'groovy', 'mellow', 'peaceful', 'aggressive',
            # Music genres/styles
            'blues', 'jazz', 'rock', 'metal', 'classical', 'country', 'reggae', 'funk', 'soul', 'disco',
            # Contexts
            'birthday', 'road trip', 'workout', 'study', 'dinner', 'morning', 'night', 'cooking'
        ]

        # Check if query is ONLY mood words (not embedded in song titles)
        words = query_lower.split()
        if len(words) <= 3:  # Short queries are more likely to be moods
            return any(word in mood_words for word in words)

        return False

    def get_song_suggestions(self, mood_or_query: str) -> List[Dict[str, Any]]:
        """Get song suggestions synchronously (for Flask routes)."""
        try:
            # Check if there's already a running event loop
            try:
                loop = asyncio.get_running_loop()
                # If there's a running loop, we need to use a different approach
                # Create a new thread to run the async function
                import concurrent.futures
                import threading

                result = []
                exception = None

                def run_async():
                    nonlocal result, exception
                    try:
                        # Create a new event loop for this thread
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            result = new_loop.run_until_complete(self._get_song_suggestions_async(mood_or_query))
                        finally:
                            # Session is handled by the async function
                            new_loop.close()
                    except Exception as e:
                        exception = e

                thread = threading.Thread(target=run_async)
                thread.start()
                thread.join(timeout=30)  # 30 second timeout

                if exception:
                    raise exception

                return result

            except RuntimeError:
                # No running event loop, we can create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._get_song_suggestions_async(mood_or_query))
                finally:
                    # Session is handled by the async function
                    loop.close()

        except Exception as e:
            self.logger.error(f"Error getting song suggestions: {e}")
            return []
    
    async def _get_song_suggestions_async(self, mood_or_query: str) -> List[Dict[str, Any]]:
        """Get song suggestions based on mood or search query."""
        session = None
        try:
            # Create a fresh session for this request to avoid conflicts
            timeout = aiohttp.ClientTimeout(total=10)
            session = aiohttp.ClientSession(timeout=timeout)

            # Detect if it's a mood or artist/song query
            mood_words = [
                # Basic emotions
                'romantic', 'party', 'chill', 'upbeat', 'slow', 'dance', 'happy', 'sad', 'energetic', 'relaxing',
                # Additional feelings
                'melancholic', 'nostalgic', 'groovy', 'mellow', 'peaceful', 'aggressive',
                # Music genres/styles
                'blues', 'jazz', 'rock', 'metal', 'classical', 'country', 'reggae', 'funk', 'soul', 'disco',
                # Contexts
                'birthday', 'road trip', 'workout', 'study', 'dinner', 'morning', 'night', 'cooking'
            ]
            is_mood_query = any(word in mood_or_query.lower() for word in mood_words)

            if is_mood_query:
                # Add some randomness to prevent caching
                import time
                import random
                seed = int(time.time()) % 1000 + random.randint(1, 100)

                prompt = f"""You are a music expert. Generate exactly 5 different songs that perfectly match this specific mood: "{mood_or_query}". Be creative and diverse in your suggestions.

CRITICAL INSTRUCTIONS:
1. Songs MUST match the "{mood_or_query}" mood specifically
2. Return ONLY a valid JSON array
3. Each song must be an object with title, artist, and album fields
4. Provide real, well-known songs
5. Vary genres and artists for diversity

Example JSON format:
[
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}}
]

Request seed: {seed}
Return only the JSON array, no other text."""
            else:
                prompt = f"""You are a music expert. Suggest exactly 5 songs similar to "{mood_or_query}":

IMPORTANT: Respond with ONLY a valid JSON array. Each song must be an object with title, artist, and album fields.

Format:
[
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}}
]

Return only the JSON array, no other text."""

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7
            }

            # Use the session timeout we already set
            async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get('response', '').strip()

                    # Enhanced JSON parsing with better error handling
                    self.logger.info(f"Raw Ollama response for '{mood_or_query}': {response_text[:300]}...")

                    # Try multiple parsing strategies
                    parsing_attempts = []

                    # Strategy 1: Direct JSON parsing
                    try:
                        suggestions = json.loads(response_text)
                        if isinstance(suggestions, list) and len(suggestions) > 0:
                            # Validate first item has required fields
                            if all(key in suggestions[0] for key in ['title', 'artist']):
                                self.logger.info(f"✅ Direct JSON parsing successful: {len(suggestions)} songs")
                                return suggestions[:5]
                        parsing_attempts.append("Direct JSON: Invalid structure")
                    except json.JSONDecodeError as e:
                        parsing_attempts.append(f"Direct JSON: {str(e)[:50]}")

                    # Strategy 2: Markdown code block extraction with truncation handling
                    try:
                        import re
                        # Extract content between ```...``` blocks (or just ``` to end of string if truncated)
                        json_pattern = r'```(?:json)?\s*(.*?)(?:\s*```|$)'
                        match = re.search(json_pattern, response_text, re.DOTALL)
                        if match:
                            json_str = match.group(1).strip()

                            # Handle truncated JSON - try to complete it
                            if not json_str.endswith(']'):
                                # Find complete objects and create valid JSON from them
                                complete_objects = []
                                objects = re.findall(r'\{[^{}]*\}', json_str, re.DOTALL)

                                for obj_str in objects:
                                    try:
                                        # Clean up the object
                                        obj_str = obj_str.strip()
                                        # Remove trailing comma if it exists
                                        if obj_str.endswith(','):
                                            obj_str = obj_str[:-1]

                                        obj = json.loads(obj_str)
                                        if 'title' in obj and 'artist' in obj:
                                            complete_objects.append(obj)
                                    except json.JSONDecodeError:
                                        continue

                                if complete_objects:
                                    self.logger.info(f"✅ Recovered {len(complete_objects)} songs from truncated JSON")
                                    return complete_objects[:5]

                            # Try normal parsing if not truncated
                            try:
                                suggestions = json.loads(json_str)
                                if isinstance(suggestions, list) and len(suggestions) > 0:
                                    if all(isinstance(item, dict) and 'title' in item for item in suggestions):
                                        self.logger.info(f"✅ Markdown JSON parsing successful: {len(suggestions)} songs")
                                        return suggestions[:5]
                            except json.JSONDecodeError:
                                pass

                        parsing_attempts.append("Markdown JSON: No valid content found")
                    except (json.JSONDecodeError, AttributeError) as e:
                        parsing_attempts.append(f"Markdown JSON: {str(e)[:50]}")

                    # Strategy 3: String array parsing
                    try:
                        song_strings = json.loads(response_text)
                        if isinstance(song_strings, list) and all(isinstance(s, str) for s in song_strings):
                            suggestions = []
                            for song_str in song_strings[:5]:
                                if ' by ' in song_str:
                                    parts = song_str.split(' by ', 1)
                                    title = parts[0].strip().strip('"')
                                    artist = parts[1].strip().strip('"')
                                    suggestions.append({
                                        "title": title,
                                        "artist": artist,
                                        "album": "Unknown"
                                    })
                                else:
                                    suggestions.append({
                                        "title": song_str.strip().strip('"'),
                                        "artist": "Unknown",
                                        "album": "Unknown"
                                    })

                            if suggestions:
                                self.logger.info(f"✅ String array parsing successful: {len(suggestions)} songs")
                                return suggestions
                        parsing_attempts.append("String array: Not a string array")
                    except (json.JSONDecodeError, AttributeError) as e:
                        parsing_attempts.append(f"String array: {str(e)[:50]}")

                    # All parsing failed - log details
                    self.logger.error(f"❌ All JSON parsing strategies failed for '{mood_or_query}':")
                    for attempt in parsing_attempts:
                        self.logger.error(f"  - {attempt}")
                    self.logger.error(f"Raw response: {repr(response_text[:500])}")

                    # Return empty list instead of fallback message - let the caller handle this
                    return []

                return []

        except asyncio.TimeoutError:
            self.logger.warning(f"Ollama request timed out for query: {mood_or_query}")
            return []
        except Exception as e:
            self.logger.error(f"Error calling Ollama API: {e}")
            return []
        finally:
            # Always close the session
            if session and not session.closed:
                await session.close()