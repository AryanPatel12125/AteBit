# Credential Setup Guide for Team Members

## Quick Setup (2 minutes)

### 1. Get Credential Files from Team Lead
Ask your team lead for these files:
- `service-account-key.json` - GCP service account key
- `.env` - Environment configuration file

### 2. Place Files in Correct Locations
```
backend/
├── credentials/
│   └── service-account-key.json  ← Place here
└── .env  ← Place here
```

### 3. Verify Setup
```bash
cd backend
python manage.py shell

# Test GCP connection
>>> import os
>>> print("Project:", os.getenv('GOOGLE_CLOUD_PROJECT'))
>>> print("Credentials:", os.path.exists(os.getenv('GOOGLE_APPLICATION_CREDENTIALS')))

# Test Vertex AI
>>> from apps.ai_services.vertex_client import VertexAIClient
>>> client = VertexAIClient()
>>> print("Vertex AI client created successfully!")
```

## What These Credentials Provide

### `service-account-key.json`
- **Vertex AI Access**: Call Gemini models for document analysis
- **Cloud Storage Access**: Upload/download documents
- **Firestore Access**: Store document metadata and analysis results

### `.env` File Contents
```env
GOOGLE_CLOUD_PROJECT=legal-ai-team-shared
GOOGLE_APPLICATION_CREDENTIALS=credentials/service-account-key.json
VERTEX_LOCATION=us-central1
VERTEX_MODEL_ID=gemini-1.0-pro
# ... other configuration
```

## Team Shared Resources

### GCP Project: `legal-ai-team-shared`
- **Vertex AI**: Enabled with Gemini models
- **Cloud Storage**: Bucket `legal-ai-team-shared-documents`
- **Firestore**: Database for metadata storage

### Service Account: `legal-ai-backend@legal-ai-team-shared.iam.gserviceaccount.com`
- Shared across all team members
- Has minimum required permissions
- Single key file for simplicity

## Development Data Isolation

To avoid conflicts, each developer should use prefixes:

```python
# In your code, use developer-specific prefixes
DEVELOPER_NAME = os.getenv('DEVELOPER_NAME', 'dev')

# Firestore documents
document_id = f"{DEVELOPER_NAME}_{uuid4()}"

# GCS paths
storage_path = f"documents/{DEVELOPER_NAME}/{document_id}/"
```

## Security Best Practices

### ✅ Do:
- Keep credential files in the specified directories
- Use secure channels to share credentials
- Rotate credentials if compromised
- Use development prefixes to isolate data

### ❌ Don't:
- Commit credential files to git
- Share credentials in public channels
- Use production data for development
- Modify shared GCP resources without team coordination

## Troubleshooting

### "Application Default Credentials not found"
```bash
# Check file exists
ls -la backend/credentials/service-account-key.json

# Check .env file
cat backend/.env | grep GOOGLE_APPLICATION_CREDENTIALS
```

### "Permission denied" errors
- Verify you're using the shared service account key
- Check that the service account has required IAM roles
- Ensure GCP project ID is correct

### Vertex AI quota errors
- We share quotas across the team
- Use reasonable request sizes during development
- Coordinate heavy testing with team

## Getting Help

1. Check this guide first
2. Verify your file paths match exactly
3. Test with the verification commands above
4. Ask in team chat with specific error messages