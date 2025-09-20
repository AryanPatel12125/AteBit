# Requirements Document

## Introduction

This specification defines the requirements for the AteBit Legal Document AI Platform backend prototype. The platform enables users to upload legal documents and perform AI-powered analysis including summarization, multi-language translation, key point extraction, and risky clause detection. The system uses Firebase for authentication (frontend-handled), Vertex AI (Gemini) for document analysis, and Google Cloud Storage for file management.

The current codebase has foundational elements including Django/DRF setup, Firebase authentication, basic models, and Vertex AI client wrapper. This spec focuses on completing the core prototype features to demonstrate the platform's capabilities.

## Requirements

### Requirement 1: Document Upload and Storage

**User Story:** As a legal professional, I want to upload legal documents to the platform, so that I can analyze them using AI-powered tools.

#### Acceptance Criteria

1. WHEN a user uploads a document via POST /api/documents/ THEN the system SHALL accept PDF, DOCX, and TXT files up to 10MB
2. WHEN a document is uploaded THEN the system SHALL extract plain text content and store it in the database
3. WHEN text extraction is complete THEN the system SHALL detect the document language using Vertex AI
4. WHEN a document is processed THEN the system SHALL update the document status to ANALYZED
5. WHEN documents are stored THEN the system SHALL upload original files to Google Cloud Storage

### Requirement 2: Document Summarization

**User Story:** As a legal professional, I want to get plain-English summaries of complex legal documents, so that I can quickly understand key content without legal expertise.

#### Acceptance Criteria

1. WHEN a user requests document analysis via POST /api/documents/{id}/analyze/ THEN the system SHALL generate a summary using Vertex AI Gemini
2. WHEN generating summaries THEN the system SHALL use "explain to a 12-year-old" language complexity
3. WHEN analysis is complete THEN the system SHALL return JSON with detected_language, summary, and token_usage
4. WHEN summaries are generated THEN the system SHALL store results in the Analysis model

### Requirement 3: Multi-Language Translation

**User Story:** As a legal professional, I want to translate document summaries and content to different languages, so that I can work with international legal documents.

#### Acceptance Criteria

1. WHEN a target_language parameter is provided in analysis request THEN the system SHALL generate the summary in that language
2. WHEN translation is requested THEN the system SHALL use Vertex AI to translate the content
3. WHEN translation is complete THEN the system SHALL return both original and translated versions
4. WHEN multiple languages are requested THEN the system SHALL support common legal languages (EN, ES, FR, DE, etc.)

### Requirement 4: Key Points Extraction with Party Analysis

**User Story:** As a legal professional, I want to extract key points showing what's beneficial for each party, so that I can understand the balance of obligations and benefits.

#### Acceptance Criteria

1. WHEN key points analysis is requested THEN the system SHALL extract 5-10 key highlights using Vertex AI
2. WHEN extracting key points THEN the system SHALL categorize benefits for "first party" vs "opposing party"
3. WHEN key points are generated THEN the system SHALL provide short explanations for each point
4. WHEN analysis is complete THEN the system SHALL return structured JSON with party-specific categorization

### Requirement 5: Risky Clauses Detection

**User Story:** As a legal professional, I want to identify potentially risky or unusual clauses in documents, so that I can address potential issues before finalizing agreements.

#### Acceptance Criteria

1. WHEN risk analysis is requested THEN the system SHALL detect potentially risky clauses using Vertex AI
2. WHEN risks are identified THEN the system SHALL classify each with severity (HIGH, MEDIUM, LOW)
3. WHEN risks are found THEN the system SHALL provide rationale for why each clause is risky
4. WHEN risk analysis is complete THEN the system SHALL return JSON array with severity, clause text, and rationale

### Requirement 6: Document Download

**User Story:** As a legal professional, I want to download my uploaded documents, so that I can access the original files when needed.

#### Acceptance Criteria

1. WHEN a user requests document download via GET /api/documents/{id}/download/ THEN the system SHALL return a signed URL for the original file
2. WHEN download URLs are generated THEN the system SHALL use Google Cloud Storage signed URLs with 1-hour expiry
3. WHEN downloads are accessed THEN the system SHALL ensure only the document owner can download
4. WHEN download requests are made THEN the system SHALL return appropriate content-type headers

### Requirement 7: Authentication Integration

**User Story:** As a platform user, I want secure access to my documents only, so that my legal information remains confidential and properly isolated.

#### Acceptance Criteria

1. WHEN any API endpoint is accessed THEN the system SHALL require valid Firebase ID token in Authorization header
2. WHEN authentication fails THEN the system SHALL return 401 Unauthorized with clear error message
3. WHEN authenticated requests are made THEN the system SHALL scope all document queries to owner_uid = request.user_uid
4. WHEN unauthorized access is attempted THEN the system SHALL return 403 Forbidden
5. WHEN Firebase authentication is used THEN the system SHALL leverage existing Firebase auth middleware

### Requirement 8: Basic Error Handling

**User Story:** As a platform user, I want clear error messages when something goes wrong, so that I can understand what happened and how to fix it.

#### Acceptance Criteria

1. WHEN Vertex AI calls fail THEN the system SHALL return 503 Service Unavailable with clear error message
2. WHEN file upload fails THEN the system SHALL return appropriate error codes and messages
3. WHEN invalid requests are made THEN the system SHALL return 400 Bad Request with validation details
4. WHEN server errors occur THEN the system SHALL log errors without exposing sensitive information
5. WHEN API errors occur THEN the system SHALL return consistent JSON error format