"""
Test cases for document services.

Tests the service layer including:
- FirestoreService for document operations
- GCSService for file storage
- TextExtractor for document processing
"""
import uuid
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from django.test import TestCase

from .services.firestore_service import FirestoreService, FirestoreError
from .services.gcs_service import GCSService, GCSError
from .services.text_extractor import TextExtractor, TextExtractionError, UnsupportedFileFormatError


class FirestoreServiceTests(TestCase):
    """Test cases for FirestoreService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = FirestoreService()
        self.document_id = str(uuid.uuid4())
        self.owner_uid = "test-user-123"
        
        self.document_data = {
            'document_id': self.document_id,
            'title': 'Test Document',
            'owner_uid': self.owner_uid,
            'file_type': 'application/pdf',
            'storage_path': f'documents/{self.owner_uid}/{self.document_id}/original.pdf',
            'status': 'PENDING'
        }
    
    @patch('apps.documents.services.firestore_service.firestore.Client')
    def test_create_document_success(self, mock_client):
        """Test successful document creation in Firestore."""
        mock_db = Mock()
        mock_client.return_value = mock_db
        mock_doc_ref = Mock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        service = FirestoreService()
        result = service.create_document(
            document_id=self.document_id,
            title='Test Document',
            owner_uid=self.owner_uid,
            file_type='application/pdf',
            storage_path='test/path'
        )
        
        self.assertEqual(result['document_id'], self.document_id)
        self.assertEqual(result['title'], 'Test Document')
        mock_doc_ref.set.assert_called_once()
    
    @patch('apps.documents.services.firestore_service.firestore.Client')
    def test_create_document_error(self, mock_client):
        """Test document creation with Firestore error."""
        mock_db = Mock()
        mock_client.return_value = mock_db
        mock_doc_ref = Mock()
        mock_doc_ref.set.side_effect = Exception("Firestore error")
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        service = FirestoreService()
        
        with self.assertRaises(FirestoreError):
            service.create_document(
                document_id=self.document_id,
                title='Test Document',
                owner_uid=self.owner_uid,
                file_type='application/pdf',
                storage_path='test/path'
            )
    
    @patch('apps.documents.services.firestore_service.firestore.Client')
    def test_get_document_success(self, mock_client):
        """Test successful document retrieval."""
        mock_db = Mock()
        mock_client.return_value = mock_db
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.document_data
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        service = FirestoreService()
        result = service.get_document(self.document_id, self.owner_uid)
        
        self.assertEqual(result['document_id'], self.document_id)
        self.assertEqual(result['owner_uid'], self.owner_uid)
    
    @patch('apps.documents.services.firestore_service.firestore.Client')
    def test_get_document_not_found(self, mock_client):
        """Test document retrieval when document doesn't exist."""
        mock_db = Mock()
        mock_client.return_value = mock_db
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = False
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        service = FirestoreService()
        result = service.get_document(self.document_id, self.owner_uid)
        
        self.assertIsNone(result)
    
    @patch('apps.documents.services.firestore_service.firestore.Client')
    def test_get_document_unauthorized(self, mock_client):
        """Test document retrieval with wrong owner."""
        mock_db = Mock()
        mock_client.return_value = mock_db
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.document_data
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        service = FirestoreService()
        result = service.get_document(self.document_id, "wrong-user")
        
        self.assertIsNone(result)  # Should return None for unauthorized access
    
    @patch('apps.documents.services.firestore_service.firestore.Client')
    def test_update_document_success(self, mock_client):
        """Test successful document update."""
        mock_db = Mock()
        mock_client.return_value = mock_db
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.document_data
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        service = FirestoreService()
        result = service.update_document(
            self.document_id,
            self.owner_uid,
            {'status': 'ANALYZED'}
        )
        
        self.assertTrue(result)
        mock_doc_ref.update.assert_called_once()
    
    @patch('apps.documents.services.firestore_service.firestore.Client')
    def test_delete_document_success(self, mock_client):
        """Test successful document deletion."""
        mock_db = Mock()
        mock_client.return_value = mock_db
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.document_data
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        service = FirestoreService()
        result = service.delete_document(self.document_id, self.owner_uid)
        
        self.assertTrue(result)
        mock_doc_ref.delete.assert_called_once()
    
    @patch('apps.documents.services.firestore_service.firestore.Client')
    def test_list_user_documents(self, mock_client):
        """Test listing user documents."""
        mock_db = Mock()
        mock_client.return_value = mock_db
        mock_query = Mock()
        mock_doc = Mock()
        mock_doc.to_dict.return_value = self.document_data
        mock_query.stream.return_value = [mock_doc]
        
        # Chain the query methods
        mock_db.collection.return_value.where.return_value.order_by.return_value.limit.return_value.offset.return_value = mock_query
        
        service = FirestoreService()
        result = service.list_user_documents(self.owner_uid, limit=10, offset=0)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['document_id'], self.document_id)


class GCSServiceTests(TestCase):
    """Test cases for GCSService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = GCSService()
        self.document_id = str(uuid.uuid4())
        self.owner_uid = "test-user-123"
        self.test_content = b"Test PDF content"
    
    @patch('apps.documents.services.gcs_service.storage.Client')
    @patch('apps.documents.services.gcs_service.magic')
    def test_upload_document_success(self, mock_magic, mock_client):
        """Test successful document upload to GCS."""
        # Mock magic for MIME type detection
        mock_magic.from_buffer.return_value = 'application/pdf'
        
        # Mock GCS client
        mock_storage_client = Mock()
        mock_client.return_value = mock_storage_client
        mock_bucket = Mock()
        mock_storage_client.bucket.return_value = mock_bucket
        mock_blob = Mock()
        mock_bucket.blob.return_value = mock_blob
        
        service = GCSService()
        file_obj = BytesIO(self.test_content)
        
        result = service.upload_document(
            file_obj=file_obj,
            document_id=self.document_id,
            owner_uid=self.owner_uid,
            original_filename="test.pdf"
        )
        
        self.assertIn('storage_path', result)
        self.assertIn('mime_type', result)
        self.assertIn('file_size', result)
        self.assertEqual(result['mime_type'], 'application/pdf')
        mock_blob.upload_from_file.assert_called_once()
    
    @patch('apps.documents.services.gcs_service.storage.Client')
    def test_upload_document_file_too_large(self, mock_client):
        """Test upload with file size exceeding limit."""
        service = GCSService()
        large_content = b"x" * (service.max_file_size + 1)
        file_obj = BytesIO(large_content)
        
        with self.assertRaises(GCSError) as context:
            service.upload_document(
                file_obj=file_obj,
                document_id=self.document_id,
                owner_uid=self.owner_uid,
                original_filename="large.pdf"
            )
        
        self.assertIn("exceeds maximum allowed size", str(context.exception))
    
    @patch('apps.documents.services.gcs_service.storage.Client')
    def test_upload_document_empty_file(self, mock_client):
        """Test upload with empty file."""
        service = GCSService()
        file_obj = BytesIO(b"")
        
        with self.assertRaises(GCSError) as context:
            service.upload_document(
                file_obj=file_obj,
                document_id=self.document_id,
                owner_uid=self.owner_uid,
                original_filename="empty.pdf"
            )
        
        self.assertIn("File is empty", str(context.exception))
    
    @patch('apps.documents.services.gcs_service.storage.Client')
    def test_generate_signed_url_success(self, mock_client):
        """Test successful signed URL generation."""
        mock_storage_client = Mock()
        mock_client.return_value = mock_storage_client
        mock_bucket = Mock()
        mock_storage_client.bucket.return_value = mock_bucket
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {'owner_uid': self.owner_uid}
        mock_blob.generate_signed_url.return_value = 'https://signed-url.com'
        mock_bucket.blob.return_value = mock_blob
        
        service = GCSService()
        result = service.generate_signed_url(
            document_id=self.document_id,
            owner_uid=self.owner_uid,
            expiry_hours=1
        )
        
        self.assertEqual(result, 'https://signed-url.com')
        mock_blob.generate_signed_url.assert_called_once()
    
    @patch('apps.documents.services.gcs_service.storage.Client')
    def test_generate_signed_url_file_not_found(self, mock_client):
        """Test signed URL generation when file doesn't exist."""
        mock_storage_client = Mock()
        mock_client.return_value = mock_storage_client
        mock_bucket = Mock()
        mock_storage_client.bucket.return_value = mock_bucket
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        mock_bucket.blob.return_value = mock_blob
        
        service = GCSService()
        
        with self.assertRaises(GCSError) as context:
            service.generate_signed_url(
                document_id=self.document_id,
                owner_uid=self.owner_uid
            )
        
        self.assertIn("Document file not found", str(context.exception))
    
    @patch('apps.documents.services.gcs_service.storage.Client')
    def test_delete_document_success(self, mock_client):
        """Test successful document deletion from GCS."""
        mock_storage_client = Mock()
        mock_client.return_value = mock_storage_client
        mock_bucket = Mock()
        mock_storage_client.bucket.return_value = mock_bucket
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {'owner_uid': self.owner_uid}
        mock_bucket.blob.return_value = mock_blob
        
        service = GCSService()
        result = service.delete_document(self.document_id, self.owner_uid)
        
        self.assertTrue(result)
        mock_blob.delete.assert_called()


class TextExtractorTests(TestCase):
    """Test cases for TextExtractor."""
    
    def setUp(self):
        """Set up test data."""
        self.extractor = TextExtractor()
    
    def test_extract_text_from_plain_text(self):
        """Test text extraction from plain text file."""
        text_content = "This is a test legal document with important clauses."
        file_content = text_content.encode('utf-8')
        
        result = self.extractor.extract_text(file_content, "test.txt")
        
        self.assertEqual(result['text'], text_content)
        self.assertEqual(result['file_type'], 'text/plain')
        self.assertEqual(result['encoding'], 'utf-8')
        self.assertIn('metadata', result)
    
    @patch('apps.documents.services.text_extractor.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader):
        """Test text extraction from PDF file."""
        # Mock PDF content
        mock_page = Mock()
        mock_page.extract_text.return_value = "PDF text content"
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = None
        mock_pdf_reader.return_value = mock_reader
        
        # PDF file signature
        pdf_content = b'%PDF-1.4\n%fake pdf content'
        
        result = self.extractor.extract_text(pdf_content, "test.pdf")
        
        self.assertEqual(result['text'], "PDF text content")
        self.assertEqual(result['file_type'], 'application/pdf')
        self.assertIn('metadata', result)
    
    @patch('apps.documents.services.text_extractor.DocxDocument')
    def test_extract_text_from_docx(self, mock_docx):
        """Test text extraction from DOCX file."""
        # Mock DOCX content
        mock_paragraph = Mock()
        mock_paragraph.text = "DOCX paragraph text"
        mock_doc = Mock()
        mock_doc.paragraphs = [mock_paragraph]
        mock_docx.return_value = mock_doc
        
        # DOCX file signature (ZIP)
        docx_content = b'PK\x03\x04wordprocessingml'
        
        with patch.object(self.extractor, '_get_docx_properties', return_value={}):
            result = self.extractor.extract_text(docx_content, "test.docx")
        
        self.assertEqual(result['text'], "DOCX paragraph text")
        self.assertEqual(result['file_type'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    
    def test_extract_text_unsupported_format(self):
        """Test text extraction from unsupported file format."""
        # Image file content (JPEG signature)
        image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        
        with self.assertRaises(UnsupportedFileFormatError):
            self.extractor.extract_text(image_content, "test.jpg")
    
    def test_extract_text_empty_file(self):
        """Test text extraction from empty file."""
        with self.assertRaises(TextExtractionError) as context:
            self.extractor.extract_text(b"", "empty.txt")
        
        self.assertIn("Empty file content", str(context.exception))
    
    def test_extract_text_file_too_large(self):
        """Test text extraction from file exceeding size limit."""
        large_content = b"x" * (self.extractor.MAX_FILE_SIZE + 1)
        
        with self.assertRaises(TextExtractionError) as context:
            self.extractor.extract_text(large_content, "large.txt")
        
        self.assertIn("File size exceeds", str(context.exception))
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        dirty_text = "  This   is    a\n\n\n\ntest   document  \n\n  with   extra   whitespace  "
        
        cleaned = self.extractor._clean_text(dirty_text)
        
        expected = "This is a\n\ntest document\n\nwith extra whitespace"
        self.assertEqual(cleaned, expected)
    
    def test_detect_mime_type_by_signature(self):
        """Test MIME type detection by file signature."""
        # Test PDF signature
        pdf_content = b'%PDF-1.4'
        mime_type = self.extractor._detect_by_signature(pdf_content)
        self.assertEqual(mime_type, 'application/pdf')
        
        # Test text content
        text_content = "This is plain text content".encode('utf-8')
        mime_type = self.extractor._detect_by_signature(text_content)
        self.assertEqual(mime_type, 'text/plain')
    
    def test_is_supported_file_type(self):
        """Test file type support checking."""
        # Supported types
        self.assertTrue(self.extractor.is_supported_file_type(b'%PDF-1.4', 'test.pdf'))
        self.assertTrue(self.extractor.is_supported_file_type(b'Plain text', 'test.txt'))
        
        # Unsupported types
        self.assertFalse(self.extractor.is_supported_file_type(b'\xff\xd8\xff\xe0', 'test.jpg'))
    
    def test_get_supported_mime_types(self):
        """Test getting list of supported MIME types."""
        supported_types = self.extractor.get_supported_mime_types()
        
        self.assertIn('application/pdf', supported_types)
        self.assertIn('text/plain', supported_types)
        self.assertIn('application/vnd.openxmlformats-officedocument.wordprocessingml.document', supported_types)


class ServiceIntegrationTests(TestCase):
    """Integration tests for service interactions."""
    
    def setUp(self):
        """Set up test data."""
        self.document_id = str(uuid.uuid4())
        self.owner_uid = "test-user-123"
    
    @patch('apps.documents.services.firestore_service.firestore.Client')
    @patch('apps.documents.services.gcs_service.storage.Client')
    def test_document_lifecycle_services(self, mock_gcs_client, mock_firestore_client):
        """Test complete document lifecycle using services."""
        # Mock Firestore
        mock_firestore_db = Mock()
        mock_firestore_client.return_value = mock_firestore_db
        mock_doc_ref = Mock()
        mock_firestore_db.collection.return_value.document.return_value = mock_doc_ref
        
        # Mock GCS
        mock_gcs_storage = Mock()
        mock_gcs_client.return_value = mock_gcs_storage
        mock_bucket = Mock()
        mock_gcs_storage.bucket.return_value = mock_bucket
        mock_blob = Mock()
        mock_bucket.blob.return_value = mock_blob
        
        # Initialize services
        firestore_service = FirestoreService()
        gcs_service = GCSService()
        text_extractor = TextExtractor()
        
        # 1. Create document in Firestore
        doc_data = firestore_service.create_document(
            document_id=self.document_id,
            title='Integration Test Document',
            owner_uid=self.owner_uid,
            file_type='application/pdf',
            storage_path='test/path'
        )
        
        self.assertEqual(doc_data['document_id'], self.document_id)
        mock_doc_ref.set.assert_called_once()
        
        # 2. Extract text from file content
        text_content = "This is test document content for integration testing."
        file_content = text_content.encode('utf-8')
        
        extraction_result = text_extractor.extract_text(file_content, "test.txt")
        
        self.assertEqual(extraction_result['text'], text_content)
        self.assertEqual(extraction_result['file_type'], 'text/plain')
        
        # 3. Upload file to GCS (mocked)
        with patch.object(gcs_service, '_validate_file') as mock_validate:
            mock_validate.return_value = {
                'mime_type': 'text/plain',
                'extension': '.txt',
                'file_size': len(file_content),
                'validated': True
            }
            
            file_obj = BytesIO(file_content)
            upload_result = gcs_service.upload_document(
                file_obj=file_obj,
                document_id=self.document_id,
                owner_uid=self.owner_uid,
                original_filename="test.txt"
            )
            
            self.assertIn('storage_path', upload_result)
            self.assertEqual(upload_result['mime_type'], 'text/plain')
            mock_blob.upload_from_file.assert_called_once()


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
                'apps.documents',
            ],
            SECRET_KEY='test-secret-key',
            GOOGLE_CLOUD_PROJECT='test-project',
            GCS_BUCKET_NAME='test-bucket',
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["apps.documents.test_services"])