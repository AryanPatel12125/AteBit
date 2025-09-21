"""
Comprehensive test suite for document API views.

Tests all implemented features:
- Document CRUD operations (DocumentViewSet)
- File upload and processing (DocumentUploadView)
- AI analysis (DocumentAnalyzeView)
- File download (DocumentDownloadView)
- Analysis history (DocumentAnalysisHistoryView)
"""
import json
import uuid
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Document, Analysis, History
from ..services.firestore_service import FirestoreError
from ..services.gcs_service import GCSError
from ..services.text_extractor import TextExtractionError


class BaseDocumentTestCase(APITestCase):
    """Base test case with common setup for document tests."""
    
    def setUp(self):
        """Set up test data and mocks."""
        self.client = APIClient()
        
        # Mock Firebase user
        self.user_uid = "test-user-123"
        self.document_id = str(uuid.uuid4())
        
        # Mock Firebase authentication
        self.mock_user = Mock()
        self.mock_user.uid = self.user_uid
        self.mock_user.email = "test@example.com"
        self.mock_user.is_authenticated = True
        
        # Sample document data
        self.document_data = {
            'document_id': self.document_id,
            'title': 'Test Legal Document',
            'owner_uid': self.user_uid,
            'file_type': 'application/pdf',
            'storage_path': f'documents/{self.user_uid}/{self.document_id}/original.pdf',
            'extracted_text': 'This is a test legal document with important clauses.',
            'language_code': 'en',
            'status': 'ANALYZED'
        }
        
        # Sample analysis data
        self.analysis_data = {
            'document_id': self.document_id,
            'version': 1,
            'target_language': 'es',
            'summary': {'en': 'Test summary', 'es': 'Resumen de prueba'},
            'key_points': [
                {
                    'text': 'Important clause',
                    'explanation': 'This clause is important',
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
            'token_usage': {'input_tokens': 100, 'output_tokens': 50}
        }
    
    def authenticate_user(self):
        """Mock Firebase authentication for requests."""
        with patch('apps.authz.firebase_auth.FirebaseAuthentication.authenticate') as mock_auth:
            mock_auth.return_value = (self.mock_user, None)
            # Add user_uid to request
            self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer fake-token'
            # Mock the request.user_uid attribute
            with patch.object(self.client, 'request') as mock_request:
                mock_request.user_uid = self.user_uid
                yield


class DocumentViewSetTests(BaseDocumentTestCase):
    """Test cases for DocumentViewSet CRUD operations."""
    
    @patch('apps.documents.views.firestore_service')
    def test_create_document_success(self, mock_firestore):
        """Test successful document creation."""
        # Mock Firestore response
        mock_firestore.create_document.return_value = self.document_data
        
        with self.authenticate_user():
            response = self.client.post('/api/documents/', {
                'document_id': self.document_id,
                'title': 'Test Legal Document',
                'file_type': 'application/pdf'
            })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['document_id'], self.document_id)
        self.assertEqual(response.data['title'], 'Test Legal Document')
        mock_firestore.create_document.assert_called_once()
    
    @patch('apps.documents.views.firestore_service')
    def test_create_document_firestore_error(self, mock_firestore):
        """Test document creation with Firestore error."""
        mock_firestore.create_document.side_effect = FirestoreError("Database error")
        
        with self.authenticate_user():
            response = self.client.post('/api/documents/', {
                'document_id': self.document_id,
                'title': 'Test Legal Document',
                'file_type': 'application/pdf'
            })
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('Failed to create document', response.data['error'])
    
    @patch('apps.documents.views.firestore_service')
    def test_list_documents_success(self, mock_firestore):
        """Test successful document listing."""
        mock_firestore.list_user_documents.return_value = [self.document_data]
        
        with self.authenticate_user():
            response = self.client.get('/api/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['document_id'], self.document_id)
        mock_firestore.list_user_documents.assert_called_once_with(
            owner_uid=self.user_uid, limit=20, offset=0
        )
    
    @patch('apps.documents.views.firestore_service')
    def test_retrieve_document_success(self, mock_firestore):
        """Test successful document retrieval."""
        mock_firestore.get_document.return_value = self.document_data
        
        with self.authenticate_user():
            response = self.client.get(f'/api/documents/{self.document_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['document_id'], self.document_id)
        mock_firestore.get_document.assert_called_once_with(self.document_id, self.user_uid)
    
    @patch('apps.documents.views.firestore_service')
    def test_retrieve_document_not_found(self, mock_firestore):
        """Test document retrieval when document not found."""
        mock_firestore.get_document.return_value = None
        
        with self.authenticate_user():
            response = self.client.get(f'/api/documents/{self.document_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('apps.documents.views.gcs_service')
    @patch('apps.documents.views.firestore_service')
    def test_delete_document_success(self, mock_firestore, mock_gcs):
        """Test successful document deletion."""
        mock_firestore.get_document.return_value = self.document_data
        mock_firestore.delete_document.return_value = True
        mock_gcs.delete_document.return_value = True
        
        with self.authenticate_user():
            response = self.client.delete(f'/api/documents/{self.document_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_firestore.delete_document.assert_called_once_with(self.document_id, self.user_uid)
        mock_gcs.delete_document.assert_called_once_with(self.document_id, self.user_uid)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated requests are rejected."""
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DocumentUploadViewTests(BaseDocumentTestCase):
    """Test cases for DocumentUploadView file processing."""
    
    def create_test_file(self, filename="test.pdf", content=b"PDF content"):
        """Create a test file for upload."""
        return SimpleUploadedFile(filename, content, content_type="application/pdf")
    
    @patch('apps.documents.views.vertex_client')
    @patch('apps.documents.views.gcs_service')
    @patch('apps.documents.views.firestore_service')
    def test_upload_file_success(self, mock_firestore, mock_gcs, mock_vertex):
        """Test successful file upload and processing."""
        # Mock services
        mock_firestore.get_document.return_value = self.document_data
        mock_firestore.update_document.return_value = True
        
        mock_gcs.upload_document.return_value = {
            'storage_path': 'documents/test/file.pdf',
            'mime_type': 'application/pdf',
            'file_size': 1024
        }
        mock_gcs.upload_extracted_text.return_value = 'documents/test/extracted.txt'
        
        # Mock text extraction
        with patch('apps.documents.views.TextExtractor') as mock_extractor_class:
            mock_extractor = mock_extractor_class.return_value
            mock_extractor.extract_text.return_value = {
                'text': 'Extracted text content',
                'file_type': 'application/pdf',
                'encoding': None,
                'metadata': {}
            }
            
            # Mock language detection
            mock_vertex.detect_language.return_value = 'en'
            
            test_file = self.create_test_file()
            
            with self.authenticate_user():
                response = self.client.post(
                    f'/api/documents/{self.document_id}/upload/',
                    {'file': test_file},
                    format='multipart'
                )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('File uploaded and processed successfully', response.data['message'])
        self.assertEqual(response.data['document_id'], self.document_id)
        self.assertIn('file_info', response.data)
        self.assertIn('processing_results', response.data)
    
    @patch('apps.documents.views.firestore_service')
    def test_upload_file_document_not_found(self, mock_firestore):
        """Test file upload when document doesn't exist."""
        mock_firestore.get_document.return_value = None
        
        test_file = self.create_test_file()
        
        with self.authenticate_user():
            response = self.client.post(
                f'/api/documents/{self.document_id}/upload/',
                {'file': test_file},
                format='multipart'
            )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Document not found', response.data['error'])
    
    @patch('apps.documents.views.gcs_service')
    @patch('apps.documents.views.firestore_service')
    def test_upload_file_gcs_error(self, mock_firestore, mock_gcs):
        """Test file upload with GCS error."""
        mock_firestore.get_document.return_value = self.document_data
        mock_firestore.update_document.return_value = True
        mock_gcs.upload_document.side_effect = GCSError("Storage error")
        
        test_file = self.create_test_file()
        
        with self.authenticate_user():
            response = self.client.post(
                f'/api/documents/{self.document_id}/upload/',
                {'file': test_file},
                format='multipart'
            )
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('File upload failed', response.data['error'])
    
    def test_upload_file_invalid_format(self):
        """Test file upload with invalid file format."""
        invalid_file = SimpleUploadedFile(
            "test.exe", 
            b"Invalid content", 
            content_type="application/x-executable"
        )
        
        with self.authenticate_user():
            response = self.client.post(
                f'/api/documents/{self.document_id}/upload/',
                {'file': invalid_file},
                format='multipart'
            )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_upload_file_no_file(self):
        """Test file upload without providing a file."""
        with self.authenticate_user():
            response = self.client.post(
                f'/api/documents/{self.document_id}/upload/',
                {},
                format='multipart'
            )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DocumentAnalyzeViewTests(BaseDocumentTestCase):
    """Test cases for DocumentAnalyzeView AI processing."""
    
    @patch('apps.documents.views.vertex_client')
    @patch('apps.documents.views.firestore_service')
    def test_analyze_document_summary(self, mock_firestore, mock_vertex):
        """Test document analysis for summary."""
        mock_firestore.get_document.return_value = self.document_data
        mock_firestore.store_analysis_result.return_value = True
        
        # Mock AI response
        mock_vertex.summarize_document.return_value = {
            'detected_language': 'en',
            'summary': {'en': 'Test summary'},
            'confidence': 0.95,
            'token_usage': {'input_tokens': 100, 'output_tokens': 50}
        }
        
        with self.authenticate_user():
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                {
                    'analysis_type': 'summary',
                    'target_language': 'es'
                },
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['analysis_type'], 'summary')
        self.assertEqual(response.data['document_id'], self.document_id)
        self.assertIn('token_usage', response.data)
        mock_vertex.summarize_document.assert_called_once()
    
    @patch('apps.documents.views.vertex_client')
    @patch('apps.documents.views.firestore_service')
    def test_analyze_document_key_points(self, mock_firestore, mock_vertex):
        """Test document analysis for key points."""
        mock_firestore.get_document.return_value = self.document_data
        mock_firestore.store_analysis_result.return_value = True
        
        mock_vertex.extract_key_points.return_value = {
            'detected_language': 'en',
            'key_points': [
                {
                    'text': 'Important clause',
                    'explanation': 'This is important',
                    'party_benefit': 'first_party',
                    'citation': 'chars:10-25'
                }
            ],
            'token_usage': {'input_tokens': 100, 'output_tokens': 75}
        }
        
        with self.authenticate_user():
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                {'analysis_type': 'key_points'},
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['analysis_type'], 'key_points')
        mock_vertex.extract_key_points.assert_called_once()
    
    @patch('apps.documents.views.vertex_client')
    @patch('apps.documents.views.firestore_service')
    def test_analyze_document_risks(self, mock_firestore, mock_vertex):
        """Test document analysis for risks."""
        mock_firestore.get_document.return_value = self.document_data
        mock_firestore.store_analysis_result.return_value = True
        
        mock_vertex.detect_risks.return_value = {
            'detected_language': 'en',
            'risks': [
                {
                    'severity': 'HIGH',
                    'clause': 'Risky clause',
                    'rationale': 'This could cause problems',
                    'location': 'chars:50-75'
                }
            ],
            'token_usage': {'input_tokens': 100, 'output_tokens': 60}
        }
        
        with self.authenticate_user():
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                {'analysis_type': 'risks'},
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['analysis_type'], 'risks')
        mock_vertex.detect_risks.assert_called_once()
    
    @patch('apps.documents.views.vertex_client')
    @patch('apps.documents.views.firestore_service')
    def test_analyze_document_translation(self, mock_firestore, mock_vertex):
        """Test document analysis for translation."""
        mock_firestore.get_document.return_value = self.document_data
        mock_firestore.store_analysis_result.return_value = True
        
        mock_vertex.translate_content.return_value = {
            'original_language': 'en',
            'target_language': 'es',
            'original_content': 'Original text',
            'translated_content': 'Texto traducido',
            'token_usage': {'input_tokens': 50, 'output_tokens': 55}
        }
        
        with self.authenticate_user():
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                {
                    'analysis_type': 'translation',
                    'target_language': 'es'
                },
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['analysis_type'], 'translation')
        mock_vertex.translate_content.assert_called_once()
    
    @patch('apps.documents.views.vertex_client')
    @patch('apps.documents.views.firestore_service')
    def test_analyze_document_all_types(self, mock_firestore, mock_vertex):
        """Test document analysis for all types."""
        mock_firestore.get_document.return_value = self.document_data
        mock_firestore.store_analysis_result.return_value = True
        
        # Mock all AI methods
        mock_vertex.summarize_document.return_value = {
            'detected_language': 'en',
            'summary': {'en': 'Test summary'},
            'token_usage': {'input_tokens': 100, 'output_tokens': 50}
        }
        mock_vertex.extract_key_points.return_value = {
            'key_points': [{'text': 'Key point'}],
            'token_usage': {'input_tokens': 100, 'output_tokens': 75}
        }
        mock_vertex.detect_risks.return_value = {
            'risks': [{'severity': 'HIGH', 'clause': 'Risk'}],
            'token_usage': {'input_tokens': 100, 'output_tokens': 60}
        }
        mock_vertex.translate_content.return_value = {
            'original_content': 'Original',
            'translated_content': 'Traducido',
            'token_usage': {'input_tokens': 50, 'output_tokens': 55}
        }
        
        with self.authenticate_user():
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                {
                    'analysis_type': 'all',
                    'target_language': 'es'
                },
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['analysis_type'], 'all')
        self.assertIn('results', response.data)
        # Verify all methods were called
        mock_vertex.summarize_document.assert_called_once()
        mock_vertex.extract_key_points.assert_called_once()
        mock_vertex.detect_risks.assert_called_once()
        mock_vertex.translate_content.assert_called_once()
    
    @patch('apps.documents.views.firestore_service')
    def test_analyze_document_no_text(self, mock_firestore):
        """Test analysis when document has no extracted text."""
        doc_data = self.document_data.copy()
        doc_data['extracted_text'] = None
        mock_firestore.get_document.return_value = doc_data
        
        with self.authenticate_user():
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                {'analysis_type': 'summary'},
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no extracted text', response.data['error'])
    
    def test_analyze_translation_without_target_language(self):
        """Test translation analysis without target language."""
        with self.authenticate_user():
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                {'analysis_type': 'translation'},
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DocumentDownloadViewTests(BaseDocumentTestCase):
    """Test cases for DocumentDownloadView file retrieval."""
    
    @patch('apps.documents.views.gcs_service')
    @patch('apps.documents.views.firestore_service')
    def test_download_document_success(self, mock_firestore, mock_gcs):
        """Test successful document download URL generation."""
        mock_firestore.get_document.return_value = self.document_data
        
        mock_gcs.get_document_info.return_value = {
            'storage_path': 'documents/test/file.pdf',
            'content_type': 'application/pdf',
            'size': 1024,
            'created': '2023-01-01T00:00:00Z',
            'metadata': {}
        }
        mock_gcs.generate_signed_url.return_value = 'https://storage.googleapis.com/signed-url'
        
        with self.authenticate_user():
            response = self.client.get(f'/api/documents/{self.document_id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('download_url', response.data)
        self.assertEqual(response.data['document_id'], self.document_id)
        self.assertIn('file_info', response.data)
        mock_gcs.generate_signed_url.assert_called_once()
    
    @patch('apps.documents.views.gcs_service')
    @patch('apps.documents.views.firestore_service')
    def test_download_document_custom_expiry(self, mock_firestore, mock_gcs):
        """Test document download with custom expiry time."""
        mock_firestore.get_document.return_value = self.document_data
        mock_gcs.get_document_info.return_value = {'content_type': 'application/pdf', 'size': 1024}
        mock_gcs.generate_signed_url.return_value = 'https://storage.googleapis.com/signed-url'
        
        with self.authenticate_user():
            response = self.client.get(
                f'/api/documents/{self.document_id}/download/?expiry_hours=6'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['expires_in_hours'], 6)
        mock_gcs.generate_signed_url.assert_called_with(
            document_id=self.document_id,
            owner_uid=self.user_uid,
            expiry_hours=6
        )
    
    @patch('apps.documents.views.firestore_service')
    def test_download_document_not_uploaded(self, mock_firestore):
        """Test download when document file not uploaded."""
        doc_data = self.document_data.copy()
        doc_data['storage_path'] = None
        mock_firestore.get_document.return_value = doc_data
        
        with self.authenticate_user():
            response = self.client.get(f'/api/documents/{self.document_id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not uploaded yet', response.data['error'])
    
    @patch('apps.documents.views.gcs_service')
    @patch('apps.documents.views.firestore_service')
    def test_download_document_file_not_found(self, mock_firestore, mock_gcs):
        """Test download when file not found in storage."""
        mock_firestore.get_document.return_value = self.document_data
        mock_gcs.get_document_info.return_value = None
        
        with self.authenticate_user():
            response = self.client.get(f'/api/documents/{self.document_id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('not found in storage', response.data['error'])


class DocumentAnalysisHistoryViewTests(BaseDocumentTestCase):
    """Test cases for DocumentAnalysisHistoryView."""
    
    def setUp(self):
        super().setUp()
        # Create test analysis record
        self.analysis = Analysis.objects.create(
            document_id=uuid.UUID(self.document_id),
            version=1,
            target_language='es',
            summary={'en': 'Test summary', 'es': 'Resumen de prueba'},
            key_points=[{'text': 'Key point', 'explanation': 'Explanation'}],
            risk_alerts=[{'severity': 'HIGH', 'clause': 'Risk'}],
            token_usage={'input_tokens': 100, 'output_tokens': 50}
        )
    
    @patch('apps.documents.views.firestore_service')
    def test_get_latest_analysis(self, mock_firestore):
        """Test retrieving latest analysis."""
        mock_firestore.get_document.return_value = self.document_data
        
        with self.authenticate_user():
            response = self.client.get(f'/api/documents/{self.document_id}/analysis/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['document_id'], self.document_id)
        self.assertEqual(response.data['version'], 1)
        self.assertIn('summary', response.data)
        self.assertIn('key_points', response.data)
        self.assertIn('risk_alerts', response.data)
    
    @patch('apps.documents.views.firestore_service')
    def test_get_specific_analysis_version(self, mock_firestore):
        """Test retrieving specific analysis version."""
        mock_firestore.get_document.return_value = self.document_data
        
        with self.authenticate_user():
            response = self.client.get(f'/api/documents/{self.document_id}/analysis/1/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['version'], 1)
    
    @patch('apps.documents.views.firestore_service')
    def test_get_analysis_not_found(self, mock_firestore):
        """Test retrieving non-existent analysis."""
        mock_firestore.get_document.return_value = self.document_data
        
        with self.authenticate_user():
            response = self.client.get(f'/api/documents/{self.document_id}/analysis/999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PermissionTests(BaseDocumentTestCase):
    """Test cases for permission classes."""
    
    @patch('apps.documents.views.firestore_service')
    def test_unauthorized_user_access(self, mock_firestore):
        """Test that unauthorized users cannot access documents."""
        # Don't authenticate user
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @patch('apps.documents.views.firestore_service')
    def test_wrong_owner_access(self, mock_firestore):
        """Test that users cannot access other users' documents."""
        # Mock document owned by different user
        doc_data = self.document_data.copy()
        doc_data['owner_uid'] = 'different-user-456'
        mock_firestore.get_document.return_value = None  # Firestore service handles ownership
        
        with self.authenticate_user():
            response = self.client.get(f'/api/documents/{self.document_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ErrorHandlingTests(BaseDocumentTestCase):
    """Test cases for error handling scenarios."""
    
    def test_invalid_document_id_format(self):
        """Test handling of invalid document ID format."""
        with self.authenticate_user():
            response = self.client.get('/api/documents/invalid-uuid/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('apps.documents.views.firestore_service')
    def test_firestore_service_unavailable(self, mock_firestore):
        """Test handling when Firestore service is unavailable."""
        mock_firestore.list_user_documents.side_effect = FirestoreError("Service unavailable")
        
        with self.authenticate_user():
            response = self.client.get('/api/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('Failed to retrieve documents', response.data['error'])
    
    @patch('apps.documents.views.firestore_service')
    def test_unexpected_server_error(self, mock_firestore):
        """Test handling of unexpected server errors."""
        mock_firestore.list_user_documents.side_effect = Exception("Unexpected error")
        
        with self.authenticate_user():
            response = self.client.get('/api/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('Internal server error', response.data['error'])


class IntegrationTests(BaseDocumentTestCase):
    """Integration test cases for complete workflows."""
    
    @patch('apps.documents.views.vertex_client')
    @patch('apps.documents.views.gcs_service')
    @patch('apps.documents.views.firestore_service')
    def test_complete_document_workflow(self, mock_firestore, mock_gcs, mock_vertex):
        """Test complete document workflow: create -> upload -> analyze -> download."""
        # Setup mocks
        mock_firestore.create_document.return_value = self.document_data
        mock_firestore.get_document.return_value = self.document_data
        mock_firestore.update_document.return_value = True
        mock_firestore.store_analysis_result.return_value = True
        
        mock_gcs.upload_document.return_value = {
            'storage_path': 'documents/test/file.pdf',
            'mime_type': 'application/pdf',
            'file_size': 1024
        }
        mock_gcs.get_document_info.return_value = {
            'content_type': 'application/pdf',
            'size': 1024
        }
        mock_gcs.generate_signed_url.return_value = 'https://signed-url'
        
        mock_vertex.detect_language.return_value = 'en'
        mock_vertex.summarize_document.return_value = {
            'detected_language': 'en',
            'summary': {'en': 'Summary'},
            'token_usage': {'input_tokens': 100, 'output_tokens': 50}
        }
        
        with patch('apps.documents.views.TextExtractor') as mock_extractor_class:
            mock_extractor = mock_extractor_class.return_value
            mock_extractor.extract_text.return_value = {
                'text': 'Extracted text',
                'file_type': 'application/pdf',
                'encoding': None,
                'metadata': {}
            }
            
            with self.authenticate_user():
                # 1. Create document
                create_response = self.client.post('/api/documents/', {
                    'document_id': self.document_id,
                    'title': 'Test Document',
                    'file_type': 'application/pdf'
                })
                self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
                
                # 2. Upload file
                test_file = SimpleUploadedFile("test.pdf", b"PDF content", content_type="application/pdf")
                upload_response = self.client.post(
                    f'/api/documents/{self.document_id}/upload/',
                    {'file': test_file},
                    format='multipart'
                )
                self.assertEqual(upload_response.status_code, status.HTTP_200_OK)
                
                # 3. Analyze document
                analyze_response = self.client.post(
                    f'/api/documents/{self.document_id}/analyze/',
                    {'analysis_type': 'summary'},
                    format='json'
                )
                self.assertEqual(analyze_response.status_code, status.HTTP_200_OK)
                
                # 4. Download document
                download_response = self.client.get(f'/api/documents/{self.document_id}/download/')
                self.assertEqual(download_response.status_code, status.HTTP_200_OK)
                self.assertIn('download_url', download_response.data)


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
                'apps.authz',
                'apps.ai_services',
            ],
            SECRET_KEY='test-secret-key',
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["apps.documents.test_views"])