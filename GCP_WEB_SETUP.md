# GCP Setup Using Web Interface (No CLI Required)

This guide shows how to set up GCP credentials using only the web browser - no command line tools needed.

## Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console:** https://console.cloud.google.com/
2. **Click "Select a project"** at the top
3. **Click "New Project"**
4. **Enter project details:**
   - Project name: `Legal AI Team Shared`
   - Project ID: `legal-ai-team-shared` (must be globally unique)
5. **Click "Create"**

## Step 2: Enable Required APIs

1. **Go to APIs & Services > Library:** https://console.cloud.google.com/apis/library
2. **Search and enable these APIs:**
   - **Vertex AI API** - Search "Vertex AI" → Click → Enable
   - **Cloud Storage API** - Search "Cloud Storage" → Click → Enable  
   - **Firestore API** - Search "Firestore" → Click → Enable
   - **Firebase Admin SDK** - Search "Firebase Admin" → Click → Enable

## Step 3: Create Service Account

1. **Go to IAM & Admin > Service Accounts:** https://console.cloud.google.com/iam-admin/serviceaccounts
2. **Click "Create Service Account"**
3. **Enter details:**
   - Service account name: `legal-ai-backend`
   - Service account ID: `legal-ai-backend` (auto-filled)
   - Description: `Shared backend service account for Legal AI`
4. **Click "Create and Continue"**

## Step 4: Grant Permissions to Service Account

1. **In the "Grant this service account access to project" section, add these roles:**
   - `Vertex AI User` - For AI model access
   - `Storage Admin` - For file upload/download
   - `Cloud Datastore User` - For Firestore access
   - `Firebase Admin` - For Firebase services

2. **Click "Continue"** then **"Done"**

## Step 5: Create and Download Service Account Key

1. **Find your service account** in the list
2. **Click on the service account name** (legal-ai-backend)
3. **Go to "Keys" tab**
4. **Click "Add Key" > "Create new key"**
5. **Select "JSON"** format
6. **Click "Create"**
7. **The key file will download automatically** - save it as `service-account-key.json`

## Step 6: Create Cloud Storage Bucket

1. **Go to Cloud Storage > Buckets:** https://console.cloud.google.com/storage/browser
2. **Click "Create Bucket"**
3. **Enter details:**
   - Bucket name: `legal-ai-team-shared-documents` (must be globally unique)
   - Location: `us-central1` (single region)
   - Storage class: `Standard`
   - Access control: `Uniform`
4. **Click "Create"**

## Step 7: Set Up Firestore Database

1. **Go to Firestore:** https://console.cloud.google.com/firestore
2. **Click "Create database"**
3. **Select "Production mode"**
4. **Choose location:** `us-central1`
5. **Click "Create"**

## Step 8: Distribute Credentials to Team

### Create the .env file with your actual project details:

```env
# Django Configuration
DJANGO_SECRET_KEY=your-team-shared-secret-key-here
DEBUG=True

# Google Cloud Project (REPLACE WITH YOUR ACTUAL PROJECT ID)
GOOGLE_CLOUD_PROJECT=legal-ai-team-shared
GOOGLE_APPLICATION_CREDENTIALS=credentials/service-account-key.json

# Vertex AI Configuration
VERTEX_LOCATION=us-central1
VERTEX_MODEL_ID=gemini-1.0-pro
VERTEX_MAX_OUTPUT_TOKENS=2048
VERTEX_TEMPERATURE=0.2

# Firebase Configuration (SAME AS GCP PROJECT)
FIREBASE_PROJECT_ID=legal-ai-team-shared
FIREBASE_CREDENTIALS=credentials/service-account-key.json

# Firestore Configuration
FIRESTORE_DATABASE_ID=(default)
FIRESTORE_COLLECTION_PREFIX=dev_

# Google Cloud Storage Configuration (REPLACE WITH YOUR ACTUAL BUCKET NAME)
GCS_BUCKET=legal-ai-team-shared-documents
GCS_REPORT_EXPIRY_SECONDS=3600

# Development Settings
LOG_LEVEL=INFO
ENABLE_VERTEX_LOGGING=True
```

### Share with team members:
1. **The `.env` file** (with your actual project ID and bucket name)
2. **The `service-account-key.json` file** (downloaded in Step 5)

## Step 9: Team Member Setup

Each team member should:

1. **Place files in correct locations:**
   ```
   backend/
   ├── credentials/
   │   └── service-account-key.json  ← Place here
   └── .env  ← Place here
   ```

2. **Test the setup:**
   ```cmd
   cd backend
   python manage.py shell
   ```
   ```python
   >>> import os
   >>> print("Project:", os.getenv('GOOGLE_CLOUD_PROJECT'))
   >>> print("Credentials exist:", os.path.exists(os.getenv('GOOGLE_APPLICATION_CREDENTIALS')))
   ```

## Verification Checklist

✅ **Project created** with unique ID  
✅ **APIs enabled** (Vertex AI, Cloud Storage, Firestore, Firebase)  
✅ **Service account created** with proper roles  
✅ **JSON key downloaded** and shared with team  
✅ **Storage bucket created** with appropriate name  
✅ **Firestore database** set up in production mode  
✅ **Team members** can access shared resources  

## Cost Management

- **Monitor usage** in the Google Cloud Console
- **Set up billing alerts** to avoid surprises
- **Use development prefixes** to organize test data
- **Clean up test documents** regularly

## Security Notes

- **Never commit** the service account key to git
- **Share credentials** through secure channels only
- **Rotate keys** if compromised
- **Monitor access** in the IAM logs