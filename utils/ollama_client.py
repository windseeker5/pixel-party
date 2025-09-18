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
        return any(word in query.lower() for word in mood_words)

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
                prompt = f"""You are a music expert. Suggest exactly 5 songs that match this mood: "{mood_or_query}"

IMPORTANT: Respond with ONLY a valid JSON array. Each song must be an object with title, artist, and album fields.

Format:
[
  {{"title": "Happy", "artist": "Pharrell Williams", "album": "Girl"}},
  {{"title": "I Gotta Feeling", "artist": "The Black Eyed Peas", "album": "The E.N.D."}},
  {{"title": "Can't Stop the Feeling!", "artist": "Justin Timberlake", "album": "Trolls Soundtrack"}},
  {{"title": "Uptown Funk", "artist": "Mark Ronson ft. Bruno Mars", "album": "Uptown Special"}},
  {{"title": "All About That Bass", "artist": "Meghan Trainor", "album": "Title"}}
]

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

                    # Try to parse the JSON response (handle markdown code blocks)
                    try:
                        # First try direct parsing
                        suggestions = json.loads(response_text)
                        if isinstance(suggestions, list):
                            return suggestions[:5]  # Return up to 5 suggestions
                    except json.JSONDecodeError:
                        # Try to extract JSON from markdown code blocks
                        try:
                            import re
                            # Look for JSON inside ```json``` or ``` blocks
                            json_pattern = r'```(?:json)?\s*(\[.*?\])\s*```'
                            match = re.search(json_pattern, response_text, re.DOTALL)
                            if match:
                                json_str = match.group(1)
                                suggestions = json.loads(json_str)
                                if isinstance(suggestions, list):
                                    return suggestions[:5]
                        except (json.JSONDecodeError, AttributeError):
                            pass

                        # Try to parse if it returned a string array instead of objects
                        try:
                            # Parse as simple string array
                            song_strings = json.loads(response_text)
                            if isinstance(song_strings, list) and all(isinstance(s, str) for s in song_strings):
                                # Convert string array to object format
                                suggestions = []
                                for song_str in song_strings[:5]:
                                    # Try to parse "Title by Artist" format
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
                                        # If no "by" found, treat whole string as title
                                        suggestions.append({
                                            "title": song_str.strip().strip('"'),
                                            "artist": "Unknown",
                                            "album": "Unknown"
                                        })

                                if suggestions:
                                    self.logger.info(f"Successfully parsed string array format: {len(suggestions)} songs")
                                    return suggestions
                        except (json.JSONDecodeError, AttributeError):
                            pass

                        self.logger.warning(f"Could not parse Ollama response as JSON: {response_text[:200]}...")

                        # Fallback: create generic suggestions based on the query
                        return [
                            {"title": f"Memory song for '{mood_or_query}'", "artist": "Various Artists", "album": "AI Suggestion"}
                        ]

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