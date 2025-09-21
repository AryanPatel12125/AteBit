# Legal Document AI Backend - Test Documentation

This document provides comprehensive information about the test suite for the legal document AI backend, covering all implemented features and functionality.

## Overview

The test suite covers all major components of the legal document AI backend:

- **Document Management**: CRUD operations, file upload/download, metadata handling
- **AI Analysis**: Document summarization, key points extraction, risk analysis, translation
- **Authentication & Authorization**: Firebase authentication, owner-based permissions
- **File Processing**: Text extraction from PDF/DOCX/TXT files, GCS storage
- **Data Storage**: Firestore integration, Django ORM compatibility
- **Error Handling**: Comprehensive error scenarios and edge cases

## Test Structure

```
backend/apps/documents/
├── test_models.py          # Model layer tests
├── test_services.py        # Service layer tests  
├── test_serializers.py     # API serialization tests
├── test_views.py          # API endpoint tests
└── run_tests.py           # Test runner script
```

## Test Categories

### 1. Model Tests (`test_models.py`)

Tests the Django models that represent our data structures:

#### DocumentModelTests
- ✅ Document creation and validation
- ✅ Field constraints and choices
- ✅ String representation and ordering
- ✅ Unique constraints and relationships
- ✅ Optional field handling

#### AnalysisModelTests  
- ✅ Analysis creation with version tracking
- ✅ JSON field validation (summary, key_points, risk_alerts)
- ✅ Token usage tracking
- ✅ Document relationship properties
- ✅ Version uniqueness constraints

#### HistoryModelTests
- ✅ Action logging and tracking
- ✅ Payload data storage
- ✅ Timestamp ordering
- ✅ Class method utilities (`log_action`)
- ✅ Document relationship handling

#### ModelRelationshipTests
- ✅ Cross-model relationships
- ✅ Multiple analyses per document
- ✅ History tracking across operations
- ✅ Cascade behavior testing

### 2. Service Tests (`test_services.py`)

Tests the service layer that handles external integrations:

#### FirestoreServiceTests
- ✅ Document CRUD operations in Firestore
- ✅ Owner-based access control
- ✅ User document listing with pagination
- ✅ Analysis result storage
- ✅ Error handling for Firestore failures

#### GCSServiceTests
- ✅ File upload validation and processing
- ✅ Signed URL generation for downloads
- ✅ File size and type validation
- ✅ Document deletion from storage
- ✅ Metadata handling and owner verification

#### TextExtractorTests
- ✅ Text extraction from PDF files
- ✅ Text extraction from DOCX files
- ✅ Plain text file processing
- ✅ MIME type detection
- ✅ File format validation
- ✅ Text cleaning and normalization
- ✅ Encoding detection for text files

#### ServiceIntegrationTests
- ✅ Complete document lifecycle workflows
- ✅ Service interaction patterns
- ✅ Error propagation between services

### 3. Serializer Tests (`test_serializers.py`)

Tests API data validation and serialization:

#### DocumentSerializerTests
- ✅ Document data serialization
- ✅ UUID validation for document_id
- ✅ Title and file type validation
- ✅ Owner context handling
- ✅ Field filtering for different views

#### DocumentUploadSerializerTests
- ✅ File upload validation
- ✅ File size limit enforcement
- ✅ Supported file type checking
- ✅ Dangerous filename detection
- ✅ Empty file handling

#### AnalysisRequestSerializerTests
- ✅ Analysis parameter validation
- ✅ Language code validation
- ✅ Parameter range checking
- ✅ Required field validation for different analysis types
- ✅ Legacy parameter conversion

#### AnalysisResultSerializerTests
- ✅ Analysis result structure validation
- ✅ Summary format validation
- ✅ Key points structure validation
- ✅ Risk alerts structure validation
- ✅ Token usage validation
- ✅ Computed field generation

### 4. View Tests (`test_views.py`)

Tests all API endpoints and their behavior:

#### DocumentViewSetTests
- ✅ Document creation with frontend-provided IDs
- ✅ Document listing with pagination
- ✅ Document retrieval with owner validation
- ✅ Document deletion with cleanup
- ✅ Firestore integration and error handling

#### DocumentUploadViewTests
- ✅ File upload and processing pipeline
- ✅ Text extraction integration
- ✅ Language detection
- ✅ Status updates during processing
- ✅ Error handling for upload failures

#### DocumentAnalyzeViewTests
- ✅ AI analysis for all supported types (summary, key_points, risks, translation)
- ✅ Combined analysis ("all" type)
- ✅ Target language support
- ✅ Analysis versioning
- ✅ Token usage tracking
- ✅ Result storage in Firestore and Django

#### DocumentDownloadViewTests
- ✅ Signed URL generation
- ✅ Custom expiry time handling
- ✅ File metadata in responses
- ✅ Owner authorization
- ✅ Missing file handling

#### DocumentAnalysisHistoryViewTests
- ✅ Latest analysis retrieval
- ✅ Specific version retrieval
- ✅ Analysis not found handling

#### PermissionTests
- ✅ Authentication requirement enforcement
- ✅ Owner-based access control
- ✅ Unauthorized access prevention

#### ErrorHandlingTests
- ✅ Invalid UUID format handling
- ✅ Service unavailability scenarios
- ✅ Unexpected error handling
- ✅ Proper HTTP status codes

#### IntegrationTests
- ✅ Complete document workflow (create → upload → analyze → download)
- ✅ Service integration patterns
- ✅ End-to-end functionality

## Running Tests

### Basic Test Execution

```bash
# Run all tests
python run_tests.py

# Run with verbose output
python run_tests.py --verbose

# Run specific test categories
python run_tests.py --models
python run_tests.py --services
python run_tests.py --serializers
python run_tests.py --views

# Run with coverage reporting
python run_tests.py --coverage
```

### Advanced Options

```bash
# Stop on first failure
python run_tests.py --failfast

# Keep test database for inspection
python run_tests.py --keepdb

# Interactive mode
python run_tests.py --interactive
```

### Coverage Reporting

The test suite includes comprehensive coverage reporting:

```bash
# Generate coverage report
python run_tests.py --coverage

# View HTML coverage report
open htmlcov/index.html
```

## Test Data and Fixtures

### Mock Data Patterns

Tests use consistent mock data patterns:

```python
# Document data
document_data = {
    'document_id': str(uuid.uuid4()),
    'title': 'Test Legal Document',
    'owner_uid': 'test-user-123',
    'file_type': 'application/pdf',
    'status': 'ANALYZED'
}

# Analysis data
analysis_data = {
    'version': 1,
    'summary': {'en': 'Summary', 'es': 'Resumen'},
    'key_points': [{'text': 'Point', 'party_benefit': 'first_party'}],
    'risk_alerts': [{'severity': 'HIGH', 'clause': 'Risk'}],
    'token_usage': {'input_tokens': 100, 'output_tokens': 50}
}
```

### File Upload Testing

Tests include various file types and scenarios:

```python
# Valid PDF file
pdf_file = SimpleUploadedFile("test.pdf", b"PDF content", content_type="application/pdf")

# Invalid file type
exe_file = SimpleUploadedFile("malware.exe", b"MZ\x90\x00", content_type="application/x-executable")

# Oversized file
large_file = SimpleUploadedFile("large.pdf", b"x" * (11 * 1024 * 1024))
```

## Mocking Strategy

### External Service Mocking

Tests mock external services to ensure isolation:

```python
# Firebase/Firestore mocking
@patch('apps.documents.services.firestore_service.firestore.Client')
def test_firestore_operation(self, mock_client):
    # Test implementation

# Google Cloud Storage mocking  
@patch('apps.documents.services.gcs_service.storage.Client')
def test_gcs_operation(self, mock_client):
    # Test implementation

# Vertex AI mocking
@patch('apps.documents.views.vertex_client')
def test_ai_analysis(self, mock_vertex):
    # Test implementation
```

### Authentication Mocking

Firebase authentication is mocked for all API tests:

```python
def authenticate_user(self):
    """Mock Firebase authentication for requests."""
    with patch('apps.authz.firebase_auth.FirebaseAuthentication.authenticate') as mock_auth:
        mock_auth.return_value = (self.mock_user, None)
        yield
```

## Test Coverage Goals

The test suite aims for comprehensive coverage:

- **Models**: 100% line coverage
- **Services**: 95%+ line coverage with error scenarios
- **Serializers**: 100% validation path coverage
- **Views**: 95%+ line coverage including error handling
- **Overall**: 90%+ line coverage across the entire document app

## Performance Testing

### Load Testing Scenarios

```python
# Large file processing
def test_large_file_processing(self):
    # Test with maximum allowed file size
    
# Concurrent analysis requests
def test_concurrent_analysis(self):
    # Test multiple simultaneous AI analysis requests
    
# Bulk document operations
def test_bulk_operations(self):
    # Test handling of multiple documents
```

### Memory Usage Testing

```python
# Memory profiling for text extraction
@profile
def test_text_extraction_memory(self):
    # Monitor memory usage during text extraction
```

## Continuous Integration

### GitHub Actions Configuration

```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r test_requirements.txt
      - name: Run tests with coverage
        run: python run_tests.py --coverage
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
```

## Test Maintenance

### Adding New Tests

When adding new features:

1. **Model Changes**: Add tests to `test_models.py`
2. **Service Changes**: Add tests to `test_services.py`
3. **API Changes**: Add tests to `test_serializers.py` and `test_views.py`
4. **Integration**: Add end-to-end tests to integration test classes

### Test Naming Conventions

```python
# Test method naming pattern
def test_{component}_{scenario}_{expected_outcome}(self):
    """Test description."""
    
# Examples
def test_document_creation_success(self):
def test_file_upload_invalid_format(self):
def test_analysis_request_missing_language(self):
```

### Mock Maintenance

Keep mocks updated with actual service interfaces:

```python
# Update mocks when service interfaces change
# Verify mock behavior matches real service behavior
# Use integration tests to catch mock/reality mismatches
```

## Debugging Tests

### Common Issues

1. **Mock Configuration**: Ensure mocks match actual service interfaces
2. **Async Handling**: Use `asyncio.run()` for async service calls in sync tests
3. **Database State**: Use transactions or database cleanup between tests
4. **File Handling**: Properly reset file pointers in upload tests

### Debug Utilities

```python
# Enable debug logging in tests
import logging
logging.basicConfig(level=logging.DEBUG)

# Print test data for debugging
def debug_test_data(self):
    print(f"Document: {self.document_data}")
    print(f"Analysis: {self.analysis_data}")
```

## Future Test Enhancements

### Planned Additions

1. **API Integration Tests**: Real API calls against test environment
2. **Performance Benchmarks**: Automated performance regression testing
3. **Security Tests**: Authentication bypass attempts, injection testing
4. **Accessibility Tests**: API response accessibility compliance
5. **Internationalization Tests**: Multi-language content handling

### Test Infrastructure Improvements

1. **Parallel Execution**: Run tests in parallel for faster feedback
2. **Test Data Factories**: More sophisticated test data generation
3. **Visual Regression**: Screenshot comparison for any UI components
4. **Contract Testing**: API contract validation between frontend/backend

This comprehensive test suite ensures the reliability, security, and performance of all implemented features in the legal document AI backend.