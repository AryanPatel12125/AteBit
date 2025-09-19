# AteBit Legal Document AI - Frontend Testing Interface

## Overview

This frontend provides a comprehensive testing interface for the AteBit Legal Document AI backend API. It's designed to test all backend functionalities without requiring a full production frontend implementation.

## Features

### 1. System Status Tab
- **Backend Health Monitoring**: Real-time health checks with automatic refresh
- **Authentication Setup**: Configure Firebase tokens for API testing
- **API Endpoint Documentation**: Complete list of available endpoints
- **Version Information**: Backend version and status display

### 2. Document Management Tab
- **Create Documents**: Generate new document records with unique IDs
- **List Documents**: View all documents with pagination support
- **Document Selection**: Choose documents for upload and analysis operations
- **Document Details**: View metadata including creation time, file type, and status

### 3. File Upload Tab
- **File Upload**: Support for PDF, TXT, and DOCX files (up to 10MB)
- **Sample Documents**: Pre-built legal documents for testing:
  - Rental Agreement (comprehensive lease terms)
  - Employment Contract (with stock options and non-compete)
  - Service Agreement (web development contract)
  - Non-Disclosure Agreement (5-year confidentiality terms)
- **Format Options**: Generate both text and PDF versions of sample documents
- **Download Testing**: Generate and test signed download URLs

### 4. AI Analysis Tab
- **Analysis Types**:
  - **Summary**: Plain-English document summaries
  - **Key Points**: Extract important clauses and party information
  - **Risks**: Identify potentially risky or unusual clauses
  - **Translation**: Multi-language document translation
  - **All**: Run comprehensive analysis with all types
- **Language Support**: English, Spanish, French, German, Italian, Portuguese
- **Real-time Progress**: Live status updates during analysis

### 5. Results Tab
- **Analysis History**: View all completed analyses with timestamps
- **Token Usage Tracking**: Monitor AI model token consumption
- **Formatted Output**: JSON results with syntax highlighting
- **Result Management**: Clear results and export capabilities

### 6. Testing Tab
- **Complete Workflow Test**: End-to-end testing (Create → Upload → Analyze → Download)
- **Error Scenario Testing**: Comprehensive error handling validation:
  - Invalid authentication tokens
  - Missing authentication
  - Non-existent document IDs
  - Invalid document ID formats
  - Upload to non-existent documents
  - Analysis on non-existent documents
  - Invalid analysis types
  - Invalid language codes
  - Large file upload testing
  - Unsupported file type testing

## Technical Implementation

### Architecture
- **Framework**: Next.js 14.2.15 with React 18.3.1
- **TypeScript**: Full type safety with 5.6.3
- **API Service**: Centralized API client with error handling
- **Error Boundaries**: Comprehensive error catching and display
- **Real-time Updates**: Live status monitoring and progress tracking

### API Integration
- **Authentication**: Firebase token-based authentication
- **Error Handling**: Proper HTTP status code handling and user feedback
- **File Operations**: FormData uploads with progress tracking
- **JSON APIs**: RESTful API calls with proper headers and body formatting

### Sample Data
- **Legal Documents**: Realistic legal document samples with various clause types
- **PDF Generation**: Simple PDF creation for testing file upload functionality
- **UUID Generation**: Proper document ID generation using crypto.randomUUID()

## Usage Instructions

### Getting Started
1. **Start Backend**: Ensure Django backend is running on `http://localhost:8000`
2. **Configure Token**: Set Firebase token in Status tab (use "demo-token-for-testing" for development)
3. **Test Connection**: Verify backend connectivity with health check

### Basic Workflow
1. **Create Document**: Go to Documents tab and create a new document
2. **Upload File**: Use Upload tab to upload a file or select a sample document
3. **Run Analysis**: Use Analysis tab to perform AI analysis on the uploaded document
4. **View Results**: Check Results tab for analysis output and token usage
5. **Download**: Test file download functionality

### Error Testing
1. **Go to Testing Tab**: Access comprehensive error testing suite
2. **Run Workflow Test**: Test complete end-to-end functionality
3. **Run Error Tests**: Validate error handling across all scenarios
4. **Review Results**: Check test outcomes and error responses

## Development Notes

### Environment Variables
- `NEXT_PUBLIC_API_URL`: Backend API URL (defaults to http://localhost:8000)

### File Structure
```
frontend/
├── app/
│   └── page.tsx              # Main testing interface
├── components/
│   ├── ErrorBoundary.tsx     # Error handling component
│   └── ErrorTestingPanel.tsx # Comprehensive error testing
├── services/
│   └── api.ts               # API service client
├── utils/
│   └── sampleDocuments.ts   # Sample document generator
└── TESTING_INTERFACE.md     # This documentation
```

### API Service Features
- **Type Safety**: Full TypeScript interfaces for all API responses
- **Error Handling**: Consistent error response formatting
- **Token Management**: Automatic authentication header injection
- **File Uploads**: Proper FormData handling for file operations
- **Utility Methods**: Document ID generation, file size formatting, date formatting

## Testing Scenarios Covered

### Positive Test Cases
- ✅ Document creation and management
- ✅ File upload (PDF, TXT, DOCX)
- ✅ AI analysis (all types and languages)
- ✅ File download URL generation
- ✅ Authentication with valid tokens
- ✅ Pagination and listing

### Error Test Cases
- ❌ Invalid authentication (401/403 responses)
- ❌ Missing authentication (401 responses)
- ❌ Non-existent resources (404 responses)
- ❌ Invalid data formats (400 responses)
- ❌ File size limits (413 responses)
- ❌ Unsupported file types (415 responses)
- ❌ Invalid analysis parameters (400 responses)

### Performance Testing
- 📊 Token usage tracking
- 📊 Response time monitoring
- 📊 File upload progress
- 📊 Large file handling

## Security Testing
- 🔒 Authentication bypass attempts
- 🔒 Invalid token handling
- 🔒 Cross-document access validation
- 🔒 File type validation
- 🔒 Input sanitization testing

This testing interface provides comprehensive coverage of all backend functionality and serves as both a development tool and a validation suite for the AteBit Legal Document AI platform.