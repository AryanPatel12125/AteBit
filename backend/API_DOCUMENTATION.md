# AteBit Legal Document AI Platform - API Documentation

## Overview

The AteBit Legal Document AI Platform provides a REST API for uploading, processing, and analyzing legal documents using AI-powered tools. The API enables document summarization, multi-language translation, key point extraction, and risk analysis.

## Base URL

```
http://localhost:8000/api
```

## Authentication

All API endpoints require Firebase Authentication. Include the Firebase ID token in the Authorization header:

```bash
Authorization: Bearer <firebase-id-token>
```

## Content Types

- **JSON requests**: `Content-Type: application/json`
- **File uploads**: `Content-Type: multipart/form-data`
- **Responses**: `Content-Type: application/json`

## Error Response Format

All error responses follow a consistent format:

```json
{
  "error": "Error message description",
  "detail": "Additional error details (optional)",
  "code": "ERROR_CODE (optional)"
}
```

## HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `204 No Content` - Resource deleted successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - File processing error
- `503 Service Unavailable` - External service error
- `500 Internal Server Error` - Server error

---

## API Endpoints

### 1. System Endpoints

#### Health Check

Check if the API is running and healthy.

**Endpoint:** `GET /api/health/`

**Authentication:** Not required

**curl Example:**
```bash
curl -X GET http://localhost:8000/api/health/
```

**Response:**
```json
{
  "status": "healthy",
  "message": "Backend running - AteBit Legal Document Platform",
  "version": "1.0.0-dev"
}
```

#### Version Information

Get API version information.

**Endpoint:** `GET /api/version/`

**Authentication:** Not required

**curl Example:**
```bash
curl -X GET http://localhost:8000/api/version/
```

**Response:**
```json
{
  "version": "1.0.0-dev",
  "api_version": "v1",
  "platform": "AteBit Legal Document AI Platform"
}
```

---

### 2. Document Management

#### Create Document

Create a new document with metadata. The frontend should generate a UUID for the document_id to ensure consistency across Firebase services.

**Endpoint:** `POST /api/documents/`

**Authentication:** Required

**Request Body:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Rental Agreement Contract",
  "file_type": "application/pdf"
}
```

**curl Example:**
```bash
curl -X POST http://localhost:8000/api/documents/ \
  -H "Authorization: Bearer <firebase-id-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Rental Agreement Contract",
    "file_type": "application/pdf"
  }'
```

**Response (201 Created):**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Rental Agreement Contract",
  "owner_uid": "firebase-user-uid",
  "file_type": "application/pdf",
  "storage_path": "",
  "extracted_text": null,
  "language_code": null,
  "status": "PENDING",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### List Documents

Retrieve a paginated list of documents for the authenticated user.

**Endpoint:** `GET /api/documents/`

**Authentication:** Required

**Query Parameters:**
- `limit` (optional): Number of documents to return (default: 20, max: 100)
- `offset` (optional): Number of documents to skip (default: 0)

**curl Example:**
```bash
curl -X GET "http://localhost:8000/api/documents/?limit=10&offset=0" \
  -H "Authorization: Bearer <firebase-id-token>"
```

**Response (200 OK):**
```json
{
  "results": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Rental Agreement Contract",
      "file_type": "application/pdf",
      "status": "ANALYZED",
      "language_code": "en",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:35:00Z"
    }
  ],
  "count": 1,
  "limit": 10,
  "offset": 0,
  "has_more": false
}
```

#### Get Document Details

Retrieve detailed information about a specific document.

**Endpoint:** `GET /api/documents/{document_id}/`

**Authentication:** Required

**curl Example:**
```bash
curl -X GET http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer <firebase-id-token>"
```

**Response (200 OK):**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Rental Agreement Contract",
  "owner_uid": "firebase-user-uid",
  "file_type": "application/pdf",
  "storage_path": "documents/firebase-user-uid/550e8400-e29b-41d4-a716-446655440000/original.pdf",
  "extracted_text": "RENTAL AGREEMENT\n\nThis rental agreement...",
  "language_code": "en",
  "status": "ANALYZED",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

#### Delete Document

Delete a document and all associated files.

**Endpoint:** `DELETE /api/documents/{document_id}/`

**Authentication:** Required

**curl Example:**
```bash
curl -X DELETE http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer <firebase-id-token>"
```

**Response (204 No Content):**
```
(Empty response body)
```

---

### 3. File Operations

#### Upload Document File

Upload and process a document file. This endpoint extracts text, detects language, and stores the file in Google Cloud Storage.

**Endpoint:** `POST /api/documents/{document_id}/upload/`

**Authentication:** Required

**Content-Type:** `multipart/form-data`

**Supported File Types:**
- PDF (`.pdf`) - `application/pdf`
- Word Documents (`.docx`) - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Plain Text (`.txt`) - `text/plain`

**File Size Limit:** 10MB

**curl Example:**
```bash
curl -X POST http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/upload/ \
  -H "Authorization: Bearer <firebase-id-token>" \
  -F "file=@/path/to/rental_agreement.pdf"
```

**Response (200 OK):**
```json
{
  "message": "File uploaded and processed successfully",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_info": {
    "original_filename": "rental_agreement.pdf",
    "file_size": 245760,
    "mime_type": "application/pdf",
    "storage_path": "documents/firebase-user-uid/550e8400-e29b-41d4-a716-446655440000/original.pdf"
  },
  "processing_results": {
    "text_length": 1250,
    "detected_language": "en",
    "detected_encoding": "utf-8",
    "extraction_metadata": {
      "pages": 3,
      "title": "Rental Agreement"
    }
  },
  "status": "ANALYZED"
}
```

**Error Responses:**

*File too large (400 Bad Request):*
```json
{
  "error": "File size exceeds maximum allowed size of 10MB"
}
```

*Unsupported file type (400 Bad Request):*
```json
{
  "error": "Unsupported file type. Supported types: PDF, DOCX, TXT"
}
```

*Text extraction failed (422 Unprocessable Entity):*
```json
{
  "error": "Text extraction failed",
  "detail": "Unable to extract text from the uploaded file"
}
```

#### Download Document

Generate a signed URL for downloading the original document file.

**Endpoint:** `GET /api/documents/{document_id}/download/`

**Authentication:** Required

**curl Example:**
```bash
curl -X GET http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/download/ \
  -H "Authorization: Bearer <firebase-id-token>"
```

**Response (200 OK):**
```json
{
  "download_url": "https://storage.googleapis.com/bucket-name/documents/user-uid/doc-id/original.pdf?X-Goog-Algorithm=...",
  "expires_at": "2024-01-15T11:35:00Z",
  "content_type": "application/pdf",
  "file_size": 245760,
  "original_filename": "rental_agreement.pdf"
}
```

---

### 4. AI Analysis

#### Analyze Document

Perform AI-powered analysis on a document. Supports multiple analysis types and multi-language output.

**Endpoint:** `POST /api/documents/{document_id}/analyze/`

**Authentication:** Required

**Request Body:**
```json
{
  "analysis_type": "summary",
  "target_language": "en"
}
```

**Analysis Types:**
- `summary` - Generate plain-English summary
- `key_points` - Extract key points with party analysis
- `risks` - Detect risky or unusual clauses
- `translation` - Translate document content
- `all` - Perform all analysis types

**Supported Languages:**
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `pt` - Portuguese
- `it` - Italian

#### Document Summary

**curl Example:**
```bash
curl -X POST http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/analyze/ \
  -H "Authorization: Bearer <firebase-id-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "summary",
    "target_language": "en"
  }'
```

**Response (200 OK):**
```json
{
  "detected_language": "en",
  "target_language": "en",
  "summary": "This is a rental agreement between a landlord and tenant. The tenant agrees to pay $1,200 per month for rent. There is a security deposit that can be returned if there are no damages. The landlord has some rules about pets and can end the agreement if the tenant breaks the rules.",
  "confidence": 0.94,
  "token_usage": {
    "input_tokens": 1250,
    "output_tokens": 85,
    "total_tokens": 1335
  },
  "analysis_id": "analysis_550e8400_summary_v1",
  "created_at": "2024-01-15T10:40:00Z"
}
```

#### Key Points Extraction

**curl Example:**
```bash
curl -X POST http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/analyze/ \
  -H "Authorization: Bearer <firebase-id-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "key_points",
    "target_language": "en"
  }'
```

**Response (200 OK):**
```json
{
  "detected_language": "en",
  "target_language": "en",
  "key_points": [
    {
      "text": "Monthly rent is $1,200",
      "explanation": "The tenant must pay this amount every month on the 1st",
      "party_benefit": "opposing_party",
      "citation": "chars:150-180",
      "importance": "high"
    },
    {
      "text": "Security deposit refundable",
      "explanation": "Tenant gets the deposit back if there are no damages",
      "party_benefit": "first_party",
      "citation": "chars:200-250",
      "importance": "medium"
    },
    {
      "text": "No pets allowed",
      "explanation": "Tenant cannot have any animals in the rental property",
      "party_benefit": "opposing_party",
      "citation": "chars:300-320",
      "importance": "medium"
    }
  ],
  "confidence": 0.91,
  "token_usage": {
    "input_tokens": 1250,
    "output_tokens": 120,
    "total_tokens": 1370
  },
  "analysis_id": "analysis_550e8400_key_points_v1",
  "created_at": "2024-01-15T10:42:00Z"
}
```

#### Risk Analysis

**curl Example:**
```bash
curl -X POST http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/analyze/ \
  -H "Authorization: Bearer <firebase-id-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "risks",
    "target_language": "en"
  }'
```

**Response (200 OK):**
```json
{
  "detected_language": "en",
  "target_language": "en",
  "risks": [
    {
      "severity": "HIGH",
      "clause": "Landlord may enter without notice",
      "rationale": "This violates tenant privacy rights in most jurisdictions and may be illegal",
      "location": "chars:400-450",
      "risk_category": "privacy_violation"
    },
    {
      "severity": "MEDIUM",
      "clause": "30-day notice required for termination",
      "rationale": "Standard clause but could be problematic in emergency situations",
      "location": "chars:500-550",
      "risk_category": "termination_terms"
    }
  ],
  "risk_summary": {
    "high_risks": 1,
    "medium_risks": 1,
    "low_risks": 0,
    "overall_assessment": "MEDIUM"
  },
  "confidence": 0.87,
  "token_usage": {
    "input_tokens": 1250,
    "output_tokens": 95,
    "total_tokens": 1345
  },
  "analysis_id": "analysis_550e8400_risks_v1",
  "created_at": "2024-01-15T10:44:00Z"
}
```

#### Translation

**curl Example:**
```bash
curl -X POST http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/analyze/ \
  -H "Authorization: Bearer <firebase-id-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "translation",
    "target_language": "es"
  }'
```

**Response (200 OK):**
```json
{
  "original_language": "en",
  "target_language": "es",
  "original_content": "RENTAL AGREEMENT\n\nThis rental agreement is between John Doe (Tenant) and Jane Smith (Landlord)...",
  "translated_content": "ACUERDO DE ALQUILER\n\nEste acuerdo de alquiler es entre John Doe (Inquilino) y Jane Smith (Propietario)...",
  "confidence": 0.93,
  "token_usage": {
    "input_tokens": 800,
    "output_tokens": 850,
    "total_tokens": 1650
  },
  "analysis_id": "analysis_550e8400_translation_es_v1",
  "created_at": "2024-01-15T10:46:00Z"
}
```

#### Comprehensive Analysis

Perform all analysis types in a single request:

**curl Example:**
```bash
curl -X POST http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/analyze/ \
  -H "Authorization: Bearer <firebase-id-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "all",
    "target_language": "es"
  }'
```

**Response (200 OK):**
```json
{
  "summary": {
    "detected_language": "en",
    "target_language": "es",
    "summary": "Este es un acuerdo de alquiler entre un propietario y un inquilino...",
    "confidence": 0.94,
    "token_usage": {
      "input_tokens": 1250,
      "output_tokens": 90,
      "total_tokens": 1340
    }
  },
  "key_points": {
    "detected_language": "en",
    "target_language": "es",
    "key_points": [
      {
        "text": "Alquiler mensual es $1,200",
        "explanation": "El inquilino debe pagar esta cantidad cada mes",
        "party_benefit": "opposing_party",
        "citation": "chars:150-180",
        "importance": "high"
      }
    ],
    "confidence": 0.91,
    "token_usage": {
      "input_tokens": 1250,
      "output_tokens": 125,
      "total_tokens": 1375
    }
  },
  "risks": {
    "detected_language": "en",
    "target_language": "es",
    "risks": [
      {
        "severity": "HIGH",
        "clause": "El propietario puede entrar sin aviso",
        "rationale": "Esto viola los derechos de privacidad del inquilino",
        "location": "chars:400-450",
        "risk_category": "privacy_violation"
      }
    ],
    "risk_summary": {
      "high_risks": 1,
      "medium_risks": 1,
      "low_risks": 0,
      "overall_assessment": "MEDIUM"
    },
    "confidence": 0.87,
    "token_usage": {
      "input_tokens": 1250,
      "output_tokens": 100,
      "total_tokens": 1350
    }
  },
  "translation": {
    "original_language": "en",
    "target_language": "es",
    "original_content": "RENTAL AGREEMENT...",
    "translated_content": "ACUERDO DE ALQUILER...",
    "confidence": 0.93,
    "token_usage": {
      "input_tokens": 800,
      "output_tokens": 850,
      "total_tokens": 1650
    }
  },
  "total_token_usage": {
    "input_tokens": 4550,
    "output_tokens": 1165,
    "total_tokens": 5715
  },
  "analysis_id": "analysis_550e8400_all_es_v1",
  "created_at": "2024-01-15T10:48:00Z"
}
```

**Analysis Error Responses:**

*Document not found (404 Not Found):*
```json
{
  "error": "Document not found or unauthorized"
}
```

*No extracted text (400 Bad Request):*
```json
{
  "error": "Document has no extracted text. Please upload a file first."
}
```

*Invalid analysis type (400 Bad Request):*
```json
{
  "error": "Unsupported analysis type: invalid_type"
}
```

*Missing target language for translation (400 Bad Request):*
```json
{
  "error": "target_language is required for translation analysis"
}
```

*AI service unavailable (503 Service Unavailable):*
```json
{
  "error": "AI analysis service temporarily unavailable",
  "detail": "Please try again in a few moments"
}
```

---

## Complete Workflow Example

Here's a complete example of the document workflow from creation to analysis:

### Step 1: Create Document

```bash
# Create document metadata
curl -X POST http://localhost:8000/api/documents/ \
  -H "Authorization: Bearer <firebase-id-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Software License Agreement",
    "file_type": "application/pdf"
  }'
```

### Step 2: Upload File

```bash
# Upload and process the document file
curl -X POST http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/upload/ \
  -H "Authorization: Bearer <firebase-id-token>" \
  -F "file=@/path/to/software_license.pdf"
```

### Step 3: Analyze Document

```bash
# Get document summary
curl -X POST http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/analyze/ \
  -H "Authorization: Bearer <firebase-id-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "summary",
    "target_language": "en"
  }'

# Extract key points
curl -X POST http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/analyze/ \
  -H "Authorization: Bearer <firebase-id-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "key_points",
    "target_language": "en"
  }'

# Analyze risks
curl -X POST http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/analyze/ \
  -H "Authorization: Bearer <firebase-id-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "risks",
    "target_language": "en"
  }'
```

### Step 4: Download Document

```bash
# Get download URL
curl -X GET http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/download/ \
  -H "Authorization: Bearer <firebase-id-token>"
```

### Step 5: List Documents

```bash
# List all documents
curl -X GET http://localhost:8000/api/documents/ \
  -H "Authorization: Bearer <firebase-id-token>"
```

---

## Firebase Configuration Setup

### Prerequisites

1. **Google Cloud Project**: Create a project in Google Cloud Console
2. **Firebase Project**: Enable Firebase for your Google Cloud project
3. **Service Account**: Create a service account with appropriate permissions
4. **Vertex AI**: Enable Vertex AI API in your Google Cloud project
5. **Cloud Storage**: Create a storage bucket for document files

### Required Environment Variables

Create a `.env` file in the backend directory:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GCS_BUCKET_NAME=your-storage-bucket-name

# Firebase Configuration
FIREBASE_PROJECT_ID=your-firebase-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Vertex AI Configuration
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL_ID=gemini-1.0-pro

# Django Configuration
SECRET_KEY=your-django-secret-key
DEBUG=True
```

### Service Account Permissions

Your service account needs the following IAM roles:

- `Firebase Admin SDK Administrator Service Agent`
- `Cloud Storage Object Admin`
- `Vertex AI User`
- `Firestore User`

### Firebase Authentication Setup

1. **Enable Authentication**: In Firebase Console, enable Authentication
2. **Configure Providers**: Set up your preferred authentication providers
3. **Get Config**: Download the Firebase config for your web app
4. **Frontend Integration**: Configure Firebase Auth in your frontend application

### Testing Authentication

You can test authentication by getting a Firebase ID token from your frontend and using it in API requests:

```javascript
// Frontend JavaScript example
import { getAuth } from 'firebase/auth';

const auth = getAuth();
const user = auth.currentUser;
if (user) {
  const idToken = await user.getIdToken();
  // Use idToken in Authorization header
}
```

---

## Rate Limiting and Quotas

### API Rate Limits

- **Document uploads**: 10 files per minute per user
- **Analysis requests**: 20 requests per minute per user
- **General API calls**: 100 requests per minute per user

### File Size Limits

- **Maximum file size**: 10MB per document
- **Supported formats**: PDF, DOCX, TXT
- **Text extraction limit**: 50,000 characters per document

### Vertex AI Quotas

- **Token limits**: Varies by model and region
- **Request limits**: 60 requests per minute (default)
- **Concurrent requests**: 10 simultaneous requests

### Storage Limits

- **Document retention**: 90 days for free tier
- **Storage quota**: 1GB per user (free tier)

---

## Error Handling Best Practices

### Retry Logic

Implement exponential backoff for transient errors:

```bash
# Example retry script
for i in {1..3}; do
  response=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/api/documents/analyze/ \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -d '{"analysis_type": "summary"}')
  
  if [[ "${response: -3}" == "200" ]]; then
    echo "Success"
    break
  elif [[ "${response: -3}" == "503" ]]; then
    echo "Service unavailable, retrying in $((2**i)) seconds..."
    sleep $((2**i))
  else
    echo "Error: ${response: -3}"
    break
  fi
done
```

### Common Error Scenarios

1. **Authentication Errors**
   - Expired Firebase token
   - Invalid token format
   - Missing Authorization header

2. **File Upload Errors**
   - File too large
   - Unsupported file type
   - Corrupted file

3. **Analysis Errors**
   - Document not processed yet
   - AI service temporarily unavailable
   - Invalid analysis parameters

4. **Network Errors**
   - Connection timeout
   - Service unavailable
   - Rate limit exceeded

---

## SDK and Client Libraries

### Python Client Example

```python
import requests
import json

class AteBitClient:
    def __init__(self, base_url, firebase_token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {firebase_token}',
            'Content-Type': 'application/json'
        }
    
    def create_document(self, document_id, title, file_type):
        data = {
            'document_id': document_id,
            'title': title,
            'file_type': file_type
        }
        response = requests.post(
            f'{self.base_url}/documents/',
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def upload_file(self, document_id, file_path):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f'{self.base_url}/documents/{document_id}/upload/',
                headers={'Authorization': self.headers['Authorization']},
                files=files
            )
        return response.json()
    
    def analyze_document(self, document_id, analysis_type, target_language=None):
        data = {'analysis_type': analysis_type}
        if target_language:
            data['target_language'] = target_language
        
        response = requests.post(
            f'{self.base_url}/documents/{document_id}/analyze/',
            headers=self.headers,
            json=data
        )
        return response.json()

# Usage example
client = AteBitClient('http://localhost:8000/api', 'your-firebase-token')

# Create document
doc = client.create_document(
    '550e8400-e29b-41d4-a716-446655440000',
    'Contract Analysis',
    'application/pdf'
)

# Upload file
upload_result = client.upload_file(
    '550e8400-e29b-41d4-a716-446655440000',
    '/path/to/contract.pdf'
)

# Analyze document
summary = client.analyze_document(
    '550e8400-e29b-41d4-a716-446655440000',
    'summary',
    'en'
)
```

### JavaScript/Node.js Client Example

```javascript
class AteBitClient {
  constructor(baseUrl, firebaseToken) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${firebaseToken}`,
      'Content-Type': 'application/json'
    };
  }

  async createDocument(documentId, title, fileType) {
    const response = await fetch(`${this.baseUrl}/documents/`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        document_id: documentId,
        title: title,
        file_type: fileType
      })
    });
    return response.json();
  }

  async uploadFile(documentId, file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/documents/${documentId}/upload/`, {
      method: 'POST',
      headers: {
        'Authorization': this.headers.Authorization
      },
      body: formData
    });
    return response.json();
  }

  async analyzeDocument(documentId, analysisType, targetLanguage = null) {
    const data = { analysis_type: analysisType };
    if (targetLanguage) {
      data.target_language = targetLanguage;
    }

    const response = await fetch(`${this.baseUrl}/documents/${documentId}/analyze/`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(data)
    });
    return response.json();
  }
}

// Usage example
const client = new AteBitClient('http://localhost:8000/api', 'your-firebase-token');

// Create and analyze document
async function processDocument() {
  try {
    // Create document
    const doc = await client.createDocument(
      '550e8400-e29b-41d4-a716-446655440000',
      'Legal Contract',
      'application/pdf'
    );

    // Upload file (assuming you have a file input)
    const fileInput = document.getElementById('file-input');
    const uploadResult = await client.uploadFile(
      '550e8400-e29b-41d4-a716-446655440000',
      fileInput.files[0]
    );

    // Analyze document
    const analysis = await client.analyzeDocument(
      '550e8400-e29b-41d4-a716-446655440000',
      'summary',
      'en'
    );

    console.log('Analysis result:', analysis);
  } catch (error) {
    console.error('Error processing document:', error);
  }
}
```

---

## Changelog

### Version 1.0.0-dev

**Features:**
- Document upload and text extraction
- AI-powered document analysis (summary, key points, risks)
- Multi-language translation support
- Firebase authentication integration
- Google Cloud Storage for file management
- Firestore for metadata and analysis storage

**Supported Analysis Types:**
- Document summarization in plain English
- Key points extraction with party analysis
- Risk and clause analysis with severity ratings
- Multi-language translation (EN, ES, FR, DE, PT, IT)

**API Endpoints:**
- Document CRUD operations
- File upload and download
- AI analysis with multiple types
- System health and version endpoints

---

## Support and Contact

For technical support or questions about the AteBit Legal Document AI Platform API:

- **Documentation**: This document
- **Issues**: Report bugs and feature requests through your project management system
- **Email**: Contact your development team
- **Status Page**: Check system status at your monitoring dashboard

---

*Last updated: January 2024*
*API Version: v1*
*Platform: AteBit Legal Document AI Platform*