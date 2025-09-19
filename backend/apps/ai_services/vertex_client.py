"""
Vertex AI client wrapper for document analysis using Gemini.
"""
from typing import Dict, Any, Optional, List
import json
import logging
import os
import asyncio
import time
from django.conf import settings
from apps.documents.logging_utils import ai_services_logger, log_performance, log_ai_service_call

# Import Vertex AI modules only if not in test mode
if not (getattr(settings, 'TESTING', False) or os.environ.get('TESTING')):
    try:
        from tenacity import retry, stop_after_attempt, wait_exponential
        import vertexai
        from vertexai.generative_models import GenerativeModel
        from google.auth import default
        from google.auth.exceptions import DefaultCredentialsError
        from django.core.cache import cache
        
        # Test credentials on import
        try:
            credentials, project = default()
            logger = logging.getLogger(__name__)
            logger.info(f"Successfully loaded GCP credentials for project: {project}")
        except DefaultCredentialsError as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"GCP credentials not found: {e}")
            logger.warning("Some features may not work. Please check your GOOGLE_APPLICATION_CREDENTIALS setting.")
            
    except ImportError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to import Vertex AI modules: {e}")
        logger.error("Please ensure google-cloud-aiplatform is installed: pip install google-cloud-aiplatform")
        # Fall back to mocks
        from unittest.mock import Mock
        def retry(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
        stop_after_attempt = Mock()
        wait_exponential = Mock()
        vertexai = Mock()
        GenerativeModel = Mock()
        cache = Mock()
else:
    # Mock for testing
    from unittest.mock import Mock
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    stop_after_attempt = Mock()
    wait_exponential = Mock()
    vertexai = Mock()
    GenerativeModel = Mock()
    cache = Mock()

logger = logging.getLogger(__name__)

class VertexAIClient:
    """
    Wrapper for Vertex AI text generation operations.
    Implements retry logic and structured output handling.
    """
    
    def __init__(self):
        """Initialize Vertex AI client with project settings."""
        # Skip authentication in test mode
        if getattr(settings, 'TESTING', False) or os.environ.get('TESTING'):
            from unittest.mock import Mock
            self.model = Mock()
            self.safety_settings = {}
            self.project_id = "test-project"
            self.location = "us-central1"
        else:
            try:
                # Initialize Vertex AI with credentials
                self.project_id = settings.GOOGLE_CLOUD_PROJECT
                self.location = settings.VERTEX_SETTINGS['location']
                
                if not self.project_id:
                    raise ValueError("GOOGLE_CLOUD_PROJECT not set in environment")
                
                # Initialize Vertex AI
                vertexai.init(
                    project=self.project_id,
                    location=self.location
                )
                
                # Use the newer Gemini model
                model_name = settings.VERTEX_SETTINGS.get('model_id', 'gemini-1.0-pro')
                self.model = GenerativeModel(model_name)
                
                self.safety_settings = settings.VERTEX_SETTINGS.get('safety_settings', {})
                
                logger.info(f"Initialized Vertex AI client for project {self.project_id} in {self.location}")
                
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI client: {e}")
                logger.error("Please check your GCP credentials and project configuration")
                raise
    
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
        Generate text with retry logic using Gemini API.
        
        Args:
            prompt: The input prompt
            max_output_tokens: Optional token limit
            temperature: Optional temperature parameter
            
        Returns:
            Generated text response
        """
        start_time = time.time()
        
        if getattr(settings, 'TESTING', False) or os.environ.get('TESTING'):
            # Return mock response for testing
            return '{"summary": "Mock summary", "detected_language": "en", "confidence": 0.95}'
        
        try:
            # Log request start
            ai_services_logger.info(
                "Starting Vertex AI text generation",
                extra={
                    'max_output_tokens': max_output_tokens,
                    'temperature': temperature,
                    'prompt_length': len(prompt)
                }
            )
            
            # Configure generation parameters
            generation_config = {
                'max_output_tokens': max_output_tokens or settings.VERTEX_SETTINGS['max_output_tokens'],
                'temperature': temperature or settings.VERTEX_SETTINGS['temperature'],
            }
            
            # Generate content using Gemini
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
            )
            
            if not response.text:
                raise ValueError("Empty response from Vertex AI")
            
            duration = time.time() - start_time
            
            # Log successful generation
            log_ai_service_call(
                service="vertex_ai",
                operation="generate_text",
                duration=duration,
                extra={
                    'response_length': len(response.text),
                    'prompt_length': len(prompt),
                    'max_output_tokens': max_output_tokens,
                    'temperature': temperature
                }
            )
                
            return response.text.strip()
            
        except Exception as e:
            duration = time.time() - start_time
            ai_services_logger.error(
                f"Error generating text with Vertex AI: {e}",
                extra={
                    'duration_ms': round(duration * 1000, 2),
                    'prompt_length': len(prompt),
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            raise

    @log_performance("document_analysis")
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
            analysis_type: Type of analysis (summarize, key_points, risks, translate)
            target_language: Optional target language for translation
            
        Returns:
            Structured analysis results
        """
        ai_services_logger.info(
            f"Starting document analysis",
            extra={
                'analysis_type': analysis_type,
                'target_language': target_language,
                'text_length': len(text)
            }
        )
        
        # Route to specific analysis methods
        if analysis_type == 'summarize':
            return await self.summarize_document(text, target_language)
        elif analysis_type == 'key_points':
            return await self.extract_key_points(text, target_language)
        elif analysis_type == 'risks':
            return await self.detect_risks(text, target_language)
        elif analysis_type == 'translate':
            if not target_language:
                raise ValueError("target_language is required for translation analysis")
            return await self.translate_content(text, target_language)
        else:
            # Fallback to legacy method for backward compatibility
            prompt_config = settings.DEFAULT_PROMPT_SETTINGS.get(analysis_type, {})
            if not prompt_config:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")
            
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
        
    @log_performance("document_summarization")
    async def summarize_document(
        self,
        text: str,
        target_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a plain-English summary of a legal document.
        
        Args:
            text: Document text to summarize
            target_language: Optional target language for translation
            
        Returns:
            Dictionary containing summary, detected language, and token usage
        """
        ai_services_logger.info(
            f"Starting document summarization",
            extra={
                'target_language': target_language,
                'text_length': len(text)
            }
        )
        
        # Build the prompt for summarization
        system_prompt = """You are a legal document expert who explains complex legal documents in extremely simple language that a 12-year-old could understand.

Your task is to:
1. Read the legal document carefully
2. Create a summary using very simple words and short sentences
3. Explain what the document is about and what it means for the people involved
4. Avoid legal jargon - use everyday language instead
5. Keep the summary concise but complete

Return your response in the following JSON format:
{
    "detected_language": "en",
    "summary": "Your simple summary here...",
    "confidence": 0.95
}"""

        full_prompt = f"{system_prompt}\n\nDocument text:\n{text[:8000]}"  # Limit text length
        
        if target_language:
            full_prompt += f"\n\nPlease provide the summary in {target_language}."
        
        try:
            # Track token usage
            input_tokens = len(text.split()) + len(system_prompt.split())
            
            response_text = await self._generate_text(
                full_prompt,
                max_output_tokens=1024,
                temperature=0.3
            )
            
            # Parse JSON response
            result = json.loads(response_text)
            
            # Add token usage tracking
            output_tokens = len(response_text.split())
            result['token_usage'] = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens
            }
            
            if target_language:
                result['target_language'] = target_language
            
            ai_services_logger.info(
                f"Summarization completed",
                extra={
                    'tokens_used': result['token_usage']['total_tokens'],
                    'target_language': target_language,
                    'summary_length': len(result.get('summary', ''))
                }
            )
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError("Failed to get valid JSON response from model")
        except Exception as e:
            logger.error(f"Error during summarization: {e}")
            raise

    async def translate_content(
        self,
        content: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate content to target language with support for common legal languages.
        
        Args:
            content: Text content to translate
            target_language: Target language code (EN, ES, FR, DE, etc.)
            source_language: Optional source language code
            
        Returns:
            Dictionary containing original and translated versions
        """
        logger.info(f"Starting translation to {target_language}")
        
        # Supported legal languages
        supported_languages = {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'zh': 'Chinese',
            'ja': 'Japanese'
        }
        
        target_lang_lower = target_language.lower()
        if target_lang_lower not in supported_languages:
            raise ValueError(f"Unsupported target language: {target_language}")
        
        target_lang_name = supported_languages[target_lang_lower]
        
        # Build translation prompt
        system_prompt = f"""You are a professional legal translator. Translate the following legal content to {target_lang_name}.

Requirements:
1. Maintain legal accuracy and terminology
2. Preserve the meaning and intent of the original text
3. Use appropriate legal language for the target language
4. Keep the same structure and formatting

Return your response in the following JSON format:
{{
    "original_language": "detected_language_code",
    "target_language": "{target_lang_lower}",
    "original_content": "original text here...",
    "translated_content": "translated text here...",
    "confidence": 0.95
}}"""

        full_prompt = f"{system_prompt}\n\nContent to translate:\n{content[:6000]}"  # Limit content length
        
        try:
            # Track token usage
            input_tokens = len(content.split()) + len(system_prompt.split())
            
            response_text = await self._generate_text(
                full_prompt,
                max_output_tokens=2048,
                temperature=0.2
            )
            
            # Parse JSON response
            result = json.loads(response_text)
            
            # Add token usage tracking
            output_tokens = len(response_text.split())
            result['token_usage'] = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens
            }
            
            logger.info(f"Translation completed, tokens used: {result['token_usage']['total_tokens']}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError("Failed to get valid JSON response from model")
        except Exception as e:
            logger.error(f"Error during translation: {e}")
            raise

    async def extract_key_points(
        self,
        text: str,
        target_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract key points from legal document with party benefit analysis.
        
        Args:
            text: Document text to analyze
            target_language: Optional target language for results
            
        Returns:
            Dictionary containing key points with party categorization
        """
        logger.info("Starting key points extraction with party analysis")
        
        # Build key points extraction prompt
        system_prompt = """You are a legal analyst who extracts key points from legal documents and identifies which party benefits from each point.

Your task is to:
1. Extract 5-10 most important key points from the document
2. For each key point, determine if it benefits the "first_party" (the party who likely drafted/proposed the document) or "opposing_party" (the other party)
3. Provide a simple explanation for each key point
4. Include character position citations where possible

Return your response in the following JSON format:
{
    "detected_language": "en",
    "key_points": [
        {
            "text": "Monthly rent is $1,200",
            "explanation": "The tenant must pay this amount every month",
            "party_benefit": "opposing_party",
            "citation": "chars:150-180",
            "importance": "high"
        }
    ],
    "confidence": 0.95
}

Party benefit guidelines:
- "first_party": Benefits the party who likely created/proposed the document (landlord in lease, employer in employment contract, etc.)
- "opposing_party": Benefits the other party (tenant, employee, etc.)
- "mutual": Benefits both parties equally"""

        full_prompt = f"{system_prompt}\n\nDocument text:\n{text[:7000]}"  # Limit text length
        
        if target_language:
            full_prompt += f"\n\nPlease provide the key points and explanations in {target_language}."
        
        try:
            # Track token usage
            input_tokens = len(text.split()) + len(system_prompt.split())
            
            response_text = await self._generate_text(
                full_prompt,
                max_output_tokens=1536,
                temperature=0.3
            )
            
            # Parse JSON response
            result = json.loads(response_text)
            
            # Add token usage tracking
            output_tokens = len(response_text.split())
            result['token_usage'] = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens
            }
            
            if target_language:
                result['target_language'] = target_language
            
            logger.info(f"Key points extraction completed, found {len(result.get('key_points', []))} points")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError("Failed to get valid JSON response from model")
        except Exception as e:
            logger.error(f"Error during key points extraction: {e}")
            raise

    async def detect_risks(
        self,
        text: str,
        target_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect risky clauses and analyze potential legal risks in the document.
        
        Args:
            text: Document text to analyze for risks
            target_language: Optional target language for results
            
        Returns:
            Dictionary containing identified risks with severity classification
        """
        logger.info("Starting risk and clause analysis")
        
        # Build risk analysis prompt
        system_prompt = """You are a legal risk analyst who identifies potentially risky or unusual clauses in legal documents.

Your task is to:
1. Identify clauses that could be risky, unfair, or unusual
2. Classify each risk as HIGH, MEDIUM, or LOW severity
3. Provide clear rationale for why each clause is risky
4. Include character position citations where possible
5. Focus on clauses that could cause legal, financial, or operational problems

Return your response in the following JSON format:
{
    "detected_language": "en",
    "risks": [
        {
            "severity": "HIGH",
            "clause": "Landlord may enter without notice",
            "rationale": "This violates tenant privacy rights in most jurisdictions and could lead to legal disputes",
            "location": "chars:500-550",
            "risk_category": "privacy_violation"
        }
    ],
    "risk_summary": {
        "high_risks": 1,
        "medium_risks": 2,
        "low_risks": 1,
        "overall_assessment": "MEDIUM"
    },
    "confidence": 0.90
}

Risk severity guidelines:
- HIGH: Could lead to significant legal liability, financial loss, or regulatory violations
- MEDIUM: Could cause operational problems or minor legal issues
- LOW: Minor concerns or standard but potentially problematic clauses

Risk categories include: privacy_violation, financial_liability, termination_risk, compliance_issue, unfair_terms, ambiguous_language, etc."""

        full_prompt = f"{system_prompt}\n\nDocument text:\n{text[:7000]}"  # Limit text length
        
        if target_language:
            full_prompt += f"\n\nPlease provide the risk analysis and rationale in {target_language}."
        
        try:
            # Track token usage
            input_tokens = len(text.split()) + len(system_prompt.split())
            
            response_text = await self._generate_text(
                full_prompt,
                max_output_tokens=1536,
                temperature=0.2
            )
            
            # Parse JSON response
            result = json.loads(response_text)
            
            # Add token usage tracking
            output_tokens = len(response_text.split())
            result['token_usage'] = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens
            }
            
            if target_language:
                result['target_language'] = target_language
            
            risk_count = len(result.get('risks', []))
            logger.info(f"Risk analysis completed, found {risk_count} potential risks")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError("Failed to get valid JSON response from model")
        except Exception as e:
            logger.error(f"Error during risk analysis: {e}")
            raise

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

# Global client instance - lazy loaded to avoid authentication issues during import
client = None

def get_vertex_client():
    """Get or create the global Vertex AI client instance."""
    global client
    if client is None:
        client = VertexAIClient()
    return client