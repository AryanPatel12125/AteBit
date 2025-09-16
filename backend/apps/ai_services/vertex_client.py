"""
Vertex AI client wrapper for document analysis using Gemini.
"""
from typing import Dict, Any, Optional, List
import json
from tenacity import retry, stop_after_attempt, wait_exponential
import vertexai
from vertexai.language_models import TextGenerationModel
from django.conf import settings
from django.core.cache import cache

class VertexAIClient:
    """
    Wrapper for Vertex AI text generation operations.
    Implements retry logic and structured output handling.
    """
    
    def __init__(self):
        """Initialize Vertex AI client with project settings."""
        vertexai.init(
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.VERTEX_SETTINGS['location']
        )
        self.model = TextGenerationModel.from_pretrained(
            settings.VERTEX_SETTINGS['model_id']
        )
        self.safety_settings = settings.VERTEX_SETTINGS['safety_settings']
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _generate_text(
        self,
        prompt: str,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate text with retry logic.
        
        Args:
            prompt: The input prompt
            max_output_tokens: Optional token limit
            temperature: Optional temperature parameter
            
        Returns:
            Generated text response
        """
        parameters = {
            'max_output_tokens': max_output_tokens or settings.VERTEX_SETTINGS['max_output_tokens'],
            'temperature': temperature or settings.VERTEX_SETTINGS['temperature'],
        }
        
        response = await self.model.predict_async(
            prompt,
            **parameters
        )
        return response.text

    async def analyze_document(
        self,
        text: str,
        analysis_type: str = 'summarize',
        target_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze document text using specified analysis type.
        
        Args:
            text: Document text to analyze
            analysis_type: Type of analysis (summarize, key_points, risks)
            target_language: Optional target language for translation
            
        Returns:
            Structured analysis results
        """
        # Get prompt settings
        prompt_config = settings.DEFAULT_PROMPT_SETTINGS.get(analysis_type, {})
        system_prompt = prompt_config['system_prompt']
        
        # Build full prompt
        full_prompt = f"{system_prompt}\n\nDocument text:\n{text}"
        if target_language:
            full_prompt += f"\n\nPlease provide the response in {target_language}."
        
        # Add JSON structure requirement
        full_prompt += "\n\nProvide your response in valid JSON format."
        
        # Generate and parse response
        try:
            response_text = await self._generate_text(
                full_prompt,
                max_output_tokens=prompt_config.get('max_tokens'),
            )
            
            # Parse JSON response
            result = json.loads(response_text)
            
            # Add metadata
            result['analysis_type'] = analysis_type
            if target_language:
                result['target_language'] = target_language
            
            return result
            
        except json.JSONDecodeError:
            raise ValueError("Failed to get valid JSON response from model")
        
    async def detect_language(self, text: str) -> str:
        """
        Detect the language of input text.
        
        Args:
            text: Text to analyze
            
        Returns:
            ISO 639-1 language code
        """
        prompt = """
        Analyze the following text and return only the ISO 639-1 language code.
        Return just the 2-letter code with no other text or formatting.
        
        Text to analyze:
        {}
        """.format(text[:1000])  # Only use first 1000 chars for detection
        
        response = await self._generate_text(
            prompt,
            max_output_tokens=8,
            temperature=0.1
        )
        
        # Clean and validate response
        lang_code = response.strip().lower()
        if len(lang_code) != 2:
            raise ValueError("Invalid language code received")
            
        return lang_code

# Global client instance
client = VertexAIClient()