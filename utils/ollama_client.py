"""Ollama client for AI music suggestions."""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any
from flask import current_app

class OllamaClient:
    """Simple Ollama client for music suggestions."""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:11434"
        self.model = "llama3.2:1b"
        self.session = None
    
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
            current_app.logger.error(f"Error listing Ollama models: {e}")
            return []
    
    def get_song_suggestions(self, mood_or_query: str) -> List[Dict[str, Any]]:
        """Get song suggestions synchronously (for Flask routes)."""
        try:
            # Run the async function in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._get_song_suggestions_async(mood_or_query))
            finally:
                # Ensure proper cleanup
                loop.run_until_complete(self.close())
                loop.close()
        except Exception as e:
            current_app.logger.error(f"Error getting song suggestions: {e}")
            return []
    
    async def _get_song_suggestions_async(self, mood_or_query: str) -> List[Dict[str, Any]]:
        """Get song suggestions based on mood or search query."""
        try:
            session = await self._get_session()

            # Detect if it's a mood or artist/song query
            mood_words = ['romantic', 'party', 'chill', 'upbeat', 'slow', 'dance', 'happy', 'sad', 'energetic', 'relaxing']
            is_mood_query = any(word in mood_or_query.lower() for word in mood_words)

            if is_mood_query:
                prompt = f"""Suggest 5 songs that match this mood: "{mood_or_query}"

Return ONLY a JSON array with this exact format:
[
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}}
]

No other text, just the JSON array."""
            else:
                prompt = f"""Suggest 5 songs similar in style to "{mood_or_query}" or that would remind people of memories with this artist/song:

Return ONLY a JSON array with this exact format:
[
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}},
  {{"title": "Song Title", "artist": "Artist Name", "album": "Album Name"}}
]

No other text, just the JSON array."""

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7
            }

            # Add 10-second timeout for Raspberry Pi
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.post(f"{self.base_url}/api/generate", json=payload, timeout=timeout) as response:
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

                        current_app.logger.warning(f"Could not parse Ollama response as JSON: {response_text[:200]}...")

                        # Fallback: create generic suggestions based on the query
                        return [
                            {"title": f"Memory song for '{mood_or_query}'", "artist": "Various Artists", "album": "AI Suggestion"}
                        ]

                return []

        except asyncio.TimeoutError:
            current_app.logger.warning(f"Ollama request timed out for query: {mood_or_query}")
            return []
        except Exception as e:
            current_app.logger.error(f"Error calling Ollama API: {e}")
            return []