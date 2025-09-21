import json
import asyncio
from unittest.mock import patch, MagicMock, Mock, AsyncMock
from django.test import TestCase, override_settings

from .vertex_client import VertexAIClient


class VertexAIClientTestCase(TestCase):
    """Test cases for VertexAIClient."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('apps.ai_services.vertex_client.vertexai'), \
             patch('apps.ai_services.vertex_client.GenerativeModel'):
            self.client = VertexAIClient()
            self.mock_model = Mock()
            self.client.model = self.mock_model
            
        self.test_document_text = """
        This is a sample legal document for testing purposes.
        It contains various clauses and terms that need to be analyzed.
        The document establishes rights and obligations for both parties.
        """
        
        self.mock_summary_response = {
            "detected_language": "en",
            "summary": "This is a simple agreement between two parties that sets up basic rules and responsibilities.",
            "confidence": 0.95
        }
        
        self.mock_key_points_response = {
            "detected_language": "en",
            "key_points": [
                {
                    "text": "Both parties must follow the rules",
                    "explanation": "Everyone has to do what the agreement says",
                    "party_benefit": "mutual",
                    "citation": "chars:50-100",
                    "importance": "high"
                },
                {
                    "text": "Payment due monthly",
                    "explanation": "Money must be paid every month",
                    "party_benefit": "opposing_party",
                    "citation": "chars:150-200",
                    "importance": "high"
                }
            ],
            "confidence": 0.90
        }
        
        self.mock_risks_response = {
            "detected_language": "en",
            "risks": [
                {
                    "severity": "HIGH",
                    "clause": "No refunds allowed",
                    "rationale": "This could be unfair to customers and may violate consumer protection laws",
                    "location": "chars:300-350",
                    "risk_category": "unfair_terms"
                },
                {
                    "severity": "MEDIUM",
                    "clause": "30-day notice required",
                    "rationale": "Standard but could be problematic in urgent situations",
                    "location": "chars:400-450",
                    "risk_category": "operational_risk"
                }
            ],
            "risk_summary": {
                "high_risks": 1,
                "medium_risks": 1,
                "low_risks": 0,
                "overall_assessment": "MEDIUM"
            },
            "confidence": 0.85
        }
        
        self.mock_translation_response = {
            "original_language": "en",
            "target_language": "es",
            "original_content": "This is a legal document",
            "translated_content": "Este es un documento legal",
            "confidence": 0.92
        }
    
    @patch('apps.ai_services.vertex_client.settings')
    @patch.dict('os.environ', {'TESTING': ''}, clear=False)  # Clear TESTING env var for this test
    def test_init_success(self, mock_settings):
        """Test successful VertexAI client initialization."""
        mock_settings.TESTING = False
        mock_settings.GOOGLE_CLOUD_PROJECT = "test-project"
        mock_settings.VERTEX_SETTINGS = {
            'location': 'us-central1',
            'model_id': 'gemini-1.0-pro',
            'safety_settings': {}
        }
        
        with patch('apps.ai_services.vertex_client.vertexai') as mock_vertexai, \
             patch('apps.ai_services.vertex_client.GenerativeModel') as mock_gen_model:
            
            client = VertexAIClient()
            
            # Verify initialization calls
            mock_vertexai.init.assert_called_once_with(
                project="test-project",
                location="us-central1"
            )
            mock_gen_model.assert_called_once_with('gemini-1.0-pro')
    
    @patch('apps.ai_services.vertex_client.settings')
    @patch.dict('os.environ', {'TESTING': ''}, clear=False)  # Clear TESTING env var for this test
    def test_init_missing_project(self, mock_settings):
        """Test initialization failure with missing project."""
        mock_settings.TESTING = False
        mock_settings.GOOGLE_CLOUD_PROJECT = None
        
        with patch('apps.ai_services.vertex_client.vertexai'), \
             patch('apps.ai_services.vertex_client.GenerativeModel'):
            
            with self.assertRaises(ValueError) as context:
                VertexAIClient()
            
            self.assertIn("GOOGLE_CLOUD_PROJECT not set", str(context.exception))
    
    async def test_generate_text_success(self):
        """Test successful text generation."""
        mock_response = Mock()
        mock_response.text = json.dumps(self.mock_summary_response)
        
        # Mock the model's generate_content method
        self.mock_model.generate_content.return_value = mock_response
        
        with patch('apps.ai_services.vertex_client.settings') as mock_settings, \
             patch.dict('os.environ', {'TESTING': ''}, clear=False):
            mock_settings.TESTING = False
            mock_settings.VERTEX_SETTINGS = {
                'max_output_tokens': 1024,
                'temperature': 0.3
            }
            
            result = await self.client._generate_text(
                "Test prompt",
                max_output_tokens=512,
                temperature=0.2
            )
            
            # Verify model call
            self.mock_model.generate_content.assert_called_once()
            call_args = self.mock_model.generate_content.call_args
            
            # Verify prompt
            self.assertEqual(call_args[0][0], "Test prompt")
            
            # Verify generation config
            generation_config = call_args[1]['generation_config']
            self.assertEqual(generation_config['max_output_tokens'], 512)
            self.assertEqual(generation_config['temperature'], 0.2)
            
            # Verify result
            self.assertEqual(result, json.dumps(self.mock_summary_response))
    
    async def test_generate_text_empty_response(self):
        """Test text generation with empty response."""
        mock_response = Mock()
        mock_response.text = ""
        
        self.mock_model.generate_content.return_value = mock_response
        
        with patch('apps.ai_services.vertex_client.settings') as mock_settings, \
             patch.dict('os.environ', {'TESTING': ''}, clear=False):
            mock_settings.TESTING = False
            
            with self.assertRaises(ValueError) as context:
                await self.client._generate_text("Test prompt")
            
            self.assertIn("Empty response from Vertex AI", str(context.exception))
    
    async def test_generate_text_testing_mode(self):
        """Test text generation in testing mode returns mock response."""
        with patch('apps.ai_services.vertex_client.settings') as mock_settings:
            mock_settings.TESTING = True
            
            result = await self.client._generate_text("Test prompt")
            
            # Should return mock response without calling actual model
            self.assertIn("Mock summary", result)
            self.mock_model.generate_content.assert_not_called()
    
    async def test_summarize_document_success(self):
        """Test successful document summarization."""
        mock_response_text = json.dumps(self.mock_summary_response)
        
        with patch.object(self.client, '_generate_text', return_value=mock_response_text) as mock_generate:
            result = await self.client.summarize_document(
                self.test_document_text,
                target_language="es"
            )
            
            # Verify generate_text was called
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            
            # Verify prompt contains system instructions
            prompt = call_args[0][0]
            self.assertIn("12-year-old", prompt)
            self.assertIn("simple language", prompt)
            self.assertIn("JSON format", prompt)
            self.assertIn(self.test_document_text[:8000], prompt)
            self.assertIn("es", prompt)
            
            # Verify generation parameters
            self.assertEqual(call_args[1]['max_output_tokens'], 1024)
            self.assertEqual(call_args[1]['temperature'], 0.3)
            
            # Verify result structure
            self.assertEqual(result['detected_language'], 'en')
            self.assertEqual(result['summary'], self.mock_summary_response['summary'])
            self.assertEqual(result['confidence'], 0.95)
            self.assertEqual(result['target_language'], 'es')
            self.assertIn('token_usage', result)
            self.assertIn('input_tokens', result['token_usage'])
            self.assertIn('output_tokens', result['token_usage'])
    
    async def test_summarize_document_invalid_json(self):
        """Test summarization with invalid JSON response."""
        with patch.object(self.client, '_generate_text', return_value="Invalid JSON response"):
            with self.assertRaises(ValueError) as context:
                await self.client.summarize_document(self.test_document_text)
            
            self.assertIn("Failed to get valid JSON response", str(context.exception))
    
    async def test_translate_content_success(self):
        """Test successful content translation."""
        mock_response_text = json.dumps(self.mock_translation_response)
        
        with patch.object(self.client, '_generate_text', return_value=mock_response_text) as mock_generate:
            result = await self.client.translate_content(
                "This is a legal document",
                "es",
                source_language="en"
            )
            
            # Verify generate_text was called
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            
            # Verify prompt contains translation instructions
            prompt = call_args[0][0]
            self.assertIn("professional legal translator", prompt)
            self.assertIn("Spanish", prompt)
            self.assertIn("This is a legal document", prompt)
            
            # Verify generation parameters
            self.assertEqual(call_args[1]['max_output_tokens'], 2048)
            self.assertEqual(call_args[1]['temperature'], 0.2)
            
            # Verify result structure
            self.assertEqual(result['original_language'], 'en')
            self.assertEqual(result['target_language'], 'es')
            self.assertEqual(result['translated_content'], 'Este es un documento legal')
            self.assertIn('token_usage', result)
    
    async def test_translate_content_unsupported_language(self):
        """Test translation with unsupported language."""
        with self.assertRaises(ValueError) as context:
            await self.client.translate_content(
                "Test content",
                "xyz"  # Unsupported language
            )
        
        self.assertIn("Unsupported target language", str(context.exception))
    
    async def test_extract_key_points_success(self):
        """Test successful key points extraction."""
        mock_response_text = json.dumps(self.mock_key_points_response)
        
        with patch.object(self.client, '_generate_text', return_value=mock_response_text) as mock_generate:
            result = await self.client.extract_key_points(
                self.test_document_text,
                target_language="fr"
            )
            
            # Verify generate_text was called
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            
            # Verify prompt contains key points instructions
            prompt = call_args[0][0]
            self.assertIn("legal analyst", prompt)
            self.assertIn("5-10 most important", prompt)
            self.assertIn("first_party", prompt)
            self.assertIn("opposing_party", prompt)
            self.assertIn(self.test_document_text[:7000], prompt)
            self.assertIn("fr", prompt)
            
            # Verify generation parameters
            self.assertEqual(call_args[1]['max_output_tokens'], 1536)
            self.assertEqual(call_args[1]['temperature'], 0.3)
            
            # Verify result structure
            self.assertEqual(result['detected_language'], 'en')
            self.assertEqual(len(result['key_points']), 2)
            self.assertEqual(result['key_points'][0]['party_benefit'], 'mutual')
            self.assertEqual(result['key_points'][1]['party_benefit'], 'opposing_party')
            self.assertEqual(result['target_language'], 'fr')
            self.assertIn('token_usage', result)
    
    async def test_detect_risks_success(self):
        """Test successful risk detection."""
        mock_response_text = json.dumps(self.mock_risks_response)
        
        with patch.object(self.client, '_generate_text', return_value=mock_response_text) as mock_generate:
            result = await self.client.detect_risks(
                self.test_document_text,
                target_language="de"
            )
            
            # Verify generate_text was called
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            
            # Verify prompt contains risk analysis instructions
            prompt = call_args[0][0]
            self.assertIn("legal risk analyst", prompt)
            self.assertIn("risky, unfair, or unusual", prompt)
            self.assertIn("HIGH, MEDIUM, or LOW", prompt)
            self.assertIn(self.test_document_text[:7000], prompt)
            self.assertIn("de", prompt)
            
            # Verify generation parameters
            self.assertEqual(call_args[1]['max_output_tokens'], 1536)
            self.assertEqual(call_args[1]['temperature'], 0.2)
            
            # Verify result structure
            self.assertEqual(result['detected_language'], 'en')
            self.assertEqual(len(result['risks']), 2)
            self.assertEqual(result['risks'][0]['severity'], 'HIGH')
            self.assertEqual(result['risks'][1]['severity'], 'MEDIUM')
            self.assertEqual(result['risk_summary']['high_risks'], 1)
            self.assertEqual(result['risk_summary']['medium_risks'], 1)
            self.assertEqual(result['target_language'], 'de')
            self.assertIn('token_usage', result)
    
    async def test_analyze_document_summarize(self):
        """Test analyze_document with summarize type."""
        async def mock_summarize_async(*args, **kwargs):
            return self.mock_summary_response
        
        with patch.object(self.client, 'summarize_document', side_effect=mock_summarize_async) as mock_summarize:
            result = await self.client.analyze_document(
                self.test_document_text,
                analysis_type='summarize',
                target_language='es'
            )
            
            # Verify summarize_document was called
            mock_summarize.assert_called_once_with(self.test_document_text, 'es')
            
            # Verify result
            self.assertEqual(result, self.mock_summary_response)
    
    async def test_analyze_document_key_points(self):
        """Test analyze_document with key_points type."""
        async def mock_extract_async(*args, **kwargs):
            return self.mock_key_points_response
        
        with patch.object(self.client, 'extract_key_points', side_effect=mock_extract_async) as mock_extract:
            result = await self.client.analyze_document(
                self.test_document_text,
                analysis_type='key_points',
                target_language='fr'
            )
            
            # Verify extract_key_points was called
            mock_extract.assert_called_once_with(self.test_document_text, 'fr')
            
            # Verify result
            self.assertEqual(result, self.mock_key_points_response)
    
    async def test_analyze_document_risks(self):
        """Test analyze_document with risks type."""
        async def mock_detect_async(*args, **kwargs):
            return self.mock_risks_response
        
        with patch.object(self.client, 'detect_risks', side_effect=mock_detect_async) as mock_detect:
            result = await self.client.analyze_document(
                self.test_document_text,
                analysis_type='risks',
                target_language='de'
            )
            
            # Verify detect_risks was called
            mock_detect.assert_called_once_with(self.test_document_text, 'de')
            
            # Verify result
            self.assertEqual(result, self.mock_risks_response)
    
    async def test_analyze_document_translate(self):
        """Test analyze_document with translate type."""
        async def mock_translate_async(*args, **kwargs):
            return self.mock_translation_response
        
        with patch.object(self.client, 'translate_content', side_effect=mock_translate_async) as mock_translate:
            result = await self.client.analyze_document(
                self.test_document_text,
                analysis_type='translate',
                target_language='es'
            )
            
            # Verify translate_content was called
            mock_translate.assert_called_once_with(self.test_document_text, 'es')
            
            # Verify result
            self.assertEqual(result, self.mock_translation_response)
    
    async def test_analyze_document_translate_missing_language(self):
        """Test analyze_document translate without target language."""
        with self.assertRaises(ValueError) as context:
            await self.client.analyze_document(
                self.test_document_text,
                analysis_type='translate'
            )
        
        self.assertIn("target_language is required for translation", str(context.exception))
    
    async def test_analyze_document_unsupported_type(self):
        """Test analyze_document with unsupported analysis type."""
        with patch('apps.ai_services.vertex_client.settings') as mock_settings:
            mock_settings.DEFAULT_PROMPT_SETTINGS = {}
            
            with self.assertRaises(ValueError) as context:
                await self.client.analyze_document(
                    self.test_document_text,
                    analysis_type='unsupported_type'
                )
            
            self.assertIn("Unsupported analysis type", str(context.exception))
    
    async def test_detect_language_success(self):
        """Test successful language detection."""
        with patch.object(self.client, '_generate_text', return_value="en") as mock_generate:
            result = await self.client.detect_language("This is English text")
            
            # Verify generate_text was called
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            
            # Verify prompt
            prompt = call_args[0][0]
            self.assertIn("ISO 639-1 language code", prompt)
            self.assertIn("This is English text", prompt)
            
            # Verify generation parameters
            self.assertEqual(call_args[1]['max_output_tokens'], 8)
            self.assertEqual(call_args[1]['temperature'], 0.1)
            
            # Verify result
            self.assertEqual(result, "en")
    
    async def test_detect_language_invalid_code(self):
        """Test language detection with invalid response."""
        with patch.object(self.client, '_generate_text', return_value="invalid_long_code"):
            with self.assertRaises(ValueError) as context:
                await self.client.detect_language("Test text")
            
            self.assertIn("Invalid language code received", str(context.exception))
    
    def test_get_vertex_client_singleton(self):
        """Test that get_vertex_client returns singleton instance."""
        from .vertex_client import get_vertex_client
        
        with patch('apps.ai_services.vertex_client.vertexai'), \
             patch('apps.ai_services.vertex_client.GenerativeModel'):
            
            client1 = get_vertex_client()
            client2 = get_vertex_client()
            
            # Should return the same instance
            self.assertIs(client1, client2)


class VertexAIClientIntegrationTestCase(TestCase):
    """Integration tests for VertexAIClient with mocked external dependencies."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        with patch('apps.ai_services.vertex_client.vertexai'), \
             patch('apps.ai_services.vertex_client.GenerativeModel'):
            self.client = VertexAIClient()
            self.mock_model = Mock()
            self.client.model = self.mock_model
    
    async def test_full_analysis_workflow(self):
        """Test complete analysis workflow with all types."""
        # Mock responses for different analysis types
        summary_response = json.dumps({
            "detected_language": "en",
            "summary": "Simple contract summary",
            "confidence": 0.95
        })
        
        key_points_response = json.dumps({
            "detected_language": "en",
            "key_points": [
                {
                    "text": "Payment terms",
                    "explanation": "How money is paid",
                    "party_benefit": "opposing_party",
                    "citation": "chars:100-150",
                    "importance": "high"
                }
            ],
            "confidence": 0.90
        })
        
        risks_response = json.dumps({
            "detected_language": "en",
            "risks": [
                {
                    "severity": "MEDIUM",
                    "clause": "Termination clause",
                    "rationale": "Could be problematic",
                    "location": "chars:200-250",
                    "risk_category": "termination_risk"
                }
            ],
            "risk_summary": {
                "high_risks": 0,
                "medium_risks": 1,
                "low_risks": 0,
                "overall_assessment": "MEDIUM"
            },
            "confidence": 0.85
        })
        
        translation_response = json.dumps({
            "original_language": "en",
            "target_language": "es",
            "original_content": "Contract text",
            "translated_content": "Texto del contrato",
            "confidence": 0.92
        })
        
        # Mock generate_text to return different responses based on prompt content
        def mock_generate_side_effect(prompt, **kwargs):
            if "12-year-old" in prompt:
                return summary_response
            elif "key points" in prompt:
                return key_points_response
            elif "risk analyst" in prompt:
                return risks_response
            elif "translator" in prompt:
                return translation_response
            else:
                return '{"error": "Unknown prompt type"}'
        
        with patch.object(self.client, '_generate_text', side_effect=mock_generate_side_effect):
            document_text = "Sample legal contract with various clauses and terms."
            
            # Test summarization
            summary_result = await self.client.analyze_document(
                document_text,
                analysis_type='summarize'
            )
            self.assertEqual(summary_result['detected_language'], 'en')
            self.assertIn('token_usage', summary_result)
            
            # Test key points extraction
            key_points_result = await self.client.analyze_document(
                document_text,
                analysis_type='key_points'
            )
            self.assertEqual(len(key_points_result['key_points']), 1)
            self.assertIn('token_usage', key_points_result)
            
            # Test risk analysis
            risks_result = await self.client.analyze_document(
                document_text,
                analysis_type='risks'
            )
            self.assertEqual(len(risks_result['risks']), 1)
            self.assertEqual(risks_result['risk_summary']['medium_risks'], 1)
            self.assertIn('token_usage', risks_result)
            
            # Test translation
            translation_result = await self.client.analyze_document(
                document_text,
                analysis_type='translate',
                target_language='es'
            )
            self.assertEqual(translation_result['target_language'], 'es')
            self.assertIn('token_usage', translation_result)
    
    async def test_error_handling_and_retry_logic(self):
        """Test error handling behavior."""
        # Test that exceptions are properly raised and logged
        self.mock_model.generate_content.side_effect = Exception("Service unavailable")
        
        with patch('apps.ai_services.vertex_client.settings') as mock_settings, \
             patch.dict('os.environ', {'TESTING': ''}, clear=False):
            mock_settings.TESTING = False
            mock_settings.VERTEX_SETTINGS = {
                'max_output_tokens': 1024,
                'temperature': 0.3
            }
            
            # Should raise exception
            with self.assertRaises(Exception) as context:
                await self.client._generate_text("Test prompt")
            
            self.assertIn("Service unavailable", str(context.exception))
    
    async def test_token_usage_tracking(self):
        """Test that token usage is properly tracked across different operations."""
        mock_response_text = json.dumps({
            "detected_language": "en",
            "summary": "Test summary with token tracking",
            "confidence": 0.95
        })
        
        with patch.object(self.client, '_generate_text', return_value=mock_response_text):
            document_text = "A" * 1000  # 1000 character document
            
            result = await self.client.summarize_document(document_text)
            
            # Verify token usage is tracked
            self.assertIn('token_usage', result)
            token_usage = result['token_usage']
            
            self.assertIn('input_tokens', token_usage)
            self.assertIn('output_tokens', token_usage)
            self.assertIn('total_tokens', token_usage)
            
            # Verify token counts are reasonable
            self.assertGreater(token_usage['input_tokens'], 0)
            self.assertGreater(token_usage['output_tokens'], 0)
            self.assertEqual(
                token_usage['total_tokens'],
                token_usage['input_tokens'] + token_usage['output_tokens']
            )