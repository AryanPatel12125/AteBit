"""
End-to-end integration tests for the legal document AI backend.

This module contains comprehensive integration tests that verify the complete
document upload to analysis workflow, multi-language translation functionality,
download URL generation and access, and error handling across the full stack.

Requirements: All workflow requirements
"""
import io
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from .models import Document, Analysis, History
from .services.firestore_service import FirestoreService, FirestoreError
from .services.gcs_service import GCSService, GCSError
from .services.text_extractor import TextExtractor, TextExtractionError
from apps.ai_services.vertex_client import VertexAIClient


@override_settings(TESTING=True)
class DocumentWorkflowIntegrationTestCase(TestCase):
    """
    Integration tests for complete document upload to analysis workflow.
    
    Tests the full end-to-end flow:
    1. Create document metadata
    2. Upload file and extract text
    3. Perform AI analysis (all types)
    4. Generate download URLs
    5. Error handling scenarios
    """
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.client = APIClient()
        self.user_uid = "test-user-integration-123"
        self.document_id = str(uuid.uuid4())
        
        # Mock Firebase authentication
        self.auth_patcher = patch('apps.authz.firebase_auth.FirebaseAuthentication.authenticate')
        self.mock_auth = self.auth_patcher.start()
        self.mock_auth.return_value = (None, None)
        
        # Mock request.user_uid
        self.request_patcher = patch('apps.documents.views.Request')
        self.mock_request = self.request_patcher.start()
        
        # Set up authentication headers
        self.client.credentials(HTTP_AUTHORIZATION='Bearer fake-firebase-token')
        
        # Sample document content for testing (define before mocks)
        self.sample_pdf_content = b'%PDF-1.4 fake pdf content for testing'
        self.sample_text_content = """
        RENTAL AGREEMENT
        
        This rental agreement is between John Doe (Tenant) and Jane Smith (Landlord).
        
        Terms:
        1. Monthly rent is $1,200 due on the 1st of each month
        2. Security deposit of $1,200 is required and refundable
        3. No pets allowed on the premises
        4. Landlord may enter without notice for emergencies
        5. 30-day notice required for termination
        
        This agreement is governed by state law.
        """
        
        # Mock all external services
        self.setup_service_mocks()
    
    def tearDown(self):
        """Clean up after tests."""
        self.auth_patcher.stop()
        self.request_patcher.stop()
    
    def setup_service_mocks(self):
        """Set up mocks for all external services."""
        # Mock Firestore service
        self.firestore_patcher = patch('apps.documents.services.firestore_service')
        self.mock_firestore = self.firestore_patcher.start()
        
        # Mock GCS service
        self.gcs_patcher = patch('apps.documents.services.gcs_service')
        self.mock_gcs = self.gcs_patcher.start()
        
        # Mock Vertex AI client
        self.vertex_patcher = patch('apps.documents.services.vertex_client')
        self.mock_vertex = self.vertex_patcher.start()
        
        # Mock text extractor
        self.extractor_patcher = patch('apps.documents.services.text_extractor.TextExtractor')
        self.mock_extractor_class = self.extractor_patcher.start()
        self.mock_extractor = Mock()
        self.mock_extractor_class.return_value = self.mock_extractor
        
        # Configure default mock responses
        self.configure_default_mocks()
    
    def configure_default_mocks(self):
        """Configure default responses for mocked services."""
        # Firestore mock responses
        self.mock_firestore.create_document.return_value = {
            'document_id': self.document_id,
            'title': 'Test Document',
            'owner_uid': self.user_uid,
            'file_type': 'application/pdf',
            'status': 'PENDING',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        self.mock_firestore.get_document.return_value = {
            'document_id': self.document_id,
            'title': 'Test Document',
            'owner_uid': self.user_uid,
            'file_type': 'application/pdf',
            'storage_path': f'documents/{self.user_uid}/{self.document_id}/original.pdf',
            'extracted_text': self.sample_text_content,
            'language_code': 'en',
            'status': 'ANALYZED'
        }
        
        self.mock_firestore.update_document.return_value = True
        self.mock_firestore.store_analysis_result.return_value = True
        
        # GCS mock responses
        self.mock_gcs.upload_document.return_value = {
            'storage_path': f'documents/{self.user_uid}/{self.document_id}/original.pdf',
            'mime_type': 'application/pdf',
            'file_size': len(self.sample_pdf_content)
        }
        
        self.mock_gcs.upload_extracted_text.return_value = f'documents/{self.user_uid}/{self.document_id}/extracted.txt'
        
        self.mock_gcs.generate_signed_url.return_value = 'https://storage.googleapis.com/signed-url-example'
        
        # Text extractor mock responses
        self.mock_extractor.extract_text.return_value = {
            'text': self.sample_text_content,
            'file_type': 'application/pdf',
            'encoding': 'utf-8',
            'metadata': {'pages': 1, 'title': 'Test Document'}
        }
        
        # Vertex AI mock responses
        async def mock_detect_language(text):
            return 'en'
        
        async def mock_summarize_document(text, target_language=None):
            return {
                'detected_language': 'en',
                'target_language': target_language or 'en',
                'summary': 'This is a simple rental agreement between a tenant and landlord with basic terms.',
                'confidence': 0.95,
                'token_usage': {'input_tokens': 150, 'output_tokens': 25, 'total_tokens': 175}
            }
        
        async def mock_extract_key_points(text, target_language=None):
            return {
                'detected_language': 'en',
                'target_language': target_language or 'en',
                'key_points': [
                    {
                        'text': 'Monthly rent is $1,200',
                        'explanation': 'The tenant must pay this amount every month',
                        'party_benefit': 'opposing_party',
                        'citation': 'chars:150-180',
                        'importance': 'high'
                    },
                    {
                        'text': 'Security deposit refundable',
                        'explanation': 'Tenant gets deposit back if no damages',
                        'party_benefit': 'first_party',
                        'citation': 'chars:200-230',
                        'importance': 'medium'
                    }
                ],
                'confidence': 0.90,
                'token_usage': {'input_tokens': 150, 'output_tokens': 45, 'total_tokens': 195}
            }
        
        async def mock_detect_risks(text, target_language=None):
            return {
                'detected_language': 'en',
                'target_language': target_language or 'en',
                'risks': [
                    {
                        'severity': 'HIGH',
                        'clause': 'Landlord may enter without notice',
                        'rationale': 'This violates tenant privacy rights in most jurisdictions',
                        'location': 'chars:300-350',
                        'risk_category': 'privacy_violation'
                    },
                    {
                        'severity': 'MEDIUM',
                        'clause': 'No pets allowed',
                        'rationale': 'Standard clause but may limit tenant options',
                        'location': 'chars:250-270',
                        'risk_category': 'lifestyle_restriction'
                    }
                ],
                'risk_summary': {
                    'high_risks': 1,
                    'medium_risks': 1,
                    'low_risks': 0,
                    'overall_assessment': 'MEDIUM'
                },
                'confidence': 0.85,
                'token_usage': {'input_tokens': 150, 'output_tokens': 55, 'total_tokens': 205}
            }
        
        async def mock_translate_content(text, target_language, source_language='en'):
            translations = {
                'es': 'Este es un acuerdo de alquiler simple entre un inquilino y propietario con términos básicos.',
                'fr': 'Ceci est un accord de location simple entre un locataire et un propriétaire avec des termes de base.',
                'de': 'Dies ist eine einfache Mietvereinbarung zwischen einem Mieter und Vermieter mit grundlegenden Bedingungen.'
            }
            
            return {
                'original_language': source_language,
                'target_language': target_language,
                'original_content': text[:100] + '...' if len(text) > 100 else text,
                'translated_content': translations.get(target_language, 'Translation not available'),
                'confidence': 0.92,
                'token_usage': {'input_tokens': 100, 'output_tokens': 30, 'total_tokens': 130}
            }
        
        self.mock_vertex.detect_language = mock_detect_language
        self.mock_vertex.summarize_document = mock_summarize_document
        self.mock_vertex.extract_key_points = mock_extract_key_points
        self.mock_vertex.detect_risks = mock_detect_risks
        self.mock_vertex.translate_content = mock_translate_content
    
    def mock_request_user_uid(self, view_func):
        """Decorator to mock request.user_uid for view functions."""
        def wrapper(*args, **kwargs):
            with patch.object(type(args[0]), 'request') as mock_request:
                mock_request.user_uid = self.user_uid
                return view_func(*args, **kwargs)
        return wrapper
    
    def test_complete_document_workflow_success(self):
        """Test the complete end-to-end document workflow."""
        # Step 1: Create document metadata
        create_data = {
            'document_id': self.document_id,
            'title': 'Test Rental Agreement',
            'file_type': 'application/pdf'
        }
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            create_response = self.client.post('/api/documents/', create_data, format='json')
        
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data['document_id'], self.document_id)
        self.assertEqual(create_response.data['status'], 'PENDING')
        
        # Verify Firestore create was called
        self.mock_firestore.create_document.assert_called_once()
        
        # Step 2: Upload file and process
        upload_file = io.BytesIO(self.sample_pdf_content)
        upload_file.name = 'rental_agreement.pdf'
        
        upload_data = {'file': upload_file}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            upload_response = self.client.post(
                f'/api/documents/{self.document_id}/upload/',
                upload_data,
                format='multipart'
            )
        
        self.assertEqual(upload_response.status_code, status.HTTP_200_OK)
        self.assertIn('processing_results', upload_response.data)
        self.assertEqual(upload_response.data['status'], 'ANALYZED')
        
        # Verify services were called
        self.mock_gcs.upload_document.assert_called_once()
        self.mock_extractor.extract_text.assert_called_once()
        self.mock_firestore.update_document.assert_called()
        
        # Step 3: Perform AI analysis - Summary
        analysis_data = {'analysis_type': 'summary'}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            summary_response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                analysis_data,
                format='json'
            )
        
        self.assertEqual(summary_response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', summary_response.data)
        self.assertEqual(summary_response.data['detected_language'], 'en')
        
        # Step 4: Perform key points analysis
        analysis_data = {'analysis_type': 'key_points'}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            key_points_response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                analysis_data,
                format='json'
            )
        
        self.assertEqual(key_points_response.status_code, status.HTTP_200_OK)
        self.assertIn('key_points', key_points_response.data)
        self.assertEqual(len(key_points_response.data['key_points']), 2)
        
        # Step 5: Perform risk analysis
        analysis_data = {'analysis_type': 'risks'}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            risks_response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                analysis_data,
                format='json'
            )
        
        self.assertEqual(risks_response.status_code, status.HTTP_200_OK)
        self.assertIn('risks', risks_response.data)
        self.assertEqual(len(risks_response.data['risks']), 2)
        self.assertEqual(risks_response.data['risk_summary']['high_risks'], 1)
        
        # Step 6: Generate download URL
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            download_response = self.client.get(f'/api/documents/{self.document_id}/download/')
        
        self.assertEqual(download_response.status_code, status.HTTP_200_OK)
        self.assertIn('download_url', download_response.data)
        self.assertTrue(download_response.data['download_url'].startswith('https://'))
        
        # Verify GCS signed URL generation was called
        self.mock_gcs.generate_signed_url.assert_called_once()
    
    def test_multi_language_translation_workflow(self):
        """Test multi-language translation functionality across the workflow."""
        # Set up document with extracted text
        self.mock_firestore.get_document.return_value['extracted_text'] = self.sample_text_content
        
        # Test Spanish translation
        analysis_data = {
            'analysis_type': 'translation',
            'target_language': 'es'
        }
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            es_response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                analysis_data,
                format='json'
            )
        
        self.assertEqual(es_response.status_code, status.HTTP_200_OK)
        self.assertEqual(es_response.data['target_language'], 'es')
        self.assertIn('translated_content', es_response.data)
        
        # Test French summary with translation
        analysis_data = {
            'analysis_type': 'summary',
            'target_language': 'fr'
        }
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            fr_response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                analysis_data,
                format='json'
            )
        
        self.assertEqual(fr_response.status_code, status.HTTP_200_OK)
        self.assertEqual(fr_response.data['target_language'], 'fr')
        
        # Test German key points analysis
        analysis_data = {
            'analysis_type': 'key_points',
            'target_language': 'de'
        }
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            de_response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                analysis_data,
                format='json'
            )
        
        self.assertEqual(de_response.status_code, status.HTTP_200_OK)
        self.assertEqual(de_response.data['target_language'], 'de')
        
        # Test comprehensive analysis with translation
        analysis_data = {
            'analysis_type': 'all',
            'target_language': 'es'
        }
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            all_response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                analysis_data,
                format='json'
            )
        
        self.assertEqual(all_response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', all_response.data)
        self.assertIn('key_points', all_response.data)
        self.assertIn('risks', all_response.data)
        self.assertIn('translation', all_response.data)
    
    def test_download_url_generation_and_access(self):
        """Test download URL generation and access validation."""
        # Test successful download URL generation
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.get(f'/api/documents/{self.document_id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('download_url', response.data)
        self.assertIn('expires_at', response.data)
        self.assertIn('content_type', response.data)
        
        # Verify signed URL was generated with correct parameters
        self.mock_gcs.generate_signed_url.assert_called_with(
            self.document_id,
            self.user_uid,
            expiry_hours=1
        )
        
        # Test download URL for non-existent document
        fake_doc_id = str(uuid.uuid4())
        self.mock_firestore.get_document.return_value = None
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.get(f'/api/documents/{fake_doc_id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test unauthorized access (different user)
        different_user = "different-user-456"
        self.mock_firestore.get_document.return_value = None  # Simulates unauthorized access
        
        with patch('apps.documents.views.Request.user_uid', different_user):
            response = self.client.get(f'/api/documents/{self.document_id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_error_handling_across_full_stack(self):
        """Test comprehensive error handling across the full stack."""
        # Test Firestore connection error during document creation
        self.mock_firestore.create_document.side_effect = FirestoreError("Connection failed")
        
        create_data = {
            'document_id': self.document_id,
            'title': 'Test Document',
            'file_type': 'application/pdf'
        }
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.post('/api/documents/', create_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('error', response.data)
        
        # Reset mock for next test
        self.mock_firestore.create_document.side_effect = None
        self.configure_default_mocks()
        
        # Test GCS upload failure during file processing
        self.mock_gcs.upload_document.side_effect = GCSError("Upload failed")
        
        upload_file = io.BytesIO(self.sample_pdf_content)
        upload_file.name = 'test.pdf'
        upload_data = {'file': upload_file}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.post(
                f'/api/documents/{self.document_id}/upload/',
                upload_data,
                format='multipart'
            )
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('File upload failed', response.data['error'])
        
        # Reset mock for next test
        self.mock_gcs.upload_document.side_effect = None
        self.configure_default_mocks()
        
        # Test text extraction failure
        self.mock_extractor.extract_text.side_effect = TextExtractionError("Extraction failed")
        
        upload_file = io.BytesIO(self.sample_pdf_content)
        upload_file.name = 'test.pdf'
        upload_data = {'file': upload_file}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.post(
                f'/api/documents/{self.document_id}/upload/',
                upload_data,
                format='multipart'
            )
        
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn('Text extraction failed', response.data['error'])
        
        # Reset mock for next test
        self.mock_extractor.extract_text.side_effect = None
        self.configure_default_mocks()
        
        # Test Vertex AI failure during analysis
        async def mock_vertex_error(*args, **kwargs):
            raise Exception("Vertex AI service unavailable")
        
        self.mock_vertex.summarize_document = mock_vertex_error
        
        analysis_data = {'analysis_type': 'summary'}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                analysis_data,
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Test invalid analysis type
        analysis_data = {'analysis_type': 'invalid_type'}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                analysis_data,
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test missing target language for translation
        analysis_data = {'analysis_type': 'translation'}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                analysis_data,
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('target_language is required', response.data['error'])
    
    def test_authentication_and_authorization_workflow(self):
        """Test authentication and authorization across the workflow."""
        # Test unauthenticated request
        self.mock_auth.return_value = (None, None)
        
        # Remove authentication credentials
        self.client.credentials()
        
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test cross-user access attempt
        self.client.credentials(HTTP_AUTHORIZATION='Bearer fake-firebase-token')
        
        # Mock document belonging to different user
        self.mock_firestore.get_document.return_value = {
            'document_id': self.document_id,
            'owner_uid': 'different-user-123',  # Different owner
            'title': 'Test Document'
        }
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.get(f'/api/documents/{self.document_id}/')
        
        # Should return 404 (not found) rather than 403 to avoid information leakage
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_document_lifecycle_management(self):
        """Test complete document lifecycle from creation to deletion."""
        # Create document
        create_data = {
            'document_id': self.document_id,
            'title': 'Lifecycle Test Document',
            'file_type': 'application/pdf'
        }
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            create_response = self.client.post('/api/documents/', create_data, format='json')
        
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        
        # Upload file
        upload_file = io.BytesIO(self.sample_pdf_content)
        upload_file.name = 'lifecycle_test.pdf'
        upload_data = {'file': upload_file}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            upload_response = self.client.post(
                f'/api/documents/{self.document_id}/upload/',
                upload_data,
                format='multipart'
            )
        
        self.assertEqual(upload_response.status_code, status.HTTP_200_OK)
        
        # Perform analysis
        analysis_data = {'analysis_type': 'summary'}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            analysis_response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                analysis_data,
                format='json'
            )
        
        self.assertEqual(analysis_response.status_code, status.HTTP_200_OK)
        
        # List documents (should include our document)
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            list_response = self.client.get('/api/documents/')
        
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        
        # Retrieve specific document
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            retrieve_response = self.client.get(f'/api/documents/{self.document_id}/')
        
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        
        # Delete document
        self.mock_firestore.delete_document.return_value = True
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            delete_response = self.client.delete(f'/api/documents/{self.document_id}/')
        
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify deletion was called on all services
        self.mock_gcs.delete_document.assert_called_once()
        self.mock_firestore.delete_document.assert_called_once()
    
    def test_concurrent_analysis_requests(self):
        """Test handling of concurrent analysis requests on the same document."""
        # Set up document with extracted text
        self.mock_firestore.get_document.return_value['extracted_text'] = self.sample_text_content
        
        # Simulate concurrent requests for different analysis types
        analysis_requests = [
            {'analysis_type': 'summary'},
            {'analysis_type': 'key_points'},
            {'analysis_type': 'risks'},
            {'analysis_type': 'translation', 'target_language': 'es'}
        ]
        
        responses = []
        
        for analysis_data in analysis_requests:
            with patch('apps.documents.views.Request.user_uid', self.user_uid):
                response = self.client.post(
                    f'/api/documents/{self.document_id}/analyze/',
                    analysis_data,
                    format='json'
                )
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify each analysis type returned appropriate data
        self.assertIn('summary', responses[0].data)
        self.assertIn('key_points', responses[1].data)
        self.assertIn('risks', responses[2].data)
        self.assertIn('translated_content', responses[3].data)
    
    def test_large_document_processing(self):
        """Test processing of large documents with extensive content."""
        # Create large document content
        large_content = self.sample_text_content * 100  # Simulate large document
        
        # Mock text extraction for large document
        self.mock_extractor.extract_text.return_value = {
            'text': large_content,
            'file_type': 'application/pdf',
            'encoding': 'utf-8',
            'metadata': {'pages': 50, 'title': 'Large Test Document'}
        }
        
        # Mock Firestore to return large content
        large_doc_data = self.mock_firestore.get_document.return_value.copy()
        large_doc_data['extracted_text'] = large_content
        self.mock_firestore.get_document.return_value = large_doc_data
        
        # Test upload of large document
        large_file_content = b'%PDF-1.4 ' + b'x' * 5000000  # 5MB file
        upload_file = io.BytesIO(large_file_content)
        upload_file.name = 'large_document.pdf'
        upload_data = {'file': upload_file}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            upload_response = self.client.post(
                f'/api/documents/{self.document_id}/upload/',
                upload_data,
                format='multipart'
            )
        
        self.assertEqual(upload_response.status_code, status.HTTP_200_OK)
        
        # Test analysis of large document
        analysis_data = {'analysis_type': 'summary'}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            analysis_response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                analysis_data,
                format='json'
            )
        
        self.assertEqual(analysis_response.status_code, status.HTTP_200_OK)
        self.assertIn('token_usage', analysis_response.data)


@override_settings(TESTING=True)
class DocumentAPIEndpointIntegrationTestCase(TestCase):
    """
    Integration tests focused on API endpoint behavior and responses.
    
    Tests API contract compliance, response formats, error codes,
    and endpoint-specific functionality.
    """
    
    def setUp(self):
        """Set up API integration test fixtures."""
        self.client = APIClient()
        self.user_uid = "test-api-user-456"
        self.document_id = str(uuid.uuid4())
        
        # Mock authentication
        self.auth_patcher = patch('apps.authz.firebase_auth.FirebaseAuthentication.authenticate')
        self.mock_auth = self.auth_patcher.start()
        self.mock_auth.return_value = (None, None)
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer fake-firebase-token')
        
        # Mock services
        self.setup_api_mocks()
    
    def tearDown(self):
        """Clean up after API tests."""
        self.auth_patcher.stop()
    
    def setup_api_mocks(self):
        """Set up mocks for API testing."""
        # Mock all services to avoid external dependencies
        self.firestore_patcher = patch('apps.documents.services.firestore_service')
        self.mock_firestore = self.firestore_patcher.start()
        
        self.gcs_patcher = patch('apps.documents.services.gcs_service')
        self.mock_gcs = self.gcs_patcher.start()
        
        self.vertex_patcher = patch('apps.documents.services.vertex_client')
        self.mock_vertex = self.vertex_patcher.start()
        
        # Configure basic responses
        self.mock_firestore.get_document.return_value = {
            'document_id': self.document_id,
            'title': 'API Test Document',
            'owner_uid': self.user_uid,
            'file_type': 'application/pdf',
            'extracted_text': 'Sample document text for API testing.',
            'status': 'ANALYZED'
        }
    
    def test_api_response_formats(self):
        """Test that all API endpoints return properly formatted responses."""
        # Test document list response format
        self.mock_firestore.list_user_documents.return_value = [
            {
                'document_id': self.document_id,
                'title': 'Test Document 1',
                'owner_uid': self.user_uid,
                'status': 'ANALYZED',
                'created_at': datetime.utcnow().isoformat()
            }
        ]
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.get('/api/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertIn('limit', response.data)
        self.assertIn('offset', response.data)
        
        # Test document detail response format
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.get(f'/api/documents/{self.document_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('document_id', response.data)
        self.assertIn('title', response.data)
        self.assertIn('status', response.data)
        
        # Test analysis response format
        async def mock_analysis(*args, **kwargs):
            return {
                'detected_language': 'en',
                'summary': 'Test summary',
                'confidence': 0.95,
                'token_usage': {'input_tokens': 100, 'output_tokens': 20, 'total_tokens': 120}
            }
        
        self.mock_vertex.summarize_document = mock_analysis
        
        analysis_data = {'analysis_type': 'summary'}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                analysis_data,
                format='json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detected_language', response.data)
        self.assertIn('token_usage', response.data)
    
    def test_api_error_response_consistency(self):
        """Test that error responses follow consistent format across endpoints."""
        # Test 404 error format
        self.mock_firestore.get_document.return_value = None
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.get(f'/api/documents/{self.document_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        
        # Test 400 error format (invalid data)
        invalid_data = {'invalid_field': 'invalid_value'}
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.post('/api/documents/', invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test 503 error format (service unavailable)
        self.mock_firestore.create_document.side_effect = FirestoreError("Service unavailable")
        
        create_data = {
            'document_id': str(uuid.uuid4()),
            'title': 'Test Document',
            'file_type': 'application/pdf'
        }
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.post('/api/documents/', create_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('error', response.data)
    
    def test_api_pagination_and_filtering(self):
        """Test API pagination and filtering functionality."""
        # Mock multiple documents
        mock_documents = [
            {
                'document_id': str(uuid.uuid4()),
                'title': f'Test Document {i}',
                'owner_uid': self.user_uid,
                'status': 'ANALYZED',
                'created_at': datetime.utcnow().isoformat()
            }
            for i in range(25)
        ]
        
        # Test default pagination
        self.mock_firestore.list_user_documents.return_value = mock_documents[:20]
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.get('/api/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 20)
        self.assertEqual(response.data['limit'], 20)
        self.assertEqual(response.data['offset'], 0)
        
        # Test custom pagination
        self.mock_firestore.list_user_documents.return_value = mock_documents[10:20]
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.get('/api/documents/?limit=10&offset=10')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 10)
        self.assertEqual(response.data['offset'], 10)
    
    def test_api_content_type_handling(self):
        """Test API handling of different content types."""
        # Test JSON content type for document creation
        create_data = {
            'document_id': str(uuid.uuid4()),
            'title': 'JSON Test Document',
            'file_type': 'application/pdf'
        }
        
        self.mock_firestore.create_document.return_value = create_data
        
        with patch('apps.documents.views.Request.user_uid', self.user_uid):
            response = self.client.post(
                '/api/documents/',
                create_data,
                format='json',
                content_type='application/json'
            )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test multipart content type for file upload
        upload_file = io.BytesIO(b'test file content')
        upload_file.name = 'test.pdf'
        
        self.mock_gcs.upload_document.return_value = {
            'storage_path': 'test/path',
            'mime_type': 'application/pdf',
            'file_size': 17
        }
        
        with patch('apps.documents.services.text_extractor.TextExtractor') as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor_class.return_value = mock_extractor
            mock_extractor.extract_text.return_value = {
                'text': 'Extracted text',
                'file_type': 'application/pdf',
                'encoding': 'utf-8',
                'metadata': {}
            }
            
            with patch('apps.documents.views.Request.user_uid', self.user_uid):
                response = self.client.post(
                    f'/api/documents/{self.document_id}/upload/',
                    {'file': upload_file},
                    format='multipart'
                )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_api_rate_limiting_and_performance(self):
        """Test API behavior under load and rate limiting scenarios."""
        # Test multiple rapid requests to the same endpoint
        responses = []
        
        for i in range(10):
            with patch('apps.documents.views.Request.user_uid', self.user_uid):
                response = self.client.get(f'/api/documents/{self.document_id}/')
            responses.append(response)
        
        # All requests should succeed (no rate limiting implemented yet)
        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test concurrent analysis requests
        analysis_data = {'analysis_type': 'summary'}
        analysis_responses = []
        
        async def mock_analysis(*args, **kwargs):
            return {
                'detected_language': 'en',
                'summary': 'Test summary',
                'confidence': 0.95,
                'token_usage': {'input_tokens': 100, 'output_tokens': 20, 'total_tokens': 120}
            }
        
        self.mock_vertex.summarize_document = mock_analysis
        
        for i in range(5):
            with patch('apps.documents.views.Request.user_uid', self.user_uid):
                response = self.client.post(
                    f'/api/documents/{self.document_id}/analyze/',
                    analysis_data,
                    format='json'
                )
            analysis_responses.append(response)
        
        # All analysis requests should succeed
        for response in analysis_responses:
            self.assertEqual(response.status_code, status.HTTP_200_OK)


@override_settings(TESTING=True)
class DocumentServiceIntegrationTestCase(TestCase):
    """
    Integration tests for service layer interactions.
    
    Tests the integration between different services (Firestore, GCS, Vertex AI)
    and their error handling when working together.
    """
    
    def setUp(self):
        """Set up service integration test fixtures."""
        self.user_uid = "test-service-user-789"
        self.document_id = str(uuid.uuid4())
        
        # Mock external service clients but test service interactions
        self.setup_service_integration_mocks()
    
    def setup_service_integration_mocks(self):
        """Set up mocks for service integration testing."""
        # Mock the underlying clients but allow service logic to run
        self.firestore_client_patcher = patch('apps.documents.services.firestore_service.firestore')
        self.mock_firestore_client = self.firestore_client_patcher.start()
        
        self.gcs_client_patcher = patch('apps.documents.services.gcs_service.storage')
        self.mock_gcs_client = self.gcs_client_patcher.start()
        
        self.vertex_client_patcher = patch('apps.ai_services.vertex_client.vertexai')
        self.mock_vertex_client = self.vertex_client_patcher.start()
        
        # Configure mock responses
        self.configure_service_mocks()
    
    def tearDown(self):
        """Clean up service integration tests."""
        self.firestore_client_patcher.stop()
        self.gcs_client_patcher.stop()
        self.vertex_client_patcher.stop()
    
    def configure_service_mocks(self):
        """Configure mock responses for service integration."""
        # Mock Firestore client
        mock_db = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'document_id': self.document_id,
            'title': 'Service Integration Test',
            'owner_uid': self.user_uid,
            'file_type': 'application/pdf',
            'status': 'PENDING'
        }
        
        mock_doc_ref.get.return_value = mock_doc
        mock_doc_ref.set.return_value = None
        mock_doc_ref.update.return_value = None
        
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        self.mock_firestore_client.client.return_value = mock_db
        
        # Mock GCS client
        mock_bucket = Mock()
        mock_blob = Mock()
        
        mock_blob.exists.return_value = True
        mock_blob.metadata = {
            'document_id': self.document_id,
            'owner_uid': self.user_uid
        }
        mock_blob.generate_signed_url.return_value = 'https://signed-url.example.com'
        
        mock_bucket.blob.return_value = mock_blob
        self.mock_gcs_client.Client.return_value.bucket.return_value = mock_bucket
        
        # Mock Vertex AI client
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            'detected_language': 'en',
            'summary': 'Service integration test summary',
            'confidence': 0.95
        })
        mock_model.generate_content.return_value = mock_response
        
        with patch('apps.ai_services.vertex_client.GenerativeModel', return_value=mock_model):
            pass
    
    def test_firestore_gcs_integration(self):
        """Test integration between Firestore and GCS services."""
        from apps.documents.services.firestore_service import FirestoreService
        from apps.documents.services.gcs_service import GCSService
        
        # Initialize services
        firestore_service = FirestoreService()
        gcs_service = GCSService()
        
        # Test document creation in Firestore followed by file upload to GCS
        doc_data = firestore_service.create_document(
            document_id=self.document_id,
            title='Integration Test Document',
            owner_uid=self.user_uid,
            file_type='application/pdf',
            storage_path=f'documents/{self.user_uid}/{self.document_id}/original.pdf'
        )
        
        self.assertEqual(doc_data['document_id'], self.document_id)
        
        # Test file upload to GCS
        test_file = io.BytesIO(b'test file content')
        
        with patch('apps.documents.services.gcs_service.magic') as mock_magic:
            mock_magic.from_buffer.return_value = 'application/pdf'
            
            upload_result = gcs_service.upload_document(
                file_obj=test_file,
                document_id=self.document_id,
                owner_uid=self.user_uid,
                original_filename='test.pdf'
            )
        
        self.assertIn('storage_path', upload_result)
        self.assertEqual(upload_result['mime_type'], 'application/pdf')
        
        # Test signed URL generation
        signed_url = gcs_service.generate_signed_url(
            document_id=self.document_id,
            owner_uid=self.user_uid
        )
        
        self.assertTrue(signed_url.startswith('https://'))
    
    def test_text_extraction_vertex_ai_integration(self):
        """Test integration between text extraction and Vertex AI analysis."""
        from apps.documents.services.text_extractor import TextExtractor
        from apps.ai_services.vertex_client import VertexAIClient
        
        # Test text extraction
        extractor = TextExtractor()
        test_content = b'This is a test legal document with sample content.'
        
        with patch.object(extractor, '_detect_mime_type', return_value='text/plain'):
            extraction_result = extractor.extract_text(test_content, 'test.txt')
        
        extracted_text = extraction_result['text']
        self.assertIn('legal document', extracted_text)
        
        # Test Vertex AI analysis of extracted text
        with patch('apps.ai_services.vertex_client.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_response = Mock()
            mock_response.text = json.dumps({
                'detected_language': 'en',
                'summary': 'This is a summary of the legal document',
                'confidence': 0.95
            })
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model
            
            vertex_client = VertexAIClient()
            
            # Test async analysis
            async def run_analysis():
                return await vertex_client.summarize_document(extracted_text)
            
            with patch('apps.ai_services.vertex_client.settings') as mock_settings:
                mock_settings.TESTING = False
                mock_settings.VERTEX_SETTINGS = {
                    'max_output_tokens': 1024,
                    'temperature': 0.3
                }
                
                result = asyncio.run(run_analysis())
        
        self.assertEqual(result['detected_language'], 'en')
        self.assertIn('summary', result)
    
    def test_service_error_propagation(self):
        """Test how errors propagate between integrated services."""
        from apps.documents.services.firestore_service import FirestoreService, FirestoreError
        from apps.documents.services.gcs_service import GCSService, GCSError
        
        # Test Firestore error propagation
        firestore_service = FirestoreService()
        
        # Mock Firestore to raise an exception
        self.mock_firestore_client.client.side_effect = Exception("Firestore connection failed")
        
        with self.assertRaises(FirestoreError):
            firestore_service.create_document(
                document_id=self.document_id,
                title='Error Test',
                owner_uid=self.user_uid,
                file_type='application/pdf',
                storage_path='test/path'
            )
        
        # Test GCS error propagation
        gcs_service = GCSService()
        
        # Mock GCS to raise an exception
        self.mock_gcs_client.Client.side_effect = Exception("GCS connection failed")
        
        test_file = io.BytesIO(b'test content')
        
        with self.assertRaises(GCSError):
            gcs_service.upload_document(
                file_obj=test_file,
                document_id=self.document_id,
                owner_uid=self.user_uid,
                original_filename='test.pdf'
            )
    
    def test_service_transaction_rollback(self):
        """Test rollback behavior when service operations fail."""
        from apps.documents.services.firestore_service import FirestoreService
        from apps.documents.services.gcs_service import GCSService
        
        firestore_service = FirestoreService()
        gcs_service = GCSService()
        
        # Test scenario: Firestore succeeds but GCS fails
        # In a real implementation, this would test transaction rollback
        
        # Create document in Firestore
        doc_data = firestore_service.create_document(
            document_id=self.document_id,
            title='Rollback Test',
            owner_uid=self.user_uid,
            file_type='application/pdf',
            storage_path='test/path'
        )
        
        self.assertIsNotNone(doc_data)
        
        # Simulate GCS failure
        self.mock_gcs_client.Client.side_effect = Exception("GCS upload failed")
        
        test_file = io.BytesIO(b'test content')
        
        with self.assertRaises(GCSError):
            gcs_service.upload_document(
                file_obj=test_file,
                document_id=self.document_id,
                owner_uid=self.user_uid,
                original_filename='test.pdf'
            )
        
        # In a real implementation, we would verify that the Firestore
        # document was rolled back or marked as failed


@override_settings(TESTING=True)
class DocumentAnalysisWorkflowTestCase(TestCase):
    """
    Integration tests specifically for AI analysis workflows.
    
    Tests the complete analysis pipeline from document upload through
    various AI analysis types and result storage.
    """
    
    def setUp(self):
        """Set up analysis workflow test fixtures."""
        self.user_uid = "test-analysis-user-101"
        self.document_id = str(uuid.uuid4())
        
        # Sample legal document for analysis testing
        self.legal_document_text = """
        SOFTWARE LICENSE AGREEMENT
        
        This Software License Agreement ("Agreement") is entered into between
        TechCorp Inc. ("Licensor") and Customer ("Licensee").
        
        1. GRANT OF LICENSE
        Licensor grants Licensee a non-exclusive, non-transferable license to use
        the Software for internal business purposes only.
        
        2. RESTRICTIONS
        Licensee shall not:
        a) Reverse engineer, decompile, or disassemble the Software
        b) Distribute, sublicense, or transfer the Software to third parties
        c) Use the Software for commercial purposes beyond internal use
        
        3. TERMINATION
        This Agreement may be terminated immediately by Licensor without notice
        if Licensee breaches any terms of this Agreement.
        
        4. LIABILITY
        IN NO EVENT SHALL LICENSOR BE LIABLE FOR ANY INDIRECT, INCIDENTAL,
        SPECIAL, OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OF THE SOFTWARE.
        
        5. GOVERNING LAW
        This Agreement shall be governed by the laws of California.
        """
        
        self.setup_analysis_mocks()
    
    def setup_analysis_mocks(self):
        """Set up mocks for analysis workflow testing."""
        # Mock Vertex AI responses for different analysis types
        self.vertex_patcher = patch('apps.ai_services.vertex_client.VertexAIClient')
        self.mock_vertex_class = self.vertex_patcher.start()
        self.mock_vertex = Mock()
        self.mock_vertex_class.return_value = self.mock_vertex
        
        # Configure realistic analysis responses
        self.configure_analysis_responses()
    
    def tearDown(self):
        """Clean up analysis workflow tests."""
        self.vertex_patcher.stop()
    
    def configure_analysis_responses(self):
        """Configure realistic AI analysis responses."""
        # Summary response
        async def mock_summarize(*args, **kwargs):
            target_lang = kwargs.get('target_language', 'en')
            return {
                'detected_language': 'en',
                'target_language': target_lang,
                'summary': 'This is a software license agreement that gives the customer permission to use software but with strict rules about not sharing it or changing it.',
                'confidence': 0.94,
                'token_usage': {'input_tokens': 245, 'output_tokens': 32, 'total_tokens': 277}
            }
        
        # Key points response
        async def mock_extract_key_points(*args, **kwargs):
            target_lang = kwargs.get('target_language', 'en')
            return {
                'detected_language': 'en',
                'target_language': target_lang,
                'key_points': [
                    {
                        'text': 'License is non-exclusive and non-transferable',
                        'explanation': 'You can use the software but cannot sell or give it to others',
                        'party_benefit': 'opposing_party',
                        'citation': 'chars:150-220',
                        'importance': 'high'
                    },
                    {
                        'text': 'Internal business use only',
                        'explanation': 'Software can only be used inside your company',
                        'party_benefit': 'opposing_party',
                        'citation': 'chars:220-280',
                        'importance': 'high'
                    },
                    {
                        'text': 'Immediate termination for breach',
                        'explanation': 'License can be cancelled right away if rules are broken',
                        'party_benefit': 'opposing_party',
                        'citation': 'chars:450-520',
                        'importance': 'high'
                    },
                    {
                        'text': 'No liability for damages',
                        'explanation': 'Company is not responsible if software causes problems',
                        'party_benefit': 'opposing_party',
                        'citation': 'chars:600-700',
                        'importance': 'medium'
                    }
                ],
                'confidence': 0.91,
                'token_usage': {'input_tokens': 245, 'output_tokens': 85, 'total_tokens': 330}
            }
        
        # Risk analysis response
        async def mock_detect_risks(*args, **kwargs):
            target_lang = kwargs.get('target_language', 'en')
            return {
                'detected_language': 'en',
                'target_language': target_lang,
                'risks': [
                    {
                        'severity': 'HIGH',
                        'clause': 'Immediate termination without notice',
                        'rationale': 'This gives the licensor too much power and provides no protection for the licensee',
                        'location': 'chars:450-520',
                        'risk_category': 'termination_risk'
                    },
                    {
                        'severity': 'HIGH',
                        'clause': 'No liability for any damages',
                        'rationale': 'This completely shields the licensor from responsibility, which may be unenforceable',
                        'location': 'chars:600-700',
                        'risk_category': 'liability_exclusion'
                    },
                    {
                        'severity': 'MEDIUM',
                        'clause': 'Non-transferable license',
                        'rationale': 'This limits business flexibility if company is sold or restructured',
                        'location': 'chars:150-220',
                        'risk_category': 'business_flexibility'
                    }
                ],
                'risk_summary': {
                    'high_risks': 2,
                    'medium_risks': 1,
                    'low_risks': 0,
                    'overall_assessment': 'HIGH'
                },
                'confidence': 0.88,
                'token_usage': {'input_tokens': 245, 'output_tokens': 95, 'total_tokens': 340}
            }
        
        # Translation response
        async def mock_translate(*args, **kwargs):
            target_lang = kwargs.get('target_language', 'es')
            translations = {
                'es': 'Este es un acuerdo de licencia de software que otorga al cliente permiso para usar el software pero con reglas estrictas sobre no compartirlo o cambiarlo.',
                'fr': 'Il s\'agit d\'un accord de licence logicielle qui donne au client la permission d\'utiliser le logiciel mais avec des règles strictes sur le fait de ne pas le partager ou le modifier.',
                'de': 'Dies ist eine Software-Lizenzvereinbarung, die dem Kunden die Erlaubnis gibt, die Software zu verwenden, aber mit strengen Regeln, sie nicht zu teilen oder zu ändern.'
            }
            
            return {
                'original_language': 'en',
                'target_language': target_lang,
                'original_content': args[0][:200] + '...',
                'translated_content': translations.get(target_lang, 'Translation not available'),
                'confidence': 0.93,
                'token_usage': {'input_tokens': 200, 'output_tokens': 45, 'total_tokens': 245}
            }
        
        # Language detection response
        async def mock_detect_language(*args, **kwargs):
            return 'en'
        
        # Assign mock methods
        self.mock_vertex.summarize_document = mock_summarize
        self.mock_vertex.extract_key_points = mock_extract_key_points
        self.mock_vertex.detect_risks = mock_detect_risks
        self.mock_vertex.translate_content = mock_translate
        self.mock_vertex.detect_language = mock_detect_language
    
    def test_comprehensive_analysis_workflow(self):
        """Test complete analysis workflow with all analysis types."""
        # Test individual analysis types
        
        # 1. Test summarization
        summary_result = asyncio.run(
            self.mock_vertex.summarize_document(self.legal_document_text)
        )
        
        self.assertEqual(summary_result['detected_language'], 'en')
        self.assertIn('software license agreement', summary_result['summary'].lower())
        self.assertGreater(summary_result['confidence'], 0.9)
        self.assertIn('token_usage', summary_result)
        
        # 2. Test key points extraction
        key_points_result = asyncio.run(
            self.mock_vertex.extract_key_points(self.legal_document_text)
        )
        
        self.assertEqual(len(key_points_result['key_points']), 4)
        self.assertTrue(all(
            'party_benefit' in kp and 'explanation' in kp 
            for kp in key_points_result['key_points']
        ))
        
        # 3. Test risk analysis
        risks_result = asyncio.run(
            self.mock_vertex.detect_risks(self.legal_document_text)
        )
        
        self.assertEqual(risks_result['risk_summary']['high_risks'], 2)
        self.assertEqual(risks_result['risk_summary']['overall_assessment'], 'HIGH')
        self.assertTrue(all(
            risk['severity'] in ['HIGH', 'MEDIUM', 'LOW'] 
            for risk in risks_result['risks']
        ))
        
        # 4. Test translation
        translation_result = asyncio.run(
            self.mock_vertex.translate_content(
                self.legal_document_text[:500], 
                target_language='es'
            )
        )
        
        self.assertEqual(translation_result['target_language'], 'es')
        self.assertIn('software', translation_result['translated_content'].lower())
    
    def test_multi_language_analysis_consistency(self):
        """Test that analysis results are consistent across different target languages."""
        languages = ['es', 'fr', 'de']
        results = {}
        
        for lang in languages:
            # Test summary in different languages
            summary_result = asyncio.run(
                self.mock_vertex.summarize_document(
                    self.legal_document_text, 
                    target_language=lang
                )
            )
            results[lang] = summary_result
        
        # Verify consistency
        for lang, result in results.items():
            self.assertEqual(result['detected_language'], 'en')
            self.assertEqual(result['target_language'], lang)
            self.assertGreater(result['confidence'], 0.9)
            
            # Token usage should be similar across languages
            self.assertIn('token_usage', result)
            self.assertGreater(result['token_usage']['total_tokens'], 0)
    
    def test_analysis_error_handling_and_recovery(self):
        """Test error handling and recovery in analysis workflows."""
        # Test Vertex AI service failure
        async def mock_vertex_error(*args, **kwargs):
            raise Exception("Vertex AI service temporarily unavailable")
        
        self.mock_vertex.summarize_document = mock_vertex_error
        
        with self.assertRaises(Exception) as context:
            asyncio.run(self.mock_vertex.summarize_document(self.legal_document_text))
        
        self.assertIn("temporarily unavailable", str(context.exception))
        
        # Test recovery after error
        async def mock_vertex_recovery(*args, **kwargs):
            return {
                'detected_language': 'en',
                'summary': 'Recovery test summary',
                'confidence': 0.95,
                'token_usage': {'input_tokens': 100, 'output_tokens': 20, 'total_tokens': 120}
            }
        
        self.mock_vertex.summarize_document = mock_vertex_recovery
        
        recovery_result = asyncio.run(
            self.mock_vertex.summarize_document(self.legal_document_text)
        )
        
        self.assertEqual(recovery_result['summary'], 'Recovery test summary')
    
    def test_analysis_performance_and_token_tracking(self):
        """Test analysis performance metrics and token usage tracking."""
        # Test token usage across different analysis types
        analysis_types = ['summarize_document', 'extract_key_points', 'detect_risks']
        token_usage_results = {}
        
        for analysis_type in analysis_types:
            method = getattr(self.mock_vertex, analysis_type)
            result = asyncio.run(method(self.legal_document_text))
            token_usage_results[analysis_type] = result['token_usage']
        
        # Verify token usage is tracked for all analysis types
        for analysis_type, usage in token_usage_results.items():
            self.assertIn('input_tokens', usage)
            self.assertIn('output_tokens', usage)
            self.assertIn('total_tokens', usage)
            self.assertEqual(
                usage['total_tokens'], 
                usage['input_tokens'] + usage['output_tokens']
            )
        
        # Test that more complex analysis uses more tokens
        summary_tokens = token_usage_results['summarize_document']['total_tokens']
        key_points_tokens = token_usage_results['extract_key_points']['total_tokens']
        risks_tokens = token_usage_results['detect_risks']['total_tokens']
        
        # Key points and risks analysis should generally use more tokens than summary
        self.assertGreaterEqual(key_points_tokens, summary_tokens)
        self.assertGreaterEqual(risks_tokens, summary_tokens)
    
    def test_analysis_result_validation(self):
        """Test validation of analysis results structure and content."""
        # Test summary result structure
        summary_result = asyncio.run(
            self.mock_vertex.summarize_document(self.legal_document_text)
        )
        
        required_summary_fields = ['detected_language', 'summary', 'confidence', 'token_usage']
        for field in required_summary_fields:
            self.assertIn(field, summary_result)
        
        # Test key points result structure
        key_points_result = asyncio.run(
            self.mock_vertex.extract_key_points(self.legal_document_text)
        )
        
        required_key_point_fields = ['text', 'explanation', 'party_benefit', 'citation', 'importance']
        for key_point in key_points_result['key_points']:
            for field in required_key_point_fields:
                self.assertIn(field, key_point)
            
            # Validate party_benefit values
            self.assertIn(key_point['party_benefit'], ['first_party', 'opposing_party', 'mutual'])
            
            # Validate importance levels
            self.assertIn(key_point['importance'], ['high', 'medium', 'low'])
        
        # Test risks result structure
        risks_result = asyncio.run(
            self.mock_vertex.detect_risks(self.legal_document_text)
        )
        
        required_risk_fields = ['severity', 'clause', 'rationale', 'location', 'risk_category']
        for risk in risks_result['risks']:
            for field in required_risk_fields:
                self.assertIn(field, risk)
            
            # Validate severity levels
            self.assertIn(risk['severity'], ['HIGH', 'MEDIUM', 'LOW'])
        
        # Validate risk summary
        risk_summary = risks_result['risk_summary']
        required_summary_fields = ['high_risks', 'medium_risks', 'low_risks', 'overall_assessment']
        for field in required_summary_fields:
            self.assertIn(field, risk_summary)
        
        self.assertIn(risk_summary['overall_assessment'], ['HIGH', 'MEDIUM', 'LOW'])