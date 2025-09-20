"""
Test cases for document serializers.

Tests all serializers including:
- DocumentSerializer and DocumentListSerializer
- DocumentUploadSerializer
- AnalysisRequestSerializer and AnalysisResultSerializer
- DocumentAnalysisSerializer
"""
import uuid
from unittest.mock import Mock
from io import BytesIO
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError

from .serializers import (
    DocumentSerializer,
    DocumentListSerializer,
    DocumentUploadSerializer,
    AnalysisRequestSerializer,
    AnalysisResultSerializer,
    DocumentAnalysisSerializer
)
from .models import Document, Analysis


class DocumentSerializerTests(TestCase):
    """Test cases for DocumentSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.document_id = uuid.uuid4()
        self.owner_uid = "test-user-123"
        
        self.valid_data = {
            'document_id': str(self.document_id),
            'title': 'Test Legal Document',
            'file_type': 'application/pdf'
        }
        
        self.document = Document.objects.create(
            document_id=self.document_id,
            title='Test Legal Document',
            owner_uid=self.owner_uid,
            file_type='application/pdf',
            storage_path='test/path'
        )
    
    def test_serialize_document(self):
        """Test document serialization."""
        serializer = DocumentSerializer(self.document)
        data = serializer.data
        
        self.assertEqual(data['document_id'], str(self.document_id))
        self.assertEqual(data['title'], 'Test Legal Document')
        self.assertEqual(data['file_type'], 'application/pdf')
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_validate_document_id(self):
        """Test document_id validation."""
        # Valid UUID
        serializer = DocumentSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Invalid UUID
        invalid_data = self.valid_data.copy()
        invalid_data['document_id'] = 'invalid-uuid'
        serializer = DocumentSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('document_id', serializer.errors)
    
    def test_validate_title(self):
        """Test title validation."""
        # Empty title
        invalid_data = self.valid_data.copy()
        invalid_data['title'] = ''
        serializer = DocumentSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        
        # Title too long
        invalid_data['title'] = 'x' * 256
        serializer = DocumentSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        
        # Whitespace-only title
        invalid_data['title'] = '   '
        serializer = DocumentSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
    
    def test_validate_file_type(self):
        """Test file_type validation."""
        # Valid file type
        serializer = DocumentSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Invalid file type
        invalid_data = self.valid_data.copy()
        invalid_data['file_type'] = 'application/exe'
        serializer = DocumentSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('file_type', serializer.errors)
    
    def test_create_document_with_context(self):
        """Test document creation with request context."""
        # Mock request with user_uid
        mock_request = Mock()
        mock_request.user_uid = self.owner_uid
        
        serializer = DocumentSerializer(
            data=self.valid_data,
            context={'request': mock_request}
        )
        
        self.assertTrue(serializer.is_valid())
        # Note: We can't actually call create() here because it would try to
        # interact with Firestore, but we can test validation
    
    def test_create_document_without_auth(self):
        """Test document creation without authentication."""
        serializer = DocumentSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        # This would raise ValidationError in create() method
        # but we can't test that without mocking Firestore


class DocumentListSerializerTests(TestCase):
    """Test cases for DocumentListSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.document_id = uuid.uuid4()
        self.owner_uid = "test-user-123"
        
        self.document = Document.objects.create(
            document_id=self.document_id,
            title='Test Document',
            owner_uid=self.owner_uid,
            file_type='application/pdf',
            storage_path='test/path',
            extracted_text='Long extracted text content...'
        )
    
    def test_serialize_document_list(self):
        """Test document list serialization excludes heavy fields."""
        serializer = DocumentListSerializer(self.document)
        data = serializer.data
        
        # Should include basic fields
        self.assertEqual(data['document_id'], str(self.document_id))
        self.assertEqual(data['title'], 'Test Document')
        self.assertEqual(data['file_type'], 'application/pdf')
        
        # Should exclude heavy fields
        self.assertNotIn('extracted_text', data)


class DocumentUploadSerializerTests(TestCase):
    """Test cases for DocumentUploadSerializer."""
    
    def create_test_file(self, filename="test.pdf", content=b"PDF content", content_type="application/pdf"):
        """Create a test file for upload."""
        return SimpleUploadedFile(filename, content, content_type=content_type)
    
    def test_validate_file_success(self):
        """Test successful file validation."""
        test_file = self.create_test_file()
        serializer = DocumentUploadSerializer(data={'file': test_file})
        
        self.assertTrue(serializer.is_valid())
    
    def test_validate_file_no_file(self):
        """Test validation when no file provided."""
        serializer = DocumentUploadSerializer(data={})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)
    
    def test_validate_file_too_large(self):
        """Test validation of file size limit."""
        # Create file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)
        large_file = self.create_test_file(content=large_content)
        
        serializer = DocumentUploadSerializer(data={'file': large_file})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)
        self.assertIn('exceeds maximum allowed size', str(serializer.errors['file'][0]))
    
    def test_validate_file_unsupported_extension(self):
        """Test validation of unsupported file extensions."""
        exe_file = self.create_test_file(
            filename="malware.exe",
            content=b"MZ\x90\x00",
            content_type="application/x-executable"
        )
        
        serializer = DocumentUploadSerializer(data={'file': exe_file})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)
        self.assertIn('Unsupported file extension', str(serializer.errors['file'][0]))
    
    def test_validate_file_unsupported_mime_type(self):
        """Test validation of unsupported MIME types."""
        image_file = self.create_test_file(
            filename="image.jpg",
            content=b"\xff\xd8\xff\xe0",
            content_type="image/jpeg"
        )
        
        serializer = DocumentUploadSerializer(data={'file': image_file})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)
        self.assertIn('Unsupported file type', str(serializer.errors['file'][0]))
    
    def test_validate_file_empty(self):
        """Test validation of empty file."""
        empty_file = self.create_test_file(content=b"")
        
        serializer = DocumentUploadSerializer(data={'file': empty_file})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)
        self.assertIn('appears to be empty', str(serializer.errors['file'][0]))
    
    def test_validate_dangerous_filename(self):
        """Test validation of dangerous filenames."""
        dangerous_file = self.create_test_file(filename="../../../etc/passwd")
        
        serializer = DocumentUploadSerializer(data={'file': dangerous_file})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('contains invalid characters', str(serializer.errors))


class AnalysisRequestSerializerTests(TestCase):
    """Test cases for AnalysisRequestSerializer."""
    
    def test_valid_analysis_request(self):
        """Test valid analysis request."""
        valid_data = {
            'analysis_type': 'summary',
            'target_language': 'es',
            'max_summary_length': 300,
            'max_key_points': 8
        }
        
        serializer = AnalysisRequestSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['analysis_type'], 'summary')
        self.assertEqual(validated_data['target_language'], 'es')
        self.assertEqual(validated_data['max_summary_length'], 300)
    
    def test_default_values(self):
        """Test default values for analysis request."""
        minimal_data = {'analysis_type': 'summary'}
        
        serializer = AnalysisRequestSerializer(data=minimal_data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['analysis_type'], 'summary')
        self.assertEqual(validated_data['include_original'], True)
        self.assertEqual(validated_data['max_summary_length'], 500)
        self.assertEqual(validated_data['max_key_points'], 10)
        self.assertEqual(validated_data['risk_threshold'], 'MEDIUM')
    
    def test_invalid_analysis_type(self):
        """Test invalid analysis type."""
        invalid_data = {'analysis_type': 'invalid_type'}
        
        serializer = AnalysisRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('analysis_type', serializer.errors)
    
    def test_invalid_target_language(self):
        """Test invalid target language."""
        invalid_data = {
            'analysis_type': 'summary',
            'target_language': 'invalid_lang'
        }
        
        serializer = AnalysisRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('target_language', serializer.errors)
    
    def test_translation_requires_target_language(self):
        """Test that translation analysis requires target language."""
        invalid_data = {'analysis_type': 'translation'}
        
        serializer = AnalysisRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('target_language is required', str(serializer.errors))
    
    def test_parameter_ranges(self):
        """Test parameter range validation."""
        # Test max_summary_length range
        invalid_data = {
            'analysis_type': 'summary',
            'max_summary_length': 50  # Below minimum
        }
        serializer = AnalysisRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('max_summary_length', serializer.errors)
        
        # Test max_key_points range
        invalid_data = {
            'analysis_type': 'key_points',
            'max_key_points': 25  # Above maximum
        }
        serializer = AnalysisRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('max_key_points', serializer.errors)
    
    def test_legacy_analysis_types_conversion(self):
        """Test conversion of legacy analysis_types array parameter."""
        legacy_data = {
            'analysis_types': ['summary', 'key_points']
        }
        
        serializer = AnalysisRequestSerializer(data=legacy_data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['analysis_type'], 'all')


class AnalysisResultSerializerTests(TestCase):
    """Test cases for AnalysisResultSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.document_id = uuid.uuid4()
        
        self.valid_data = {
            'document_id': self.document_id,
            'version': 1,
            'detected_language': 'en',
            'target_language': 'es',
            'summary': {'en': 'English summary', 'es': 'Resumen en español'},
            'key_points': [
                {
                    'text': 'Important clause',
                    'explanation': 'This is important',
                    'party_benefit': 'first_party',
                    'citation': 'chars:10-25'
                }
            ],
            'risk_alerts': [
                {
                    'severity': 'HIGH',
                    'clause': 'Risky clause',
                    'rationale': 'This could cause problems',
                    'location': 'chars:50-75'
                }
            ],
            'token_usage': {'input_tokens': 100, 'output_tokens': 50},
            'confidence': 0.95,
            'completion_time': '2023-01-01T12:00:00Z'
        }
    
    def test_serialize_analysis_result(self):
        """Test analysis result serialization."""
        serializer = AnalysisResultSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Test serialized output
        validated_data = serializer.validated_data
        self.assertEqual(str(validated_data['document_id']), str(self.document_id))
        self.assertEqual(validated_data['version'], 1)
        self.assertIn('summary', validated_data)
        self.assertIn('key_points', validated_data)
        self.assertIn('risk_alerts', validated_data)
    
    def test_validate_summary_structure(self):
        """Test summary structure validation."""
        # Invalid summary (not a dict)
        invalid_data = self.valid_data.copy()
        invalid_data['summary'] = "Not a dictionary"
        
        serializer = AnalysisResultSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('summary', serializer.errors)
        
        # Empty summary
        invalid_data['summary'] = {}
        serializer = AnalysisResultSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('summary', serializer.errors)
    
    def test_validate_key_points_structure(self):
        """Test key points structure validation."""
        # Invalid key points (not a list)
        invalid_data = self.valid_data.copy()
        invalid_data['key_points'] = "Not a list"
        
        serializer = AnalysisResultSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('key_points', serializer.errors)
        
        # Missing required fields in key point
        invalid_data['key_points'] = [{'text': 'Missing other fields'}]
        serializer = AnalysisResultSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('key_points', serializer.errors)
        
        # Invalid party_benefit value
        invalid_data['key_points'] = [
            {
                'text': 'Test',
                'explanation': 'Test',
                'party_benefit': 'invalid_party',
                'citation': 'test'
            }
        ]
        serializer = AnalysisResultSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('key_points', serializer.errors)
    
    def test_validate_risk_alerts_structure(self):
        """Test risk alerts structure validation."""
        # Invalid risk alerts (not a list)
        invalid_data = self.valid_data.copy()
        invalid_data['risk_alerts'] = "Not a list"
        
        serializer = AnalysisResultSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('risk_alerts', serializer.errors)
        
        # Invalid severity value
        invalid_data['risk_alerts'] = [
            {
                'severity': 'INVALID',
                'clause': 'Test',
                'rationale': 'Test',
                'location': 'test'
            }
        ]
        serializer = AnalysisResultSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('risk_alerts', serializer.errors)
    
    def test_validate_token_usage_structure(self):
        """Test token usage structure validation."""
        # Invalid token usage (not a dict)
        invalid_data = self.valid_data.copy()
        invalid_data['token_usage'] = "Not a dictionary"
        
        serializer = AnalysisResultSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('token_usage', serializer.errors)
        
        # Missing required fields
        invalid_data['token_usage'] = {'input_tokens': 100}  # Missing output_tokens
        serializer = AnalysisResultSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('token_usage', serializer.errors)
        
        # Negative token values
        invalid_data['token_usage'] = {'input_tokens': -10, 'output_tokens': 50}
        serializer = AnalysisResultSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('token_usage', serializer.errors)
    
    def test_to_representation_adds_computed_fields(self):
        """Test that to_representation adds computed fields."""
        serializer = AnalysisResultSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Get representation
        representation = serializer.to_representation(serializer.validated_data)
        
        # Should add total_tokens
        self.assertIn('total_tokens', representation)
        self.assertEqual(representation['total_tokens'], 150)  # 100 + 50
        
        # Should convert document_id to string
        self.assertIsInstance(representation['document_id'], str)


class DocumentAnalysisSerializerTests(TestCase):
    """Test cases for DocumentAnalysisSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.document_id = uuid.uuid4()
        self.owner_uid = "test-user-123"
        
        # Create document
        self.document = Document.objects.create(
            document_id=self.document_id,
            title='Test Document',
            owner_uid=self.owner_uid,
            file_type='application/pdf',
            storage_path='test/path'
        )
        
        # Create analysis
        self.analysis = Analysis.objects.create(
            document_id=self.document_id,
            version=1,
            summary={'en': 'Test summary'},
            key_points=[{'text': 'Key point'}],
            risk_alerts=[{'severity': 'HIGH', 'clause': 'Risk'}],
            token_usage={'input_tokens': 100, 'output_tokens': 50}
        )
    
    def test_serialize_document_with_analysis(self):
        """Test serialization of document with analysis."""
        serializer = DocumentAnalysisSerializer(self.document)
        data = serializer.data
        
        # Should include document data
        self.assertIn('document', data)
        self.assertEqual(data['document']['document_id'], str(self.document_id))
        
        # Should include analysis data
        self.assertIn('analysis', data)
        self.assertIsNotNone(data['analysis'])
        self.assertEqual(data['analysis']['version'], 1)
    
    def test_serialize_document_without_analysis(self):
        """Test serialization of document without analysis."""
        # Delete the analysis
        self.analysis.delete()
        
        serializer = DocumentAnalysisSerializer(self.document)
        data = serializer.data
        
        # Should include document data
        self.assertIn('document', data)
        
        # Analysis should be None
        self.assertIn('analysis', data)
        self.assertIsNone(data['analysis'])


class SerializerValidationTests(TestCase):
    """Test cases for cross-serializer validation scenarios."""
    
    def test_document_serializer_field_consistency(self):
        """Test that DocumentSerializer fields are consistent with model."""
        from .models import Document
        
        # Get model fields
        model_fields = [field.name for field in Document._meta.fields]
        
        # Get serializer fields
        serializer = DocumentSerializer()
        serializer_fields = list(serializer.fields.keys())
        
        # Check that important fields are included
        important_fields = ['document_id', 'title', 'owner_uid', 'file_type', 'status']
        for field in important_fields:
            self.assertIn(field, serializer_fields, f"Field {field} missing from serializer")
    
    def test_analysis_serializer_field_consistency(self):
        """Test that AnalysisResultSerializer fields match expected structure."""
        serializer = AnalysisResultSerializer()
        serializer_fields = list(serializer.fields.keys())
        
        # Check that all required fields are present
        required_fields = [
            'document_id', 'version', 'detected_language', 'summary',
            'token_usage', 'completion_time'
        ]
        for field in required_fields:
            self.assertIn(field, serializer_fields, f"Field {field} missing from serializer")
    
    def test_upload_serializer_file_type_consistency(self):
        """Test that upload serializer supports same file types as extractor."""
        from .services.text_extractor import TextExtractor
        
        extractor = TextExtractor()
        extractor_types = set(extractor.get_supported_mime_types())
        
        serializer = DocumentUploadSerializer()
        serializer_types = set(serializer.SUPPORTED_MIME_TYPES)
        
        # Should support the same types
        self.assertEqual(extractor_types, serializer_types)


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'rest_framework',
                'apps.documents',
            ],
            SECRET_KEY='test-secret-key',
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["apps.documents.test_serializers"])