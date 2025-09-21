import io
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock, call

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from .services.text_extractor import TextExtractor, TextExtractionError, UnsupportedFileFormatError
from .services.firestore_service import FirestoreService, FirestoreError
from .services.gcs_service import GCSService, GCSError


class TextExtractorTestCase(TestCase):
    """Test cases for TextExtractor service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = TextExtractor()
    
    def test_extract_text_from_plain_text(self):
        """Test text extraction from plain text file."""
        test_content = "This is a test document.\nWith multiple lines.\n\nAnd paragraphs."
        file_content = test_content.encode('utf-8')
        
        with patch.object(self.extractor, '_detect_mime_type', return_value='text/plain'):
            result = self.extractor.extract_text(file_content, 'test.txt')
        
        self.assertEqual(result['text'], test_content)
        self.assertEqual(result['file_type'], 'text/plain')
        # ASCII is a subset of UTF-8, so either is acceptable
        self.assertIn(result['encoding'], ['utf-8', 'ascii'])
        self.assertIn('metadata', result)
    
    def test_extract_text_empty_file(self):
        """Test handling of empty file."""
        with self.assertRaises(TextExtractionError):
            self.extractor.extract_text(b'', 'empty.txt')
    
    def test_extract_text_unsupported_format(self):
        """Test handling of unsupported file format."""
        file_content = b'fake image content'
        
        with patch.object(self.extractor, '_detect_mime_type', return_value='image/jpeg'):
            with self.assertRaises(UnsupportedFileFormatError):
                self.extractor.extract_text(file_content, 'image.jpg')
    
    def test_extract_text_file_too_large(self):
        """Test handling of files that exceed size limit."""
        large_content = b'x' * (TextExtractor.MAX_FILE_SIZE + 1)
        
        with self.assertRaises(TextExtractionError) as context:
            self.extractor.extract_text(large_content, 'large.txt')
        
        self.assertIn('exceeds', str(context.exception))
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        dirty_text = "  This   has    excessive   whitespace  \n\n\n\n\nAnd multiple newlines  \n  "
        cleaned = self.extractor._clean_text(dirty_text)
        
        expected = "This has excessive whitespace\n\nAnd multiple newlines"
        self.assertEqual(cleaned, expected)
    
    def test_is_supported_file_type(self):
        """Test file type support checking."""
        with patch.object(self.extractor, '_detect_mime_type', return_value='text/plain'):
            self.assertTrue(self.extractor.is_supported_file_type(b'test content'))
        
        with patch.object(self.extractor, '_detect_mime_type', return_value='image/jpeg'):
            self.assertFalse(self.extractor.is_supported_file_type(b'test content'))
    
    def test_get_supported_mime_types(self):
        """Test getting list of supported MIME types."""
        mime_types = self.extractor.get_supported_mime_types()
        
        self.assertIn('text/plain', mime_types)
        self.assertIn('application/pdf', mime_types)
        self.assertIn('application/vnd.openxmlformats-officedocument.wordprocessingml.document', mime_types)
    
    @patch('apps.documents.services.text_extractor.PdfReader')
    def test_extract_from_pdf_success(self, mock_pdf_reader):
        """Test successful PDF text extraction."""
        # Mock PDF reader
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test PDF content"
        
        mock_reader_instance = MagicMock()
        mock_reader_instance.pages = [mock_page]
        mock_reader_instance.metadata = None
        mock_pdf_reader.return_value = mock_reader_instance
        
        file_content = b'fake pdf content'
        
        with patch.object(self.extractor, '_detect_mime_type', return_value='application/pdf'):
            result = self.extractor.extract_text(file_content, 'test.pdf')
        
        self.assertEqual(result['text'], "Test PDF content")
        self.assertEqual(result['file_type'], 'application/pdf')
        self.assertIn('metadata', result)
    
    @patch('apps.documents.services.text_extractor.DocxDocument')
    def test_extract_from_docx_success(self, mock_docx_document):
        """Test successful DOCX text extraction."""
        # Mock DOCX document
        mock_paragraph = MagicMock()
        mock_paragraph.text = "Test DOCX content"
        
        mock_doc_instance = MagicMock()
        mock_doc_instance.paragraphs = [mock_paragraph]
        mock_doc_instance.core_properties = MagicMock()
        mock_doc_instance.core_properties.title = "Test Document"
        mock_doc_instance.core_properties.author = "Test Author"
        mock_doc_instance.core_properties.created = None
        mock_doc_instance.core_properties.modified = None
        mock_doc_instance.core_properties.subject = ""
        mock_doc_instance.core_properties.category = ""
        mock_doc_instance.core_properties.comments = ""
        
        mock_docx_document.return_value = mock_doc_instance
        
        file_content = b'fake docx content'
        
        with patch.object(self.extractor, '_detect_mime_type', return_value='application/vnd.openxmlformats-officedocument.wordprocessingml.document'):
            result = self.extractor.extract_text(file_content, 'test.docx')
        
        self.assertEqual(result['text'], "Test DOCX content")
        self.assertEqual(result['file_type'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        self.assertIn('metadata', result)


class FirestoreServiceTestCase(TestCase):
    """Test cases for FirestoreService."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('apps.documents.services.firestore_service.firestore'):
            self.service = FirestoreService()
            self.mock_db = Mock()
            self.service.db = self.mock_db
            
        self.document_id = str(uuid.uuid4())
        self.owner_uid = "test-user-123"
        self.test_doc_data = {
            'document_id': self.document_id,
            'title': 'Test Document',
            'owner_uid': self.owner_uid,
            'file_type': 'application/pdf',
            'storage_path': f'documents/{self.owner_uid}/{self.document_id}/original.pdf',
            'status': 'PENDING'
        }
    
    def test_create_document_success(self):
        """Test successful document creation."""
        mock_doc_ref = Mock()
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        result = self.service.create_document(
            document_id=self.document_id,
            title='Test Document',
            owner_uid=self.owner_uid,
            file_type='application/pdf',
            storage_path=f'documents/{self.owner_uid}/{self.document_id}/original.pdf'
        )
        
        # Verify collection and document calls
        self.mock_db.collection.assert_called_once_with('documents')
        self.mock_db.collection.return_value.document.assert_called_once_with(self.document_id)
        mock_doc_ref.set.assert_called_once()
        
        # Verify returned data structure
        self.assertEqual(result['document_id'], self.document_id)
        self.assertEqual(result['title'], 'Test Document')
        self.assertEqual(result['owner_uid'], self.owner_uid)
        self.assertEqual(result['status'], 'PENDING')
    
    def test_create_document_with_optional_fields(self):
        """Test document creation with optional fields."""
        mock_doc_ref = Mock()
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        result = self.service.create_document(
            document_id=self.document_id,
            title='Test Document',
            owner_uid=self.owner_uid,
            file_type='application/pdf',
            storage_path=f'documents/{self.owner_uid}/{self.document_id}/original.pdf',
            extracted_text='Sample text content',
            language_code='en',
            status='ANALYZED'
        )
        
        # Verify optional fields are included
        self.assertEqual(result['extracted_text'], 'Sample text content')
        self.assertEqual(result['language_code'], 'en')
        self.assertEqual(result['status'], 'ANALYZED')
    
    def test_create_document_firestore_error(self):
        """Test document creation with Firestore error."""
        mock_doc_ref = Mock()
        mock_doc_ref.set.side_effect = Exception("Firestore connection failed")
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        with self.assertRaises(FirestoreError) as context:
            self.service.create_document(
                document_id=self.document_id,
                title='Test Document',
                owner_uid=self.owner_uid,
                file_type='application/pdf',
                storage_path=f'documents/{self.owner_uid}/{self.document_id}/original.pdf'
            )
        
        self.assertIn("Failed to create document", str(context.exception))
    
    def test_get_document_success(self):
        """Test successful document retrieval."""
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.test_doc_data
        
        mock_doc_ref.get.return_value = mock_doc
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        result = self.service.get_document(self.document_id, self.owner_uid)
        
        # Verify calls
        self.mock_db.collection.assert_called_once_with('documents')
        self.mock_db.collection.return_value.document.assert_called_once_with(self.document_id)
        mock_doc_ref.get.assert_called_once()
        
        # Verify result
        self.assertEqual(result, self.test_doc_data)
    
    def test_get_document_not_found(self):
        """Test document retrieval when document doesn't exist."""
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_doc_ref.get.return_value = mock_doc
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        result = self.service.get_document(self.document_id, self.owner_uid)
        
        self.assertIsNone(result)
    
    def test_get_document_unauthorized_access(self):
        """Test document retrieval with wrong owner."""
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.test_doc_data
        
        mock_doc_ref.get.return_value = mock_doc
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        # Try to access with different owner
        result = self.service.get_document(self.document_id, "different-user")
        
        self.assertIsNone(result)
    
    def test_update_document_success(self):
        """Test successful document update."""
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.test_doc_data
        
        mock_doc_ref.get.return_value = mock_doc
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        updates = {'status': 'ANALYZED', 'language_code': 'en'}
        result = self.service.update_document(self.document_id, self.owner_uid, updates)
        
        # Verify update was called with timestamp
        mock_doc_ref.update.assert_called_once()
        update_args = mock_doc_ref.update.call_args[0][0]
        self.assertEqual(update_args['status'], 'ANALYZED')
        self.assertEqual(update_args['language_code'], 'en')
        self.assertIn('updated_at', update_args)
        
        self.assertTrue(result)
    
    def test_update_document_unauthorized(self):
        """Test document update with wrong owner."""
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.test_doc_data
        
        mock_doc_ref.get.return_value = mock_doc
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        updates = {'status': 'ANALYZED'}
        result = self.service.update_document(self.document_id, "different-user", updates)
        
        # Should not call update
        mock_doc_ref.update.assert_not_called()
        self.assertFalse(result)
    
    def test_delete_document_success(self):
        """Test successful document deletion."""
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.test_doc_data
        
        mock_doc_ref.get.return_value = mock_doc
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        result = self.service.delete_document(self.document_id, self.owner_uid)
        
        mock_doc_ref.delete.assert_called_once()
        self.assertTrue(result)
    
    def test_delete_document_not_found(self):
        """Test document deletion when document doesn't exist."""
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_doc_ref.get.return_value = mock_doc
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        result = self.service.delete_document(self.document_id, self.owner_uid)
        
        mock_doc_ref.delete.assert_not_called()
        self.assertFalse(result)
    
    def test_list_user_documents_success(self):
        """Test successful document listing."""
        mock_query = Mock()
        mock_docs = [Mock(), Mock()]
        mock_docs[0].to_dict.return_value = self.test_doc_data
        mock_docs[1].to_dict.return_value = {**self.test_doc_data, 'document_id': 'doc2'}
        
        # Chain the query methods
        self.mock_db.collection.return_value.where.return_value.order_by.return_value.limit.return_value.offset.return_value = mock_query
        mock_query.stream.return_value = mock_docs
        
        result = self.service.list_user_documents(self.owner_uid, limit=10, offset=0)
        
        # Verify query chain
        self.mock_db.collection.assert_called_once_with('documents')
        
        # Verify result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['document_id'], self.document_id)
        self.assertEqual(result[1]['document_id'], 'doc2')
    
    def test_store_analysis_result_success(self):
        """Test successful analysis result storage."""
        # Mock document existence check
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.test_doc_data
        
        mock_doc_ref.get.return_value = mock_doc
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        # Mock analysis storage
        mock_analysis_ref = Mock()
        mock_doc_ref.collection.return_value.document.return_value = mock_analysis_ref
        
        analysis_result = {
            'summary': 'Test summary',
            'confidence': 0.95
        }
        
        result = self.service.store_analysis_result(
            self.document_id,
            self.owner_uid,
            'summary',
            analysis_result,
            version=1
        )
        
        # Verify analysis storage
        mock_doc_ref.collection.assert_called_once_with('analyses')
        mock_doc_ref.collection.return_value.document.assert_called_once_with('summary_v1')
        mock_analysis_ref.set.assert_called_once()
        
        self.assertTrue(result)
    
    def test_store_analysis_result_unauthorized(self):
        """Test analysis storage with unauthorized access."""
        # Mock document not found (unauthorized)
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_doc_ref.get.return_value = mock_doc
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        analysis_result = {'summary': 'Test summary'}
        
        result = self.service.store_analysis_result(
            self.document_id,
            "different-user",
            'summary',
            analysis_result
        )
        
        self.assertFalse(result)
    
    def test_get_analysis_result_specific_version(self):
        """Test retrieval of specific analysis version."""
        # Mock document existence check
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.test_doc_data
        
        mock_doc_ref.get.return_value = mock_doc
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        # Mock analysis retrieval
        mock_analysis_ref = Mock()
        mock_analysis_doc = Mock()
        mock_analysis_doc.exists = True
        analysis_data = {
            'analysis_type': 'summary',
            'result': {'summary': 'Test summary'},
            'version': 1
        }
        mock_analysis_doc.to_dict.return_value = analysis_data
        
        mock_analysis_ref.get.return_value = mock_analysis_doc
        mock_doc_ref.collection.return_value.document.return_value = mock_analysis_ref
        
        result = self.service.get_analysis_result(
            self.document_id,
            self.owner_uid,
            'summary',
            version=1
        )
        
        # Verify calls
        mock_doc_ref.collection.assert_called_once_with('analyses')
        mock_doc_ref.collection.return_value.document.assert_called_once_with('summary_v1')
        
        self.assertEqual(result, analysis_data)


class GCSServiceTestCase(TestCase):
    """Test cases for GCSService."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('apps.documents.services.gcs_service.storage'):
            self.service = GCSService()
            self.mock_client = Mock()
            self.mock_bucket = Mock()
            self.service.client = self.mock_client
            self.service.bucket = self.mock_bucket
            
        self.document_id = str(uuid.uuid4())
        self.owner_uid = "test-user-123"
        self.test_file_content = b"Test PDF content"
        self.test_filename = "test_document.pdf"
    
    def test_get_storage_path(self):
        """Test storage path generation."""
        path = self.service._get_storage_path(
            self.owner_uid,
            self.document_id,
            "original.pdf"
        )
        
        expected = f"documents/{self.owner_uid}/{self.document_id}/original.pdf"
        self.assertEqual(path, expected)
    
    @patch('apps.documents.services.gcs_service.magic')
    def test_validate_file_success(self, mock_magic):
        """Test successful file validation."""
        mock_magic.from_buffer.return_value = 'application/pdf'
        
        file_obj = io.BytesIO(self.test_file_content)
        
        result = self.service._validate_file(file_obj, self.test_filename)
        
        self.assertEqual(result['mime_type'], 'application/pdf')
        self.assertEqual(result['extension'], '.pdf')
        self.assertEqual(result['file_size'], len(self.test_file_content))
        self.assertTrue(result['validated'])
    
    def test_validate_file_too_large(self):
        """Test file validation with oversized file."""
        large_content = b'x' * (self.service.max_file_size + 1)
        file_obj = io.BytesIO(large_content)
        
        with self.assertRaises(GCSError) as context:
            self.service._validate_file(file_obj, "large_file.pdf")
        
        self.assertIn("exceeds maximum allowed size", str(context.exception))
    
    def test_validate_file_empty(self):
        """Test file validation with empty file."""
        file_obj = io.BytesIO(b'')
        
        with self.assertRaises(GCSError) as context:
            self.service._validate_file(file_obj, "empty.pdf")
        
        self.assertIn("File is empty", str(context.exception))
    
    @patch('apps.documents.services.gcs_service.magic')
    def test_validate_file_unsupported_type(self, mock_magic):
        """Test file validation with unsupported file type."""
        mock_magic.from_buffer.return_value = 'image/jpeg'
        
        file_obj = io.BytesIO(b'fake image content')
        
        with self.assertRaises(GCSError) as context:
            self.service._validate_file(file_obj, "image.jpg")
        
        self.assertIn("Unsupported file type", str(context.exception))
    
    @patch('apps.documents.services.gcs_service.magic')
    @patch('apps.documents.services.gcs_service.datetime')
    def test_upload_document_success(self, mock_datetime, mock_magic):
        """Test successful document upload."""
        # Mock validation
        mock_magic.from_buffer.return_value = 'application/pdf'
        
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        # Mock blob
        mock_blob = Mock()
        self.mock_bucket.blob.return_value = mock_blob
        
        file_obj = io.BytesIO(self.test_file_content)
        
        result = self.service.upload_document(
            file_obj,
            self.document_id,
            self.owner_uid,
            self.test_filename
        )
        
        # Verify blob creation and upload
        expected_path = f"documents/{self.owner_uid}/{self.document_id}/original.pdf"
        self.mock_bucket.blob.assert_called_once_with(expected_path)
        
        # Verify metadata setting
        self.assertEqual(mock_blob.metadata['document_id'], self.document_id)
        self.assertEqual(mock_blob.metadata['owner_uid'], self.owner_uid)
        self.assertEqual(mock_blob.metadata['original_filename'], self.test_filename)
        
        # Verify content type
        self.assertEqual(mock_blob.content_type, 'application/pdf')
        
        # Verify upload call
        mock_blob.upload_from_file.assert_called_once_with(file_obj)
        
        # Verify result
        self.assertEqual(result['storage_path'], expected_path)
        self.assertEqual(result['mime_type'], 'application/pdf')
        self.assertEqual(result['file_size'], len(self.test_file_content))
    
    @patch('apps.documents.services.gcs_service.magic')
    def test_upload_document_validation_error(self, mock_magic):
        """Test document upload with validation error."""
        mock_magic.from_buffer.return_value = 'image/jpeg'
        
        file_obj = io.BytesIO(b'fake image')
        
        with self.assertRaises(GCSError) as context:
            self.service.upload_document(
                file_obj,
                self.document_id,
                self.owner_uid,
                "image.jpg"
            )
        
        self.assertIn("Unsupported file type", str(context.exception))
        
        # Verify no upload was attempted
        self.mock_bucket.blob.assert_not_called()
    
    @patch('apps.documents.services.gcs_service.datetime')
    def test_upload_extracted_text_success(self, mock_datetime):
        """Test successful extracted text upload."""
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        mock_blob = Mock()
        self.mock_bucket.blob.return_value = mock_blob
        
        text_content = "Extracted text content from document"
        
        result = self.service.upload_extracted_text(
            text_content,
            self.document_id,
            self.owner_uid
        )
        
        # Verify blob creation
        expected_path = f"documents/{self.owner_uid}/{self.document_id}/extracted.txt"
        self.mock_bucket.blob.assert_called_once_with(expected_path)
        
        # Verify metadata
        self.assertEqual(mock_blob.metadata['document_id'], self.document_id)
        self.assertEqual(mock_blob.metadata['owner_uid'], self.owner_uid)
        self.assertEqual(mock_blob.metadata['content_type'], 'extracted_text')
        
        # Verify content type
        self.assertEqual(mock_blob.content_type, 'text/plain; charset=utf-8')
        
        # Verify upload
        mock_blob.upload_from_string.assert_called_once_with(
            text_content,
            content_type='text/plain; charset=utf-8'
        )
        
        self.assertEqual(result, expected_path)
    
    @patch('apps.documents.services.gcs_service.datetime')
    @patch('apps.documents.services.gcs_service.timedelta')
    def test_generate_signed_url_success(self, mock_timedelta, mock_datetime):
        """Test successful signed URL generation."""
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_expiry = datetime(2024, 1, 1, 13, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        mock_timedelta.return_value = timedelta(hours=1)
        
        # Mock blob existence and metadata
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {
            'owner_uid': self.owner_uid,
            'document_id': self.document_id
        }
        mock_blob.generate_signed_url.return_value = "https://signed-url.example.com"
        
        self.mock_bucket.blob.return_value = mock_blob
        
        result = self.service.generate_signed_url(
            self.document_id,
            self.owner_uid,
            expiry_hours=1
        )
        
        # Verify blob existence check
        mock_blob.exists.assert_called()
        mock_blob.reload.assert_called()
        
        # Verify signed URL generation
        mock_blob.generate_signed_url.assert_called_once()
        
        self.assertEqual(result, "https://signed-url.example.com")
    
    def test_generate_signed_url_not_found(self):
        """Test signed URL generation when document not found."""
        # Mock all blobs as non-existent
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        self.mock_bucket.blob.return_value = mock_blob
        
        with self.assertRaises(GCSError) as context:
            self.service.generate_signed_url(
                self.document_id,
                self.owner_uid
            )
        
        self.assertIn("Document file not found", str(context.exception))
    
    def test_generate_signed_url_unauthorized(self):
        """Test signed URL generation with wrong owner."""
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {
            'owner_uid': 'different-user',
            'document_id': self.document_id
        }
        
        self.mock_bucket.blob.return_value = mock_blob
        
        with self.assertRaises(GCSError) as context:
            self.service.generate_signed_url(
                self.document_id,
                self.owner_uid
            )
        
        self.assertIn("Unauthorized access", str(context.exception))
    
    def test_get_document_info_success(self):
        """Test successful document info retrieval."""
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {
            'owner_uid': self.owner_uid,
            'document_id': self.document_id,
            'original_filename': self.test_filename
        }
        mock_blob.content_type = 'application/pdf'
        mock_blob.size = 1024
        mock_blob.time_created = datetime(2024, 1, 1, 10, 0, 0)
        mock_blob.updated = datetime(2024, 1, 1, 11, 0, 0)
        
        self.mock_bucket.blob.return_value = mock_blob
        
        result = self.service.get_document_info(
            self.document_id,
            self.owner_uid
        )
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result['content_type'], 'application/pdf')
        self.assertEqual(result['size'], 1024)
        self.assertIn('storage_path', result)
        self.assertIn('created', result)
        self.assertIn('updated', result)
        self.assertEqual(result['metadata'], mock_blob.metadata)
    
    def test_get_document_info_not_found(self):
        """Test document info retrieval when document not found."""
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        self.mock_bucket.blob.return_value = mock_blob
        
        result = self.service.get_document_info(
            self.document_id,
            self.owner_uid
        )
        
        self.assertIsNone(result)
    
    def test_delete_document_success(self):
        """Test successful document deletion."""
        # Mock original file blob (only PDF exists)
        mock_pdf_blob = Mock()
        mock_pdf_blob.exists.return_value = True
        mock_pdf_blob.metadata = {
            'owner_uid': self.owner_uid,
            'document_id': self.document_id
        }
        
        # Mock extracted text blob
        mock_text_blob = Mock()
        mock_text_blob.exists.return_value = True
        mock_text_blob.metadata = {
            'owner_uid': self.owner_uid,
            'document_id': self.document_id
        }
        
        # Mock non-existent blobs for other extensions
        mock_nonexistent_blob = Mock()
        mock_nonexistent_blob.exists.return_value = False
        
        # Return different blobs for different paths
        def mock_blob_side_effect(path):
            if 'extracted.txt' in path:
                return mock_text_blob
            elif 'original.pdf' in path:
                return mock_pdf_blob
            else:
                # Other extensions (.docx, .doc, .txt) don't exist
                return mock_nonexistent_blob
        
        self.mock_bucket.blob.side_effect = mock_blob_side_effect
        
        result = self.service.delete_document(
            self.document_id,
            self.owner_uid
        )
        
        # Verify deletions - only PDF and extracted text should be deleted
        mock_pdf_blob.delete.assert_called_once()
        mock_text_blob.delete.assert_called_once()
        mock_nonexistent_blob.delete.assert_not_called()
        
        self.assertTrue(result)
    
    def test_delete_document_not_found(self):
        """Test document deletion when no files exist."""
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        self.mock_bucket.blob.return_value = mock_blob
        
        result = self.service.delete_document(
            self.document_id,
            self.owner_uid
        )
        
        # No deletions should occur
        mock_blob.delete.assert_not_called()
        
        self.assertFalse(result)
    
    def test_delete_document_unauthorized(self):
        """Test document deletion with wrong owner."""
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {
            'owner_uid': 'different-user',
            'document_id': self.document_id
        }
        
        self.mock_bucket.blob.return_value = mock_blob
        
        with self.assertRaises(GCSError) as context:
            self.service.delete_document(
                self.document_id,
                self.owner_uid
            )
        
        self.assertIn("Unauthorized deletion attempt", str(context.exception))
    
    def test_list_document_files_success(self):
        """Test successful file listing."""
        mock_blob1 = Mock()
        mock_blob1.name = f"documents/{self.owner_uid}/{self.document_id}/original.pdf"
        mock_blob1.size = 1024
        mock_blob1.content_type = 'application/pdf'
        mock_blob1.time_created = datetime(2024, 1, 1, 10, 0, 0)
        mock_blob1.updated = datetime(2024, 1, 1, 11, 0, 0)
        mock_blob1.metadata = {'document_id': self.document_id}
        
        mock_blob2 = Mock()
        mock_blob2.name = f"documents/{self.owner_uid}/{self.document_id}/extracted.txt"
        mock_blob2.size = 512
        mock_blob2.content_type = 'text/plain'
        mock_blob2.time_created = datetime(2024, 1, 1, 10, 30, 0)
        mock_blob2.updated = datetime(2024, 1, 1, 11, 30, 0)
        mock_blob2.metadata = {'document_id': self.document_id}
        
        self.mock_client.list_blobs.return_value = [mock_blob1, mock_blob2]
        
        result = self.service.list_document_files(
            self.owner_uid,
            self.document_id
        )
        
        # Verify list_blobs call
        expected_prefix = f"documents/{self.owner_uid}/{self.document_id}/"
        self.mock_client.list_blobs.assert_called_once_with(
            self.service.bucket_name,
            prefix=expected_prefix
        )
        
        # Verify result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], mock_blob1.name)
        self.assertEqual(result[0]['size'], 1024)
        self.assertEqual(result[1]['name'], mock_blob2.name)
        self.assertEqual(result[1]['size'], 512)


class DocumentAPITestCase(TestCase):
    """Test cases for Document API endpoints."""
    
    def setUp(self):
        """Set up test fixtures for API tests."""
        self.document_id = str(uuid.uuid4())
        self.owner_uid = "test-user-123"
        self.other_user_uid = "other-user-456"
        
        # Mock Firebase authentication
        self.auth_headers = {
            'HTTP_AUTHORIZATION': 'Bearer fake-firebase-token'
        }
        
        # Test document data
        self.document_data = {
            'document_id': self.document_id,
            'title': 'Test Legal Document',
            'file_type': 'application/pdf',
            'storage_path': f'documents/{self.owner_uid}/{self.document_id}/original.pdf',
            'status': 'PENDING'
        }
        
        # Mock services
        self.firestore_patcher = patch('apps.documents.views.firestore_service')
        self.gcs_patcher = patch('apps.documents.views.gcs_service')
        self.vertex_patcher = patch('apps.documents.views.vertex_client')
        
        self.mock_firestore = self.firestore_patcher.start()
        self.mock_gcs = self.gcs_patcher.start()
        self.mock_vertex = self.vertex_patcher.start()
    
    def tearDown(self):
        """Clean up patches."""
        self.firestore_patcher.stop()
        self.gcs_patcher.stop()
        self.vertex_patcher.stop()
    
    def _mock_authenticated_request(self, user_uid=None):
        """Helper to mock Firebase authentication on request."""
        user_uid = user_uid or self.owner_uid
        
        def mock_auth_middleware(get_response):
            def middleware(request):
                request.user_uid = user_uid
                return get_response(request)
            return middleware
        
        return patch('apps.authz.firebase_auth.FirebaseAuthentication.authenticate', 
                    return_value=(None, user_uid))
    
    def test_create_document_success(self):
        """Test successful document creation."""
        with self._mock_authenticated_request():
            self.mock_firestore.create_document.return_value = self.document_data
            
            response = self.client.post(
                '/api/documents/',
                data=self.document_data,
                content_type='application/json',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 201)
            
            # Verify Firestore service was called
            self.mock_firestore.create_document.assert_called_once_with(
                document_id=self.document_id,
                title='Test Legal Document',
                owner_uid=self.owner_uid,
                file_type='application/pdf',
                storage_path=self.document_data['storage_path'],
                status='PENDING'
            )
            
            # Verify response data
            response_data = response.json()
            self.assertEqual(response_data['document_id'], self.document_id)
            self.assertEqual(response_data['title'], 'Test Legal Document')
            self.assertEqual(response_data['owner_uid'], self.owner_uid)
    
    def test_create_document_unauthenticated(self):
        """Test document creation without authentication."""
        response = self.client.post(
            '/api/documents/',
            data=self.document_data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_create_document_invalid_data(self):
        """Test document creation with invalid data."""
        with self._mock_authenticated_request():
            invalid_data = {
                'title': '',  # Empty title
                'file_type': 'invalid/type'  # Invalid file type
            }
            
            response = self.client.post(
                '/api/documents/',
                data=invalid_data,
                content_type='application/json',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 400)
            self.assertIn('title', response.json())
    
    def test_create_document_firestore_error(self):
        """Test document creation with Firestore error."""
        with self._mock_authenticated_request():
            from apps.documents.services.firestore_service import FirestoreError
            self.mock_firestore.create_document.side_effect = FirestoreError("Connection failed")
            
            response = self.client.post(
                '/api/documents/',
                data=self.document_data,
                content_type='application/json',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 503)
            self.assertIn('Failed to create document', response.json()['error'])
    
    def test_list_documents_success(self):
        """Test successful document listing."""
        with self._mock_authenticated_request():
            mock_docs = [
                {**self.document_data, 'document_id': self.document_id},
                {**self.document_data, 'document_id': str(uuid.uuid4()), 'title': 'Second Document'}
            ]
            self.mock_firestore.list_user_documents.return_value = mock_docs
            
            response = self.client.get(
                '/api/documents/',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Verify Firestore service was called
            self.mock_firestore.list_user_documents.assert_called_once_with(
                owner_uid=self.owner_uid,
                limit=20,
                offset=0
            )
            
            # Verify response structure
            response_data = response.json()
            self.assertIn('results', response_data)
            self.assertIn('count', response_data)
            self.assertEqual(len(response_data['results']), 2)
    
    def test_list_documents_with_pagination(self):
        """Test document listing with pagination parameters."""
        with self._mock_authenticated_request():
            self.mock_firestore.list_user_documents.return_value = []
            
            response = self.client.get(
                '/api/documents/?limit=10&offset=20',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Verify pagination parameters were passed
            self.mock_firestore.list_user_documents.assert_called_once_with(
                owner_uid=self.owner_uid,
                limit=10,
                offset=20
            )
    
    def test_retrieve_document_success(self):
        """Test successful document retrieval."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = self.document_data
            
            response = self.client.get(
                f'/api/documents/{self.document_id}/',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Verify Firestore service was called
            self.mock_firestore.get_document.assert_called_once_with(
                self.document_id,
                self.owner_uid
            )
            
            # Verify response data
            response_data = response.json()
            self.assertEqual(response_data['document_id'], self.document_id)
            self.assertEqual(response_data['title'], 'Test Legal Document')
    
    def test_retrieve_document_not_found(self):
        """Test document retrieval when document doesn't exist."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = None
            
            response = self.client.get(
                f'/api/documents/{self.document_id}/',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 404)
            self.assertIn('Document not found', response.json()['error'])
    
    def test_retrieve_document_invalid_id(self):
        """Test document retrieval with invalid document ID."""
        with self._mock_authenticated_request():
            response = self.client.get(
                '/api/documents/invalid-uuid/',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 404)
    
    def test_delete_document_success(self):
        """Test successful document deletion."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = self.document_data
            self.mock_firestore.delete_document.return_value = True
            self.mock_gcs.delete_document.return_value = True
            
            response = self.client.delete(
                f'/api/documents/{self.document_id}/',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 204)
            
            # Verify services were called
            self.mock_gcs.delete_document.assert_called_once_with(
                self.document_id,
                self.owner_uid
            )
            self.mock_firestore.delete_document.assert_called_once_with(
                self.document_id,
                self.owner_uid
            )
    
    def test_delete_document_not_found(self):
        """Test document deletion when document doesn't exist."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = None
            
            response = self.client.delete(
                f'/api/documents/{self.document_id}/',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 404)
    
    def test_delete_document_gcs_error(self):
        """Test document deletion with GCS error (should continue)."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = self.document_data
            self.mock_firestore.delete_document.return_value = True
            
            from apps.documents.services.gcs_service import GCSError
            self.mock_gcs.delete_document.side_effect = GCSError("Storage error")
            
            response = self.client.delete(
                f'/api/documents/{self.document_id}/',
                **self.auth_headers
            )
            
            # Should still succeed even with GCS error
            self.assertEqual(response.status_code, 204)
            
            # Verify Firestore deletion was still called
            self.mock_firestore.delete_document.assert_called_once()


class DocumentUploadAPITestCase(TestCase):
    """Test cases for Document Upload API endpoint."""
    
    def setUp(self):
        """Set up test fixtures for upload API tests."""
        self.document_id = str(uuid.uuid4())
        self.owner_uid = "test-user-123"
        
        self.auth_headers = {
            'HTTP_AUTHORIZATION': 'Bearer fake-firebase-token'
        }
        
        self.document_data = {
            'document_id': self.document_id,
            'title': 'Test Document',
            'owner_uid': self.owner_uid,
            'file_type': 'application/pdf',
            'status': 'PENDING'
        }
        
        # Mock services
        self.firestore_patcher = patch('apps.documents.views.firestore_service')
        self.gcs_patcher = patch('apps.documents.views.gcs_service')
        self.vertex_patcher = patch('apps.documents.views.vertex_client')
        self.extractor_patcher = patch('apps.documents.views.TextExtractor')
        
        self.mock_firestore = self.firestore_patcher.start()
        self.mock_gcs = self.gcs_patcher.start()
        self.mock_vertex = self.vertex_patcher.start()
        self.mock_extractor_class = self.extractor_patcher.start()
        
        # Mock text extractor instance
        self.mock_extractor = Mock()
        self.mock_extractor_class.return_value = self.mock_extractor
    
    def tearDown(self):
        """Clean up patches."""
        self.firestore_patcher.stop()
        self.gcs_patcher.stop()
        self.vertex_patcher.stop()
        self.extractor_patcher.stop()
    
    def _mock_authenticated_request(self, user_uid=None):
        """Helper to mock Firebase authentication on request."""
        user_uid = user_uid or self.owner_uid
        return patch('apps.authz.firebase_auth.FirebaseAuthentication.authenticate', 
                    return_value=(None, user_uid))
    
    def test_upload_document_success(self):
        """Test successful document upload and processing."""
        with self._mock_authenticated_request():
            # Mock document exists
            self.mock_firestore.get_document.return_value = self.document_data
            
            # Mock GCS upload
            self.mock_gcs.upload_document.return_value = {
                'storage_path': f'documents/{self.owner_uid}/{self.document_id}/original.pdf',
                'mime_type': 'application/pdf',
                'file_size': 1024
            }
            
            # Mock text extraction
            self.mock_extractor.extract_text.return_value = {
                'text': 'Extracted document text content',
                'encoding': 'utf-8',
                'file_type': 'application/pdf',
                'metadata': {}
            }
            
            # Mock language detection
            import asyncio
            async def mock_detect_language(text):
                return 'en'
            
            self.mock_vertex.detect_language = mock_detect_language
            
            # Mock extracted text upload
            self.mock_gcs.upload_extracted_text.return_value = 'text_storage_path'
            
            # Create test file
            test_file = SimpleUploadedFile(
                "test_document.pdf",
                b"fake pdf content",
                content_type="application/pdf"
            )
            
            response = self.client.post(
                f'/api/documents/{self.document_id}/upload/',
                data={'file': test_file},
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Verify services were called
            self.mock_firestore.get_document.assert_called_with(self.document_id, self.owner_uid)
            self.mock_gcs.upload_document.assert_called_once()
            self.mock_extractor.extract_text.assert_called_once()
            
            # Verify document status updates
            update_calls = self.mock_firestore.update_document.call_args_list
            self.assertEqual(len(update_calls), 2)  # PROCESSING and ANALYZED
            
            # Verify response structure
            response_data = response.json()
            self.assertIn('message', response_data)
            self.assertIn('file_info', response_data)
            self.assertIn('processing_results', response_data)
            self.assertEqual(response_data['status'], 'ANALYZED')
    
    def test_upload_document_not_found(self):
        """Test upload for non-existent document."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = None
            
            test_file = SimpleUploadedFile(
                "test.pdf",
                b"content",
                content_type="application/pdf"
            )
            
            response = self.client.post(
                f'/api/documents/{self.document_id}/upload/',
                data={'file': test_file},
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 404)
            self.assertIn('Document not found', response.json()['error'])
    
    def test_upload_document_invalid_id(self):
        """Test upload with invalid document ID."""
        with self._mock_authenticated_request():
            test_file = SimpleUploadedFile("test.pdf", b"content")
            
            response = self.client.post(
                '/api/documents/invalid-uuid/upload/',
                data={'file': test_file},
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 400)
            self.assertIn('Invalid document ID format', response.json()['error'])
    
    def test_upload_document_no_file(self):
        """Test upload without file."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = self.document_data
            
            response = self.client.post(
                f'/api/documents/{self.document_id}/upload/',
                data={},
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 400)
    
    def test_upload_document_gcs_error(self):
        """Test upload with GCS error."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = self.document_data
            
            from apps.documents.services.gcs_service import GCSError
            self.mock_gcs.upload_document.side_effect = GCSError("Storage failed")
            
            test_file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
            
            response = self.client.post(
                f'/api/documents/{self.document_id}/upload/',
                data={'file': test_file},
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 503)
            self.assertIn('File upload failed', response.json()['error'])
            
            # Verify status was updated to ERROR
            error_update_call = None
            for call in self.mock_firestore.update_document.call_args_list:
                if call[0][2].get('status') == 'ERROR':
                    error_update_call = call
                    break
            
            self.assertIsNotNone(error_update_call)
    
    def test_upload_document_text_extraction_error(self):
        """Test upload with text extraction error."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = self.document_data
            
            self.mock_gcs.upload_document.return_value = {
                'storage_path': 'test_path',
                'mime_type': 'application/pdf',
                'file_size': 1024
            }
            
            from apps.documents.services.text_extractor import TextExtractionError
            self.mock_extractor.extract_text.side_effect = TextExtractionError("Extraction failed")
            
            test_file = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
            
            response = self.client.post(
                f'/api/documents/{self.document_id}/upload/',
                data={'file': test_file},
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 422)
            self.assertIn('Text extraction failed', response.json()['error'])


class DocumentAnalyzeAPITestCase(TestCase):
    """Test cases for Document Analysis API endpoint."""
    
    def setUp(self):
        """Set up test fixtures for analysis API tests."""
        self.document_id = str(uuid.uuid4())
        self.owner_uid = "test-user-123"
        
        self.auth_headers = {
            'HTTP_AUTHORIZATION': 'Bearer fake-firebase-token'
        }
        
        self.document_data = {
            'document_id': self.document_id,
            'title': 'Test Document',
            'owner_uid': self.owner_uid,
            'extracted_text': 'This is a sample legal document with various clauses and terms.',
            'status': 'ANALYZED'
        }
        
        # Mock services
        self.firestore_patcher = patch('apps.documents.views.firestore_service')
        self.vertex_patcher = patch('apps.documents.views.vertex_client')
        
        self.mock_firestore = self.firestore_patcher.start()
        self.mock_vertex = self.vertex_patcher.start()
        
        # Mock analysis responses
        self.mock_summary_response = {
            'detected_language': 'en',
            'summary': 'This is a simple legal agreement',
            'confidence': 0.95,
            'token_usage': {'input_tokens': 100, 'output_tokens': 50, 'total_tokens': 150}
        }
        
        self.mock_key_points_response = {
            'detected_language': 'en',
            'key_points': [
                {
                    'text': 'Payment terms',
                    'explanation': 'How payments are made',
                    'party_benefit': 'opposing_party',
                    'importance': 'high'
                }
            ],
            'confidence': 0.90,
            'token_usage': {'input_tokens': 100, 'output_tokens': 75, 'total_tokens': 175}
        }
    
    def tearDown(self):
        """Clean up patches."""
        self.firestore_patcher.stop()
        self.vertex_patcher.stop()
    
    def _mock_authenticated_request(self, user_uid=None):
        """Helper to mock Firebase authentication on request."""
        user_uid = user_uid or self.owner_uid
        return patch('apps.authz.firebase_auth.FirebaseAuthentication.authenticate', 
                    return_value=(None, user_uid))
    
    def test_analyze_document_summary_success(self):
        """Test successful document summarization."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = self.document_data
            
            # Mock async vertex client methods
            import asyncio
            async def mock_summarize(text, target_lang=None):
                return self.mock_summary_response
            
            self.mock_vertex.summarize_document = mock_summarize
            
            analysis_request = {
                'analysis_type': 'summary',
                'target_language': 'es'
            }
            
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                data=analysis_request,
                content_type='application/json',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Verify response structure
            response_data = response.json()
            self.assertIn('analysis_results', response_data)
            self.assertIn('detected_language', response_data['analysis_results'])
            self.assertIn('summary', response_data['analysis_results'])
            self.assertIn('token_usage', response_data)
    
    def test_analyze_document_key_points_success(self):
        """Test successful key points extraction."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = self.document_data
            
            import asyncio
            async def mock_extract_key_points(text, target_lang=None):
                return self.mock_key_points_response
            
            self.mock_vertex.extract_key_points = mock_extract_key_points
            
            analysis_request = {
                'analysis_type': 'key_points'
            }
            
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                data=analysis_request,
                content_type='application/json',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 200)
            
            response_data = response.json()
            self.assertIn('key_points', response_data['analysis_results'])
            self.assertEqual(len(response_data['analysis_results']['key_points']), 1)
    
    def test_analyze_document_all_types(self):
        """Test analysis with all types."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = self.document_data
            
            # Mock all analysis methods
            import asyncio
            
            async def mock_summarize(text, target_lang=None):
                return self.mock_summary_response
            
            async def mock_extract_key_points(text, target_lang=None):
                return self.mock_key_points_response
            
            async def mock_detect_risks(text, target_lang=None):
                return {
                    'detected_language': 'en',
                    'risks': [],
                    'risk_summary': {'high_risks': 0, 'medium_risks': 0, 'low_risks': 0},
                    'token_usage': {'input_tokens': 100, 'output_tokens': 30, 'total_tokens': 130}
                }
            
            self.mock_vertex.summarize_document = mock_summarize
            self.mock_vertex.extract_key_points = mock_extract_key_points
            self.mock_vertex.detect_risks = mock_detect_risks
            
            analysis_request = {
                'analysis_type': 'all'
            }
            
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                data=analysis_request,
                content_type='application/json',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 200)
            
            response_data = response.json()
            analysis_results = response_data['analysis_results']
            
            # Verify all analysis types are present
            self.assertIn('summary', analysis_results)
            self.assertIn('key_points', analysis_results)
            self.assertIn('risks', analysis_results)
            
            # Verify combined token usage
            self.assertIn('token_usage', response_data)
            self.assertGreater(response_data['token_usage']['total_tokens'], 0)
    
    def test_analyze_document_not_found(self):
        """Test analysis for non-existent document."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = None
            
            analysis_request = {
                'analysis_type': 'summary'
            }
            
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                data=analysis_request,
                content_type='application/json',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 404)
            self.assertIn('Document not found', response.json()['error'])
    
    def test_analyze_document_no_extracted_text(self):
        """Test analysis for document without extracted text."""
        with self._mock_authenticated_request():
            doc_without_text = {**self.document_data, 'extracted_text': None}
            self.mock_firestore.get_document.return_value = doc_without_text
            
            analysis_request = {
                'analysis_type': 'summary'
            }
            
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                data=analysis_request,
                content_type='application/json',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 400)
            self.assertIn('no extracted text', response.json()['error'])
    
    def test_analyze_document_translation_missing_language(self):
        """Test translation analysis without target language."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = self.document_data
            
            analysis_request = {
                'analysis_type': 'translation'
                # Missing target_language
            }
            
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                data=analysis_request,
                content_type='application/json',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 400)
            self.assertIn('target_language is required', response.json()['error'])
    
    def test_analyze_document_unsupported_type(self):
        """Test analysis with unsupported analysis type."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = self.document_data
            
            analysis_request = {
                'analysis_type': 'unsupported_type'
            }
            
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                data=analysis_request,
                content_type='application/json',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 400)
            self.assertIn('Unsupported analysis type', response.json()['error'])
    
    def test_analyze_document_vertex_ai_error(self):
        """Test analysis with Vertex AI error."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = self.document_data
            
            import asyncio
            async def mock_summarize_error(text, target_lang=None):
                raise Exception("Vertex AI service unavailable")
            
            self.mock_vertex.summarize_document = mock_summarize_error
            
            analysis_request = {
                'analysis_type': 'summary'
            }
            
            response = self.client.post(
                f'/api/documents/{self.document_id}/analyze/',
                data=analysis_request,
                content_type='application/json',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 503)
            self.assertIn('AI analysis failed', response.json()['error'])


class DocumentDownloadAPITestCase(TestCase):
    """Test cases for Document Download API endpoint."""
    
    def setUp(self):
        """Set up test fixtures for download API tests."""
        self.document_id = str(uuid.uuid4())
        self.owner_uid = "test-user-123"
        
        self.auth_headers = {
            'HTTP_AUTHORIZATION': 'Bearer fake-firebase-token'
        }
        
        self.document_data = {
            'document_id': self.document_id,
            'title': 'Test Document',
            'owner_uid': self.owner_uid,
            'status': 'ANALYZED'
        }
        
        # Mock services
        self.firestore_patcher = patch('apps.documents.views.firestore_service')
        self.gcs_patcher = patch('apps.documents.views.gcs_service')
        
        self.mock_firestore = self.firestore_patcher.start()
        self.mock_gcs = self.gcs_patcher.start()
    
    def tearDown(self):
        """Clean up patches."""
        self.firestore_patcher.stop()
        self.gcs_patcher.stop()
    
    def _mock_authenticated_request(self, user_uid=None):
        """Helper to mock Firebase authentication on request."""
        user_uid = user_uid or self.owner_uid
        return patch('apps.authz.firebase_auth.FirebaseAuthentication.authenticate', 
                    return_value=(None, user_uid))
    
    def test_download_document_success(self):
        """Test successful document download URL generation."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = self.document_data
            self.mock_gcs.generate_signed_url.return_value = "https://signed-url.example.com"
            
            response = self.client.get(
                f'/api/documents/{self.document_id}/download/',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Verify GCS service was called
            self.mock_gcs.generate_signed_url.assert_called_once_with(
                self.document_id,
                self.owner_uid,
                expiry_hours=1
            )
            
            # Verify response structure
            response_data = response.json()
            self.assertIn('download_url', response_data)
            self.assertEqual(response_data['download_url'], "https://signed-url.example.com")
            self.assertIn('expires_in_hours', response_data)
    
    def test_download_document_not_found(self):
        """Test download for non-existent document."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = None
            
            response = self.client.get(
                f'/api/documents/{self.document_id}/download/',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 404)
            self.assertIn('Document not found', response.json()['error'])
    
    def test_download_document_gcs_error(self):
        """Test download with GCS error."""
        with self._mock_authenticated_request():
            self.mock_firestore.get_document.return_value = self.document_data
            
            from apps.documents.services.gcs_service import GCSError
            self.mock_gcs.generate_signed_url.side_effect = GCSError("File not found in storage")
            
            response = self.client.get(
                f'/api/documents/{self.document_id}/download/',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 503)
            self.assertIn('Failed to generate download URL', response.json()['error'])
    
    def test_download_document_unauthorized(self):
        """Test download with wrong user."""
        with self._mock_authenticated_request("different-user"):
            self.mock_firestore.get_document.return_value = None  # No access
            
            response = self.client.get(
                f'/api/documents/{self.document_id}/download/',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 404)


class DocumentPermissionsTestCase(TestCase):
    """Test cases for document permission enforcement."""
    
    def setUp(self):
        """Set up test fixtures for permission tests."""
        self.document_id = str(uuid.uuid4())
        self.owner_uid = "test-user-123"
        self.other_user_uid = "other-user-456"
        
        self.auth_headers = {
            'HTTP_AUTHORIZATION': 'Bearer fake-firebase-token'
        }
        
        # Mock services
        self.firestore_patcher = patch('apps.documents.views.firestore_service')
        self.mock_firestore = self.firestore_patcher.start()
    
    def tearDown(self):
        """Clean up patches."""
        self.firestore_patcher.stop()
    
    def _mock_authenticated_request(self, user_uid):
        """Helper to mock Firebase authentication on request."""
        return patch('apps.authz.firebase_auth.FirebaseAuthentication.authenticate', 
                    return_value=(None, user_uid))
    
    def test_access_own_document(self):
        """Test that users can access their own documents."""
        with self._mock_authenticated_request(self.owner_uid):
            document_data = {
                'document_id': self.document_id,
                'owner_uid': self.owner_uid,
                'title': 'My Document'
            }
            self.mock_firestore.get_document.return_value = document_data
            
            response = self.client.get(
                f'/api/documents/{self.document_id}/',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 200)
    
    def test_cannot_access_other_user_document(self):
        """Test that users cannot access other users' documents."""
        with self._mock_authenticated_request(self.other_user_uid):
            # Firestore service should return None for unauthorized access
            self.mock_firestore.get_document.return_value = None
            
            response = self.client.get(
                f'/api/documents/{self.document_id}/',
                **self.auth_headers
            )
            
            self.assertEqual(response.status_code, 404)
            
            # Verify the correct user_uid was used in the query
            self.mock_firestore.get_document.assert_called_with(
                self.document_id,
                self.other_user_uid
            )
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied."""
        response = self.client.get(f'/api/documents/{self.document_id}/')
        
        self.assertEqual(response.status_code, 401)
    
    def test_list_documents_scoped_to_user(self):
        """Test that document listing is scoped to authenticated user."""
        with self._mock_authenticated_request(self.owner_uid):
            self.mock_firestore.list_user_documents.return_value = []
            
            response = self.client.get('/api/documents/', **self.auth_headers)
            
            self.assertEqual(response.status_code, 200)
            
            # Verify the correct user_uid was used
            self.mock_firestore.list_user_documents.assert_called_with(
                owner_uid=self.owner_uid,
                limit=20,
                offset=0
            )