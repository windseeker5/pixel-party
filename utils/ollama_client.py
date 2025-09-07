"""Ollama LLM client for mood-based music suggestions."""

import aiohttp
import asyncio
import json
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with local Ollama server."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        
    async def _get_session(self):
        """Get or create aiohttp session."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def list_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return [model['name'] for model in data.get('models', [])]
                else:
                    logger.error(f"Failed to get models: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error connecting to Ollama: {e}")
            return []
    
    async def generate(self, model: str, prompt: str, stream: bool = False) -> Optional[Dict]:
        """Generate text using Ollama model."""
        try:
            session = await self._get_session()
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 500
                }
            }
            
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    if stream:
                        # Handle streaming response
                        full_response = ""
                        async for line in response.content:
                            if line:
                                try:
                                    chunk = json.loads(line.decode('utf-8'))
                                    if 'response' in chunk:
                                        full_response += chunk['response']
                                    if chunk.get('done', False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                        return {'response': full_response}
                    else:
                        # Handle non-streaming response
                        data = await response.json()
                        return data
                else:
                    logger.error(f"Ollama generate failed: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error generating with Ollama: {e}")
            return None
    
    async def is_available(self) -> bool:
        """Check if Ollama server is available."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except Exception:
            return False


class MoodMusicSuggester:
    """Uses Ollama to suggest music based on mood descriptions."""
    
    def __init__(self, ollama_client: OllamaClient, preferred_model: str = None):
        self.ollama_client = ollama_client
        self.preferred_model = preferred_model
        self._available_models = []
        
    async def initialize(self):
        """Initialize the suggester by checking available models."""
        self._available_models = await self.ollama_client.list_models()
        
        if not self.preferred_model:
            # Try to find a good model for text generation
            for model_name in ['llama2', 'llama3', 'mistral', 'codellama']:
                if any(model_name in model for model in self._available_models):
                    self.preferred_model = next(model for model in self._available_models if model_name in model)
                    break
            
            # Fallback to first available model
            if not self.preferred_model and self._available_models:
                self.preferred_model = self._available_models[0]
        
        logger.info(f"Using model: {self.preferred_model}")
        logger.info(f"Available models: {self._available_models}")
    
    async def suggest_music_keywords(self, mood_description: str) -> List[str]:
        """Convert mood description to music search keywords."""
        if not self.preferred_model:
            logger.warning("No Ollama model available for suggestions")
            return self._fallback_keywords(mood_description)
        
        prompt = f"""Based on the mood description: "{mood_description}"

Please suggest music search keywords that would match this mood. Focus on:
- Genre names (rock, jazz, classical, electronic, etc.)
- Mood descriptors (upbeat, relaxing, energetic, romantic, etc.)
- Artist types (indie, mainstream, instrumental, etc.)

Provide 5-8 relevant keywords separated by commas. Only return the keywords, no explanations.

Keywords:"""
        
        try:
            response = await self.ollama_client.generate(
                model=self.preferred_model,
                prompt=prompt,
                stream=False
            )
            
            if response and 'response' in response:
                # Extract keywords from response
                keywords_text = response['response'].strip()
                keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
                
                # Clean up keywords (remove quotes, extra whitespace, etc.)
                clean_keywords = []
                for keyword in keywords:
                    cleaned = keyword.strip().strip('"').strip("'").strip()
                    if cleaned and len(cleaned) > 1:
                        clean_keywords.append(cleaned)
                
                if clean_keywords:
                    logger.info(f"LLM suggested keywords for '{mood_description}': {clean_keywords}")
                    return clean_keywords[:8]  # Limit to 8 keywords
            
        except Exception as e:
            logger.error(f"Error getting LLM suggestions: {e}")
        
        # Fallback to rule-based keywords
        return self._fallback_keywords(mood_description)
    
    def _fallback_keywords(self, mood_description: str) -> List[str]:
        """Fallback keyword generation when LLM is unavailable."""
        mood_lower = mood_description.lower()
        keywords = []
        
        # Mood-based keyword mapping
        mood_mappings = {
            'happy': ['upbeat', 'pop', 'funk', 'dance', 'cheerful'],
            'sad': ['melancholy', 'blues', 'ballad', 'slow', 'emotional'],
            'energetic': ['rock', 'electronic', 'high-energy', 'fast', 'pump-up'],
            'relaxing': ['ambient', 'chill', 'acoustic', 'soft', 'calm'],
            'romantic': ['love songs', 'romantic', 'slow', 'ballad', 'intimate'],
            'party': ['dance', 'hip-hop', 'pop', 'party', 'celebration'],
            'focus': ['instrumental', 'ambient', 'lo-fi', 'classical', 'concentration'],
            'workout': ['electronic', 'rock', 'high-energy', 'motivational', 'intense']
        }
        
        # Check for mood keywords
        for mood, related_keywords in mood_mappings.items():
            if mood in mood_lower:
                keywords.extend(related_keywords)
        
        # If no specific mood found, use the original description as keywords
        if not keywords:
            # Split description into words and use as keywords
            words = mood_description.split()
            keywords = [word.strip().lower() for word in words if len(word) > 2]
        
        # Remove duplicates and limit
        keywords = list(set(keywords))[:6]
        
        logger.info(f"Fallback keywords for '{mood_description}': {keywords}")
        return keywords
    
    async def get_model_info(self) -> Dict:
        """Get information about available models."""
        return {
            'available_models': self._available_models,
            'preferred_model': self.preferred_model,
            'is_available': len(self._available_models) > 0
        }


# Global instance
ollama_client = OllamaClient()
mood_suggester = MoodMusicSuggester(ollama_client)