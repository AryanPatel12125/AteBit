# Legal AI Backend - Team Setup Guide

This guide helps team members get the Legal AI backend running locally with shared GCP resources.

## Prerequisites

1. Python 3.9+ installed
2. Git access to this repository
3. Shared credentials files (get from team lead)

## Quick Setup (5 minutes)

### Step 1: Clone and Install Dependencies

```bash
# Clone the repository
git clone <your-repo-url>
cd legal-ai-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### Step 2: Get Shared Credentials

Ask your team lead for these files and place them in `backend/credentials/`:
- `service-account.json` - GCP service account key
- `.env` - Environment configuration

### Step 3: Verify Setup

```bash
cd backend

# Run Django migrations
python manage.py migrate

# Test the server
python manage.py runserver

# Test GCP connection (optional)
python manage.py shell
>>> from apps.ai_services.vertex_client import VertexAIClient
>>> client = VertexAIClient()
>>> print("GCP connection successful!")
```

## Shared Resources

### GCP Project: `legal-ai-team-dev`
- **Vertex AI**: Enabled for document analysis
- **Cloud Storage**: Bucket `legal-ai-team-dev-documents`
- **Firestore**: Database for document metadata
- **Firebase**: Authentication (if using frontend)

### Service Account: `legal-ai-shared@legal-ai-team-dev.iam.gserviceaccount.com`
- Has permissions for all required GCP services
- Single shared key for all team members

## Environment Variables

Your `.env` file should contain:

```env
# Django
DJANGO_SECRET_KEY=<shared-secret-key>
DEBUG=True

# Google Cloud Project
GOOGLE_CLOUD_PROJECT=legal-ai-team-dev
GOOGLE_APPLICATION_CREDENTIALS=credentials/service-account.json

# Vertex AI
VERTEX_LOCATION=us-central1
VERTEX_MODEL_ID=gemini-1.0-pro
VERTEX_MAX_OUTPUT_TOKENS=2048
VERTEX_TEMPERATURE=0.2

# Firebase
FIREBASE_PROJECT_ID=legal-ai-team-dev
FIREBASE_CREDENTIALS=credentials/service-account.json

# Firestore
FIRESTORE_DATABASE_ID=(default)
FIRESTORE_COLLECTION_PREFIX=dev_

# Google Cloud Storage
GCS_BUCKET=legal-ai-team-dev-documents
GCS_REPORT_EXPIRY_SECONDS=3600

# Logging
LOG_LEVEL=INFO
ENABLE_VERTEX_LOGGING=True
```

## Development Workflow

### Data Isolation
Each developer gets their own data namespace:
- Firestore documents prefixed with `dev_{your_name}_`
- GCS folders: `documents/dev_{your_name}/`

### Testing AI Features
```bash
# Test document upload
curl -X POST http://localhost:8000/api/documents/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Document", "document_id": "test-123"}'

# Test AI analysis
curl -X POST http://localhost:8000/api/documents/test-123/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"analysis_type": "summary"}'
```

## Troubleshooting

### Common Issues

1. **"Application Default Credentials not found"**
   - Ensure `service-account.json` is in `backend/credentials/`
   - Check `GOOGLE_APPLICATION_CREDENTIALS` path in `.env`

2. **"Permission denied" errors**
   - Verify you're using the shared service account
   - Check that the service account has proper IAM roles

3. **Vertex AI quota errors**
   - We share quotas across the team
   - Use reasonable request sizes during development

4. **Firestore permission errors**
   - Ensure Firestore is enabled in the GCP project
   - Check that the service account has `datastore.user` role

### Getting Help

1. Check this README first
2. Ask in team chat
3. Check GCP Console for service status
4. Review Django logs: `python manage.py runserver --verbosity=2`

## Security Notes

- **Never commit credentials to git**
- The `.env` and `service-account.json` files are in `.gitignore`
- Share credentials through secure channels only
- Rotate service account keys periodically

## Cost Management

- We share GCP costs across the team
- Use development data prefixes to avoid conflicts
- Clean up test documents regularly
- Monitor usage in GCP Console