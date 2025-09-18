"""
Test cases for document models.

Tests the Document, Analysis, and History models including:
- Model field validation
- Model methods and properties
- Model relationships
- Custom model behaviors
"""
import uuid
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .models import Document, Analysis, History


class DocumentModelTests(TestCase):
    """Test cases for Document model."""
    
    def setUp(self):
        """Set up test data."""
        self.document_id = uuid.uuid4()
        self.owner_uid = "test-user-123"
        
        self.valid_document_data = {
            'document_id': self.document_id,
            'title': 'Test Legal Document',
            'owner_uid': self.owner_uid,
            'file_type': 'application/pdf',
            'storage_path': f'documents/{self.owner_uid}/{self.document_id}/original.pdf',
            'extracted_text': 'This is extracted text from the document.',
            'language_code': 'en',
            'status': Document.Status.ANALYZED
        }
    
    def test_create_document_success(self):
        """Test successful document creation."""
        document = Document.objects.create(**self.valid_document_data)
        
        self.assertEqual(document.document_id, self.document_id)
        self.assertEqual(document.title, 'Test Legal Document')
        self.assertEqual(document.owner_uid, self.owner_uid)
        self.assertEqual(document.status, Document.Status.ANALYZED)
        self.assertIsNotNone(document.created_at)
        self.assertIsNotNone(document.updated_at)
    
    def test_document_str_representation(self):
        """Test document string representation."""
        document = Document.objects.create(**self.valid_document_data)
        expected_str = f"Test Legal Document (ANALYZED) - {self.document_id}"
        self.assertEqual(str(document), expected_str)
    
    def test_document_ordering(self):
        """Test document ordering by updated_at descending."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create first document
        doc1 = Document.objects.create(**self.valid_document_data)
        
        # Create second document with different ID and title
        doc2_data = self.valid_document_data.copy()
        doc2_data['document_id'] = uuid.uuid4()
        doc2_data['title'] = 'Second Document'
        doc2 = Document.objects.create(**doc2_data)
        
        # Update the second document to ensure it has a later updated_at
        doc2.title = 'Second Document Updated'
        doc2.save()
        
        # Get all documents ordered by the model's default ordering
        documents = list(Document.objects.all())
        
        # doc2 should come first (more recent updated_at)
        self.assertEqual(documents[0].title, 'Second Document Updated')
        self.assertEqual(documents[1].title, 'Test Legal Document')
    
    def test_document_title_validation(self):
        """Test document title validation."""
        # Test empty title
        invalid_data = self.valid_document_data.copy()
        invalid_data['title'] = ''
        
        document = Document(**invalid_data)
        with self.assertRaises(ValidationError):
            document.full_clean()
    
    def test_document_status_choices(self):
        """Test document status choices."""
        valid_statuses = [
            Document.Status.PENDING,
            Document.Status.PROCESSING,
            Document.Status.ANALYZED,
            Document.Status.ERROR
        ]
        
        for status in valid_statuses:
            data = self.valid_document_data.copy()
            data['status'] = status
            data['document_id'] = uuid.uuid4()
            
            document = Document.objects.create(**data)
            self.assertEqual(document.status, status)
    
    def test_document_unique_primary_key(self):
        """Test that document_id must be unique."""
        Document.objects.create(**self.valid_document_data)
        
        # Try to create another document with same document_id
        duplicate_data = self.valid_document_data.copy()
        duplicate_data['title'] = 'Duplicate Document'
        
        with self.assertRaises(IntegrityError):
            Document.objects.create(**duplicate_data)
    
    def test_document_optional_fields(self):
        """Test document creation with optional fields as None."""
        minimal_data = {
            'document_id': self.document_id,
            'title': 'Minimal Document',
            'owner_uid': self.owner_uid,
            'file_type': 'application/pdf',
            'storage_path': 'test/path'
        }
        
        document = Document.objects.create(**minimal_data)
        
        self.assertIsNone(document.extracted_text)
        self.assertIsNone(document.language_code)
        self.assertEqual(document.status, Document.Status.PENDING)  # Default value


class AnalysisModelTests(TestCase):
    """Test cases for Analysis model."""
    
    def setUp(self):
        """Set up test data."""
        self.document_id = uuid.uuid4()
        
        self.valid_analysis_data = {
            'document_id': self.document_id,
            'version': 1,
            'target_language': 'es',
            'summary': {'en': 'English summary', 'es': 'Resumen en español'},
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
    
    def test_create_analysis_success(self):
        """Test successful analysis creation."""
        analysis = Analysis.objects.create(**self.valid_analysis_data)
        
        self.assertEqual(analysis.document_id, self.document_id)
        self.assertEqual(analysis.version, 1)
        self.assertEqual(analysis.target_language, 'es')
        self.assertIsInstance(analysis.summary, dict)
        self.assertIsInstance(analysis.key_points, list)
        self.assertIsInstance(analysis.risk_alerts, list)
        self.assertIsInstance(analysis.token_usage, dict)
        self.assertIsNotNone(analysis.completion_time)
    
    def test_analysis_str_representation(self):
        """Test analysis string representation."""
        analysis = Analysis.objects.create(**self.valid_analysis_data)
        expected_str = f"Analysis v1 for document {self.document_id}"
        self.assertEqual(str(analysis), expected_str)
    
    def test_analysis_ordering(self):
        """Test analysis ordering by version descending."""
        # Create version 1
        Analysis.objects.create(**self.valid_analysis_data)
        
        # Create version 2
        v2_data = self.valid_analysis_data.copy()
        v2_data['version'] = 2
        Analysis.objects.create(**v2_data)
        
        # Get all analyses
        analyses = list(Analysis.objects.all())
        
        # Version 2 should come first
        self.assertEqual(analyses[0].version, 2)
        self.assertEqual(analyses[1].version, 1)
    
    def test_analysis_unique_together(self):
        """Test that document_id + version must be unique."""
        Analysis.objects.create(**self.valid_analysis_data)
        
        # Try to create another analysis with same document_id and version
        duplicate_data = self.valid_analysis_data.copy()
        duplicate_data['target_language'] = 'fr'
        
        with self.assertRaises(IntegrityError):
            Analysis.objects.create(**duplicate_data)
    
    def test_analysis_summary_text_property(self):
        """Test summary_text property."""
        analysis = Analysis.objects.create(**self.valid_analysis_data)
        
        # Should return Spanish text (target language)
        self.assertEqual(analysis.summary_text, 'Resumen en español')
        
        # Test with no target language
        analysis.target_language = None
        analysis.save()
        self.assertEqual(analysis.summary_text, 'English summary')  # Default to English
        
        # Test with target language not in summary
        analysis.target_language = 'fr'
        analysis.save()
        self.assertEqual(analysis.summary_text, 'English summary')  # Fallback to English
    
    def test_analysis_total_tokens_property(self):
        """Test total_tokens property."""
        analysis = Analysis.objects.create(**self.valid_analysis_data)
        
        expected_total = 100 + 50  # input_tokens + output_tokens
        self.assertEqual(analysis.total_tokens, expected_total)
        
        # Test with empty token usage
        analysis.token_usage = {}
        analysis.save()
        self.assertEqual(analysis.total_tokens, 0)
    
    def test_analysis_document_property(self):
        """Test document property."""
        # Create a document first
        document = Document.objects.create(
            document_id=self.document_id,
            title='Test Document',
            owner_uid='test-user',
            file_type='application/pdf',
            storage_path='test/path'
        )
        
        analysis = Analysis.objects.create(**self.valid_analysis_data)
        
        # Should return the related document
        self.assertEqual(analysis.document, document)
        
        # Test with non-existent document
        analysis.document_id = uuid.uuid4()
        analysis.save()
        self.assertIsNone(analysis.document)
    
    def test_analysis_default_values(self):
        """Test analysis default values."""
        minimal_data = {
            'document_id': self.document_id,
            'version': 1
        }
        
        analysis = Analysis.objects.create(**minimal_data)
        
        self.assertEqual(analysis.summary, {})
        self.assertEqual(analysis.key_points, [])
        self.assertEqual(analysis.risk_alerts, [])
        self.assertEqual(analysis.token_usage, {})


class HistoryModelTests(TestCase):
    """Test cases for History model."""
    
    def setUp(self):
        """Set up test data."""
        self.document_id = uuid.uuid4()
        self.actor_uid = "test-user-123"
        
        self.valid_history_data = {
            'document_id': self.document_id,
            'action': History.Action.CREATED,
            'actor_uid': self.actor_uid,
            'version': 1,
            'payload': {'test': 'data'}
        }
    
    def test_create_history_success(self):
        """Test successful history creation."""
        history = History.objects.create(**self.valid_history_data)
        
        self.assertEqual(history.document_id, self.document_id)
        self.assertEqual(history.action, History.Action.CREATED)
        self.assertEqual(history.actor_uid, self.actor_uid)
        self.assertEqual(history.version, 1)
        self.assertEqual(history.payload, {'test': 'data'})
        self.assertIsNotNone(history.timestamp)
    
    def test_history_str_representation(self):
        """Test history string representation."""
        history = History.objects.create(**self.valid_history_data)
        expected_str = f"CREATED on document {self.document_id} by {self.actor_uid}"
        self.assertEqual(str(history), expected_str)
    
    def test_history_ordering(self):
        """Test history ordering by timestamp descending."""
        import time
        
        # Create first history entry
        history1 = History.objects.create(**self.valid_history_data)
        
        # Small delay to ensure different timestamps
        time.sleep(0.001)
        
        # Create second history entry
        second_data = self.valid_history_data.copy()
        second_data['action'] = History.Action.UPLOADED
        history2 = History.objects.create(**second_data)
        
        # Get all history entries ordered by the model's default ordering
        history_entries = list(History.objects.all())
        
        # Second entry should come first (more recent timestamp)
        self.assertEqual(history_entries[0].action, History.Action.UPLOADED)
        self.assertEqual(history_entries[1].action, History.Action.CREATED)
    
    def test_history_action_choices(self):
        """Test history action choices."""
        valid_actions = [
            History.Action.CREATED,
            History.Action.UPLOADED,
            History.Action.ANALYZED,
            History.Action.REPORT_GENERATED,
            History.Action.DOWNLOADED,
            History.Action.ERROR
        ]
        
        for action in valid_actions:
            data = self.valid_history_data.copy()
            data['action'] = action
            
            history = History.objects.create(**data)
            self.assertEqual(history.action, action)
    
    def test_history_log_action_class_method(self):
        """Test log_action class method."""
        history = History.log_action(
            document_id=self.document_id,
            action=History.Action.ANALYZED,
            actor_uid=self.actor_uid,
            version=2,
            payload={'analysis_type': 'summary'}
        )
        
        self.assertIsInstance(history, History)
        self.assertEqual(history.document_id, self.document_id)
        self.assertEqual(history.action, History.Action.ANALYZED)
        self.assertEqual(history.actor_uid, self.actor_uid)
        self.assertEqual(history.version, 2)
        self.assertEqual(history.payload, {'analysis_type': 'summary'})
    
    def test_history_document_property(self):
        """Test document property."""
        # Create a document first
        document = Document.objects.create(
            document_id=self.document_id,
            title='Test Document',
            owner_uid='test-user',
            file_type='application/pdf',
            storage_path='test/path'
        )
        
        history = History.objects.create(**self.valid_history_data)
        
        # Should return the related document
        self.assertEqual(history.document, document)
        
        # Test with non-existent document
        history.document_id = uuid.uuid4()
        history.save()
        self.assertIsNone(history.document)
    
    def test_history_optional_fields(self):
        """Test history creation with optional fields as None."""
        minimal_data = {
            'document_id': self.document_id,
            'action': History.Action.CREATED,
            'actor_uid': self.actor_uid
        }
        
        history = History.objects.create(**minimal_data)
        
        self.assertIsNone(history.version)
        self.assertIsNone(history.payload)


class ModelRelationshipTests(TestCase):
    """Test cases for model relationships and interactions."""
    
    def setUp(self):
        """Set up test data."""
        self.document_id = uuid.uuid4()
        self.owner_uid = "test-user-123"
        
        # Create a document
        self.document = Document.objects.create(
            document_id=self.document_id,
            title='Test Document',
            owner_uid=self.owner_uid,
            file_type='application/pdf',
            storage_path='test/path'
        )
    
    def test_document_with_multiple_analyses(self):
        """Test document with multiple analysis versions."""
        # Create multiple analyses for the same document
        for version in range(1, 4):
            Analysis.objects.create(
                document_id=self.document_id,
                version=version,
                summary={'en': f'Summary v{version}'},
                token_usage={'input_tokens': 100 * version, 'output_tokens': 50 * version}
            )
        
        # Get all analyses for the document
        analyses = Analysis.objects.filter(document_id=self.document_id).order_by('-version')
        
        self.assertEqual(len(analyses), 3)
        self.assertEqual(analyses[0].version, 3)  # Latest version first
        self.assertEqual(analyses[2].version, 1)  # Oldest version last
    
    def test_document_with_history_entries(self):
        """Test document with multiple history entries."""
        actions = [
            History.Action.CREATED,
            History.Action.UPLOADED,
            History.Action.ANALYZED,
            History.Action.DOWNLOADED
        ]
        
        # Create history entries
        for action in actions:
            History.objects.create(
                document_id=self.document_id,
                action=action,
                actor_uid=self.owner_uid
            )
        
        # Get all history entries for the document
        history_entries = History.objects.filter(document_id=self.document_id)
        
        self.assertEqual(len(history_entries), 4)
        
        # Check that all actions are present
        recorded_actions = [entry.action for entry in history_entries]
        for action in actions:
            self.assertIn(action, recorded_actions)
    
    def test_cascade_behavior(self):
        """Test that related objects are handled properly when document is deleted."""
        # Create analysis and history for the document
        Analysis.objects.create(
            document_id=self.document_id,
            version=1,
            summary={'en': 'Test summary'}
        )
        
        History.objects.create(
            document_id=self.document_id,
            action=History.Action.CREATED,
            actor_uid=self.owner_uid
        )
        
        # Verify they exist
        self.assertEqual(Analysis.objects.filter(document_id=self.document_id).count(), 1)
        self.assertEqual(History.objects.filter(document_id=self.document_id).count(), 1)
        
        # Delete the document
        self.document.delete()
        
        # Analysis and History should still exist (they reference document_id, not the Document model)
        self.assertEqual(Analysis.objects.filter(document_id=self.document_id).count(), 1)
        self.assertEqual(History.objects.filter(document_id=self.document_id).count(), 1)


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
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["apps.documents.test_models"])