# Firebase Configuration Setup Guide

This guide provides step-by-step instructions for setting up Firebase services required by the AteBit Legal Document AI Platform.

## Overview

The platform uses the following Firebase and Google Cloud services:

- **Firebase Authentication**: User authentication and authorization
- **Firebase Firestore**: Document metadata and analysis results storage
- **Google Cloud Storage**: Original document file storage
- **Vertex AI**: AI-powered document analysis
- **Firebase Admin SDK**: Backend service authentication

## Prerequisites

1. **Google Account**: You need a Google account to access Google Cloud Console
2. **Google Cloud Project**: Create or use an existing Google Cloud project
3. **Billing Account**: Some services require a billing account (free tier available)

---

## Step 1: Create Google Cloud Project

### 1.1 Access Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Accept the terms of service if prompted

### 1.2 Create New Project

1. Click on the project dropdown at the top of the page
2. Click "New Project"
3. Enter project details:
   - **Project name**: `atebit-legal-ai` (or your preferred name)
   - **Organization**: Select your organization (if applicable)
   - **Location**: Choose appropriate location
4. Click "Create"
5. Wait for project creation to complete
6. Select the new project from the dropdown

### 1.3 Note Your Project ID

```bash
# Your project ID will be something like:
PROJECT_ID="atebit-legal-ai-123456"

# You'll need this for configuration
echo "Project ID: $PROJECT_ID"
```

---

## Step 2: Enable Required APIs

### 2.1 Enable APIs via Console

1. Go to **APIs & Services > Library**
2. Search for and enable the following APIs:
   - **Firebase Admin SDK API**
   - **Cloud Firestore API**
   - **Cloud Storage API**
   - **Vertex AI API**
   - **Identity and Access Management (IAM) API**

### 2.2 Enable APIs via Command Line

```bash
# Install Google Cloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Set your project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable firebase.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable iam.googleapis.com

# Verify enabled services
gcloud services list --enabled
```

---

## Step 3: Set Up Firebase Project

### 3.1 Access Firebase Console

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Select your existing Google Cloud project
4. Continue through the setup wizard:
   - **Google Analytics**: Enable if desired (optional for this project)
   - **Analytics account**: Select or create if enabling Analytics

### 3.2 Configure Firebase Authentication

1. In Firebase Console, go to **Authentication**
2. Click "Get started"
3. Go to **Sign-in method** tab
4. Enable your preferred authentication providers:

#### Email/Password Authentication
```bash
# Enable Email/Password provider
# 1. Click on "Email/Password"
# 2. Enable "Email/Password"
# 3. Optionally enable "Email link (passwordless sign-in)"
# 4. Click "Save"
```

#### Google Authentication (Recommended)
```bash
# Enable Google provider
# 1. Click on "Google"
# 2. Enable Google sign-in
# 3. Enter project support email
# 4. Click "Save"
```

#### Other Providers (Optional)
- Facebook
- Twitter
- GitHub
- Microsoft
- Apple

### 3.3 Configure Firestore Database

1. In Firebase Console, go to **Firestore Database**
2. Click "Create database"
3. Choose security rules:
   - **Start in test mode** (for development)
   - **Start in production mode** (for production)
4. Select database location (choose closest to your users)
5. Click "Done"

#### Firestore Security Rules

For development, use test mode rules:

```javascript
// Firestore Security Rules (Development)
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read/write access to all documents for authenticated users
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

For production, use more restrictive rules:

```javascript
// Firestore Security Rules (Production)
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Documents collection - users can only access their own documents
    match /documents/{documentId} {
      allow read, write: if request.auth != null 
        && request.auth.uid == resource.data.owner_uid;
      allow create: if request.auth != null 
        && request.auth.uid == request.resource.data.owner_uid;
    }
    
    // Analysis subcollections
    match /documents/{documentId}/analyses/{analysisId} {
      allow read, write: if request.auth != null 
        && request.auth.uid == get(/databases/$(database)/documents/documents/$(documentId)).data.owner_uid;
    }
    
    // History subcollections
    match /documents/{documentId}/history/{historyId} {
      allow read: if request.auth != null 
        && request.auth.uid == get(/databases/$(database)/documents/documents/$(documentId)).data.owner_uid;
    }
  }
}
```

---

## Step 4: Set Up Google Cloud Storage

### 4.1 Create Storage Bucket

```bash
# Set variables
PROJECT_ID="your-project-id"
BUCKET_NAME="${PROJECT_ID}-documents"
REGION="us-central1"  # Choose appropriate region

# Create bucket
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME

# Set bucket permissions (for development)
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME

# For production, use more restrictive permissions
gsutil iam ch serviceAccount:firebase-adminsdk-xxxxx@${PROJECT_ID}.iam.gserviceaccount.com:objectAdmin gs://$BUCKET_NAME
```

### 4.2 Configure CORS (if needed for direct uploads)

```bash
# Create CORS configuration file
cat > cors.json << 'EOF'
[
  {
    "origin": ["http://localhost:3000", "https://yourdomain.com"],
    "method": ["GET", "POST", "PUT", "DELETE"],
    "responseHeader": ["Content-Type", "Authorization"],
    "maxAgeSeconds": 3600
  }
]
EOF

# Apply CORS configuration
gsutil cors set cors.json gs://$BUCKET_NAME

# Verify CORS configuration
gsutil cors get gs://$BUCKET_NAME
```

---

## Step 5: Create Service Account

### 5.1 Create Service Account

```bash
# Set variables
PROJECT_ID="your-project-id"
SERVICE_ACCOUNT_NAME="atebit-backend-service"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Create service account
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
  --display-name="AteBit Backend Service Account" \
  --description="Service account for AteBit Legal AI Platform backend"

# Verify creation
gcloud iam service-accounts list
```

### 5.2 Assign Required Roles

```bash
# Assign necessary roles to the service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/firebase.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/aiplatform.user"

# Verify role assignments
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:$SERVICE_ACCOUNT_EMAIL"
```

### 5.3 Generate Service Account Key

```bash
# Create and download service account key
gcloud iam service-accounts keys create credentials.json \
  --iam-account=$SERVICE_ACCOUNT_EMAIL

# Secure the key file
chmod 600 credentials.json

# Move to appropriate location
mkdir -p backend/credentials
mv credentials.json backend/credentials/

echo "Service account key saved to: backend/credentials/credentials.json"
```

---

## Step 6: Configure Vertex AI

### 6.1 Enable Vertex AI

```bash
# Enable Vertex AI API (if not already done)
gcloud services enable aiplatform.googleapis.com

# Set default region for Vertex AI
gcloud config set ai/region us-central1

# Verify Vertex AI is available
gcloud ai models list --region=us-central1
```

### 6.2 Test Vertex AI Access

```python
# Test script: test_vertex_ai.py
import os
from google.cloud import aiplatform

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'backend/credentials/credentials.json'

# Initialize Vertex AI
aiplatform.init(
    project='your-project-id',
    location='us-central1'
)

# Test model access
try:
    # This will list available models
    models = aiplatform.Model.list()
    print(f"Vertex AI is accessible. Found {len(models)} models.")
except Exception as e:
    print(f"Error accessing Vertex AI: {e}")
```

---

## Step 7: Backend Configuration

### 7.1 Environment Variables

Create a `.env` file in the backend directory:

```bash
# backend/.env

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=credentials/credentials.json
GCS_BUCKET_NAME=your-project-id-documents

# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id

# Vertex AI Configuration
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL_ID=gemini-1.0-pro

# Django Configuration
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (for local development)
DATABASE_URL=sqlite:///db.sqlite3
```

### 7.2 Django Settings

Update `backend/AteBit/settings.py`:

```python
# settings.py additions

import os
from pathlib import Path

# Firebase Configuration
FIREBASE_CONFIG = {
    'project_id': os.getenv('FIREBASE_PROJECT_ID'),
    'credentials_path': os.path.join(BASE_DIR, os.getenv('GOOGLE_APPLICATION_CREDENTIALS', ''))
}

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')

# Vertex AI Configuration
VERTEX_SETTINGS = {
    'location': os.getenv('VERTEX_AI_LOCATION', 'us-central1'),
    'model_id': os.getenv('VERTEX_AI_MODEL_ID', 'gemini-1.0-pro'),
    'max_output_tokens': 2048,
    'temperature': 0.3,
    'safety_settings': {}
}
```

---

## Step 8: Frontend Configuration

### 8.1 Firebase Web App Configuration

1. In Firebase Console, go to **Project Settings**
2. Scroll down to "Your apps"
3. Click "Add app" and select Web (</>) icon
4. Register your app:
   - **App nickname**: `atebit-frontend`
   - **Firebase Hosting**: Enable if desired
5. Copy the Firebase configuration

### 8.2 Frontend Environment Variables

Create `frontend/.env.local`:

```bash
# frontend/.env.local

# Firebase Configuration
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abcdef123456

# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

### 8.3 Firebase SDK Configuration

Update `frontend/lib/firebase.js`:

```javascript
// frontend/lib/firebase.js
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase services
export const auth = getAuth(app);
export const db = getFirestore(app);

export default app;
```

---

## Step 9: Testing Configuration

### 9.1 Test Backend Services

```bash
# Test script: test_services.py
import os
import asyncio
from google.cloud import firestore
from google.cloud import storage
from apps.ai_services.vertex_client import VertexAIClient

async def test_services():
    print("Testing Firebase services...")
    
    # Test Firestore
    try:
        db = firestore.Client()
        collections = list(db.collections())
        print(f"✓ Firestore connected. Collections: {len(collections)}")
    except Exception as e:
        print(f"✗ Firestore error: {e}")
    
    # Test Cloud Storage
    try:
        client = storage.Client()
        bucket_name = os.getenv('GCS_BUCKET_NAME')
        bucket = client.bucket(bucket_name)
        print(f"✓ Cloud Storage connected. Bucket: {bucket.name}")
    except Exception as e:
        print(f"✗ Cloud Storage error: {e}")
    
    # Test Vertex AI
    try:
        vertex_client = VertexAIClient()
        result = await vertex_client.detect_language("This is a test.")
        print(f"✓ Vertex AI connected. Detected language: {result}")
    except Exception as e:
        print(f"✗ Vertex AI error: {e}")

if __name__ == "__main__":
    asyncio.run(test_services())
```

### 9.2 Test Frontend Authentication

```javascript
// Test authentication in browser console
import { signInWithEmailAndPassword } from 'firebase/auth';
import { auth } from './lib/firebase';

// Test sign in
signInWithEmailAndPassword(auth, 'test@example.com', 'password')
  .then((userCredential) => {
    console.log('✓ Authentication successful:', userCredential.user);
    return userCredential.user.getIdToken();
  })
  .then((token) => {
    console.log('✓ ID Token obtained:', token.substring(0, 50) + '...');
  })
  .catch((error) => {
    console.error('✗ Authentication error:', error);
  });
```

---

## Step 10: Security Configuration

### 10.1 Production Security Rules

Update Firestore security rules for production:

```javascript
// Production Firestore Rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Helper functions
    function isAuthenticated() {
      return request.auth != null;
    }
    
    function isOwner(resource) {
      return request.auth.uid == resource.data.owner_uid;
    }
    
    function isOwnerCreate() {
      return request.auth.uid == request.resource.data.owner_uid;
    }
    
    // Documents collection
    match /documents/{documentId} {
      allow read, update, delete: if isAuthenticated() && isOwner(resource);
      allow create: if isAuthenticated() && isOwnerCreate();
    }
    
    // Analysis subcollections
    match /documents/{documentId}/analyses/{analysisId} {
      allow read, write: if isAuthenticated() && 
        isOwner(get(/databases/$(database)/documents/documents/$(documentId)));
    }
    
    // History subcollections (read-only for users)
    match /documents/{documentId}/history/{historyId} {
      allow read: if isAuthenticated() && 
        isOwner(get(/databases/$(database)/documents/documents/$(documentId)));
    }
  }
}
```

### 10.2 Storage Security Rules

```javascript
// Cloud Storage Security Rules
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Documents path: documents/{userId}/{documentId}/{filename}
    match /documents/{userId}/{documentId}/{filename} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

### 10.3 Environment Security

```bash
# Secure credential files
chmod 600 backend/credentials/credentials.json
chmod 600 backend/.env
chmod 600 frontend/.env.local

# Add to .gitignore
echo "credentials/" >> backend/.gitignore
echo ".env" >> backend/.gitignore
echo ".env.local" >> frontend/.gitignore
```

---

## Troubleshooting

### Common Issues

#### 1. Authentication Errors

```bash
# Error: "Could not load the default credentials"
# Solution: Set GOOGLE_APPLICATION_CREDENTIALS
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"

# Error: "Permission denied"
# Solution: Check service account roles
gcloud projects get-iam-policy $PROJECT_ID
```

#### 2. Firestore Connection Issues

```bash
# Error: "Firestore client not initialized"
# Solution: Check project ID and credentials
gcloud config get-value project
gcloud auth application-default print-access-token
```

#### 3. Storage Bucket Issues

```bash
# Error: "Bucket does not exist"
# Solution: Create bucket or check name
gsutil ls -p $PROJECT_ID
gsutil mb gs://$BUCKET_NAME
```

#### 4. Vertex AI Issues

```bash
# Error: "Vertex AI API not enabled"
# Solution: Enable the API
gcloud services enable aiplatform.googleapis.com

# Error: "Model not found"
# Solution: Check available models
gcloud ai models list --region=us-central1
```

### Debugging Commands

```bash
# Check project configuration
gcloud config list

# Test service account
gcloud auth activate-service-account --key-file=credentials.json
gcloud auth list

# Test API access
gcloud services list --enabled

# Check IAM permissions
gcloud projects get-iam-policy $PROJECT_ID

# Test Firestore access
gcloud firestore databases list

# Test Storage access
gsutil ls -p $PROJECT_ID
```

---

## Production Deployment Checklist

- [ ] Enable production Firestore security rules
- [ ] Enable production Storage security rules
- [ ] Set up proper IAM roles and permissions
- [ ] Configure CORS for production domains
- [ ] Set up monitoring and logging
- [ ] Configure backup and disaster recovery
- [ ] Set up billing alerts
- [ ] Enable audit logging
- [ ] Configure VPC and network security
- [ ] Set up SSL/TLS certificates
- [ ] Configure CDN for static assets
- [ ] Set up error reporting and monitoring

---

*Last updated: January 2024*
*For AteBit Legal Document AI Platform*