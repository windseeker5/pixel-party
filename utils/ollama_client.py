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
        self.model = "deepseek-r1:8b"
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
            
            prompt = f"""Suggest 3 songs for this mood or request: "{mood_or_query}"

Return ONLY a JSON array with this exact format:
[
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
            
            async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get('response', '').strip()
                    
                    # Try to parse the JSON response
                    try:
                        suggestions = json.loads(response_text)
                        if isinstance(suggestions, list):
                            return suggestions[:3]  # Limit to 3 suggestions
                    except json.JSONDecodeError:
                        current_app.logger.warning(f"Could not parse Ollama response as JSON: {response_text}")
                        
                        # Fallback: create generic suggestions based on the query
                        return [
                            {"title": f"Song for '{mood_or_query}'", "artist": "Various Artists", "album": "AI Suggestion"}
                        ]
                
                return []
                
        except Exception as e:
            current_app.logger.error(f"Error calling Ollama API: {e}")
            return []