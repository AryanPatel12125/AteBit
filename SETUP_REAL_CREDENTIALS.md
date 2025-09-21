# Setup Real GCP Credentials - Quick Guide

This guide helps you get real GCP credentials working in your project so you can test with actual Vertex AI instead of mocks.

## Step 1: Get Your GCP Project Ready

### Option A: Use Google Cloud Console (Easiest)

1. **Go to Google Cloud Console:** https://console.cloud.google.com/
2. **Create or select a project**
3. **Enable APIs:**
   - Go to "APIs & Services" > "Library"
   - Search and enable: "Vertex AI API"
   - Search and enable: "Cloud Storage API" 
   - Search and enable: "Firestore API"

### Option B: Use gcloud CLI (If you have it installed)

```bash
# Create project
gcloud projects create your-legal-ai-project

# Set as default
gcloud config set project your-legal-ai-project

# Enable APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable firestore.googleapis.com
```

## Step 2: Create Service Account

### Using Google Cloud Console:

1. **Go to IAM & Admin > Service Accounts:** https://console.cloud.google.com/iam-admin/serviceaccounts
2. **Click "Create Service Account"**
3. **Fill in details:**
   - Name: `legal-ai-backend`
   - Description: `Service account for Legal AI backend`
4. **Click "Create and Continue"**
5. **Add these roles:**
   - `Vertex AI User`
   - `Storage Admin` (if using Cloud Storage)
   - `Cloud Datastore User` (if using Firestore)
6. **Click "Continue" then "Done"**

## Step 3: Download Service Account Key

1. **Find your service account** in the list
2. **Click on the service account name**
3. **Go to "Keys" tab**
4. **Click "Add Key" > "Create new key"**
5. **Select "JSON" format**
6. **Click "Create"**
7. **The key file will download automatically**

## Step 4: Place Credentials in Your Project

1. **Rename the downloaded file** to `service-account-key.json`
2. **Place it in:** `backend/credentials/service-account-key.json`

Your project structure should look like:
```
backend/
├── credentials/
│   └── service-account-key.json  ← Place here
├── .env
└── ...
```

## Step 5: Update Your .env File

Edit `backend/.env` with your actual project details:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True

# Google Cloud Project - REPLACE WITH YOUR ACTUAL PROJECT ID
GOOGLE_CLOUD_PROJECT=your-actual-project-id
GOOGLE_APPLICATION_CREDENTIALS=credentials/service-account-key.json

# Vertex AI
VERTEX_LOCATION=us-central1
VERTEX_MODEL_ID=gemini-1.0-pro
VERTEX_MAX_OUTPUT_TOKENS=2048
VERTEX_TEMPERATURE=0.2

# Firebase (same as GCP project)
FIREBASE_PROJECT_ID=your-actual-project-id
FIREBASE_CREDENTIALS=credentials/service-account-key.json

# Firestore
FIRESTORE_DATABASE_ID=(default)
FIRESTORE_COLLECTION_PREFIX=

# Google Cloud Storage
GCS_BUCKET=your-actual-project-id-documents
GCS_REPORT_EXPIRY_SECONDS=3600

# Logging
LOG_LEVEL=INFO
ENABLE_VERTEX_LOGGING=True
```

## Step 6: Test Your Setup

Run the credential test script:

```bash
cd backend
python test_credentials.py
```

This will verify:
- ✅ Environment variables are set
- ✅ Credentials file exists and is valid
- ✅ GCP authentication works
- ✅ Vertex AI client can be initialized
- ✅ Basic text generation works
- ✅ Document analysis functions work

## Step 7: Test with Django

```bash
cd backend
python manage.py shell
```

```python
# Test Vertex AI client
from apps.ai_services.vertex_client import VertexAIClient
import asyncio

client = VertexAIClient()
print("Client initialized successfully!")

# Test document analysis
test_text = "This is a rental agreement between John and Jane."
result = asyncio.run(client.summarize_document(test_text))
print("Summary:", result['summary'])
```

## Troubleshooting

### "Application Default Credentials not found"
- Check that `service-account-key.json` is in the right location
- Verify the path in your `.env` file
- Make sure the JSON file is valid

### "Permission denied" errors
- Ensure your service account has the right roles:
  - `Vertex AI User`
  - `Storage Admin` (if using GCS)
  - `Cloud Datastore User` (if using Firestore)

### "Project not found" errors
- Double-check your project ID in the `.env` file
- Make sure the project exists in Google Cloud Console
- Verify APIs are enabled

### Import errors
```bash
pip install google-cloud-aiplatform
pip install google-auth
```

## Cost Considerations

- **Vertex AI:** Pay per token (input + output)
- **Typical costs:** $0.001-0.01 per request for testing
- **Free tier:** Google Cloud offers $300 credit for new accounts
- **Monitoring:** Check usage in Google Cloud Console

## Security Notes

- ✅ **Never commit** `service-account-key.json` to git
- ✅ **Share credentials** securely with team members
- ✅ **Rotate keys** periodically
- ✅ **Use least privilege** - only grant necessary permissions

## Next Steps

Once your credentials are working:

1. **Update your team** - share the `.env` file and service account key securely
2. **Remove mocks** - your code will now use real Vertex AI
3. **Test thoroughly** - try document upload and analysis
4. **Monitor usage** - keep an eye on costs in GCP Console

## Team Sharing

To share with your team:
1. **Share the `.env` file** (with your actual project ID)
2. **Share the `service-account-key.json` file** (securely)
3. **Each team member** places files in the same locations
4. **Everyone runs** `python test_credentials.py` to verify setup

That's it! You should now have real GCP credentials working in your project.