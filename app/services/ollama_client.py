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
    
    def is_available_sync(self) -> bool:
        """Synchronous version of is_available for Reflex state methods."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    async def get_connection_status(self) -> Dict:
        """Get detailed connection and server status."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    return {
                        'connected': True,
                        'server_url': self.base_url,
                        'model_count': len(models),
                        'models': models,
                        'has_deepseek': any('deepseek' in model.lower() for model in models),
                        'recommended_model': self._get_recommended_model(models),
                        'status': 'Connected'
                    }
                else:
                    return {
                        'connected': False,
                        'server_url': self.base_url,
                        'error': f'Server responded with status {response.status}',
                        'status': f'Error {response.status}'
                    }
        except Exception as e:
            return {
                'connected': False,
                'server_url': self.base_url,
                'error': str(e),
                'status': 'Connection Failed'
            }
    
    def _get_recommended_model(self, available_models: List[str]) -> Optional[str]:
        """Get the recommended model from available models."""
        preferred_models = [
            'deepseek-r1:8b', 'deepseek-r1', 'deepseek-coder:6.7b', 'deepseek-coder',
            'llama3.1:8b', 'llama3.1', 'llama3', 'mistral', 'codellama'
        ]
        
        for preferred in preferred_models:
            matching_model = next(
                (model for model in available_models if preferred in model.lower()), 
                None
            )
            if matching_model:
                return matching_model
        
        return available_models[0] if available_models else None


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
            # Priority order for model selection (DeepSeek models first)
            preferred_models = [
                'deepseek-r1:8b',      # Latest DeepSeek R1 model 
                'deepseek-r1',         # DeepSeek R1 any size
                'deepseek-coder:6.7b', # DeepSeek Coder
                'deepseek-coder',      # DeepSeek Coder any size
                'llama3.1:8b',         # Llama 3.1 8B
                'llama3.1',            # Llama 3.1 any size
                'llama3',              # Llama 3 any size
                'mistral',             # Mistral models
                'codellama'            # CodeLlama models
            ]
            
            # Find the best available model
            for preferred in preferred_models:
                matching_model = next(
                    (model for model in self._available_models if preferred in model.lower()), 
                    None
                )
                if matching_model:
                    self.preferred_model = matching_model
                    break
            
            # Fallback to first available model
            if not self.preferred_model and self._available_models:
                self.preferred_model = self._available_models[0]
        
        logger.info(f"🤖 Using Ollama model: {self.preferred_model}")
        logger.info(f"📋 Available models: {len(self._available_models)} total - {', '.join(self._available_models)}")
        
        # Log if DeepSeek is being used
        if self.preferred_model and 'deepseek' in self.preferred_model.lower():
            logger.info(f"🧠 DeepSeek model detected - Enhanced music suggestions enabled!")
    
    def get_model_info(self) -> Dict:
        """Get information about the current model and connection status."""
        return {
            'current_model': self.preferred_model,
            'available_models': self._available_models,
            'model_count': len(self._available_models),
            'is_deepseek': bool(self.preferred_model and 'deepseek' in self.preferred_model.lower()),
            'model_type': self._get_model_type(self.preferred_model) if self.preferred_model else 'unknown'
        }
    
    def _get_model_type(self, model_name: str) -> str:
        """Determine the type/category of the model."""
        if not model_name:
            return 'unknown'
        
        model_lower = model_name.lower()
        if 'deepseek-r1' in model_lower:
            return 'deepseek-r1'
        elif 'deepseek-coder' in model_lower:
            return 'deepseek-coder'  
        elif 'deepseek' in model_lower:
            return 'deepseek'
        elif 'llama3.1' in model_lower:
            return 'llama3.1'
        elif 'llama3' in model_lower:
            return 'llama3'
        elif 'llama2' in model_lower:
            return 'llama2'
        elif 'mistral' in model_lower:
            return 'mistral'
        elif 'codellama' in model_lower:
            return 'codellama'
        else:
            return 'other'
    
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
    


# Enhanced music suggestion methods with better prompt engineering
async def get_music_suggestions(mood: str, limit: int = 5) -> List[Dict]:
    """Get enhanced music suggestions using DeepSeek/Ollama."""
    try:
        # Initialize if needed
        if not mood_suggester.preferred_model:
            await mood_suggester.initialize()
        
        # Enhanced prompt for DeepSeek R1
        prompt = f"""You are a music expert helping curate the perfect playlist for a 50th birthday party celebration.

MOOD: {mood}

Please suggest {limit} specific songs that match this mood perfectly for the party. Each suggestion should include:
- Song title
- Artist name  
- Brief reason why it fits the mood (max 10 words)

Format your response as a JSON array like this:
[
  {{"title": "Song Name", "artist": "Artist Name", "reason": "Perfect upbeat celebration vibe"}},
  {{"title": "Another Song", "artist": "Another Artist", "reason": "Classic feel-good party anthem"}}
]

Focus on well-known songs that guests aged 25-75 would recognize and enjoy."""

        response = await mood_suggester.ollama_client.generate(
            model=mood_suggester.preferred_model,
            prompt=prompt,
            stream=False
        )
        
        if response and 'response' in response:
            try:
                # Try to parse JSON response
                import json
                suggestions_text = response['response'].strip()
                
                # Clean up the response (remove markdown formatting if present)
                if suggestions_text.startswith('```json'):
                    suggestions_text = suggestions_text.replace('```json', '').replace('```', '').strip()
                elif suggestions_text.startswith('```'):
                    suggestions_text = suggestions_text.replace('```', '').strip()
                
                suggestions = json.loads(suggestions_text)
                
                if isinstance(suggestions, list):
                    # Ensure all suggestions have required fields
                    valid_suggestions = []
                    for suggestion in suggestions[:limit]:
                        if isinstance(suggestion, dict) and 'title' in suggestion and 'artist' in suggestion:
                            if 'reason' not in suggestion:
                                suggestion['reason'] = 'Great party song'
                            valid_suggestions.append(suggestion)
                    
                    if valid_suggestions:
                        return valid_suggestions
            
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract song suggestions from text
                logger.warning("Failed to parse JSON, falling back to text parsing")
                pass
        
        # Fallback to keyword-based suggestions
        keywords = await mood_suggester.suggest_music_keywords(mood)
        return [
            {
                'title': f'Search for "{keyword}"',
                'artist': 'Various Artists',
                'reason': f'Matches {mood} mood'
            }
            for keyword in keywords[:limit]
        ]
        
    except Exception as e:
        logger.error(f"Error getting music suggestions: {e}")
        return []


# Global instances with enhanced configuration
ollama_client = OllamaClient(base_url="http://127.0.0.1:11434")

# Initialize with DeepSeek R1 as preferred model
mood_suggester = MoodMusicSuggester(
    ollama_client, 
    preferred_model="deepseek-r1:8b"  # Explicitly prefer DeepSeek R1
)