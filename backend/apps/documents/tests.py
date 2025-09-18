import io
from unittest.mock import patch, MagicMock

from django.test import TestCase

from .services.text_extractor import TextExtractor, TextExtractionError, UnsupportedFileFormatError


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
