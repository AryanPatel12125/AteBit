"""
Django settings for testing the legal document AI backend.
This configuration avoids Google Cloud authentication issues during testing.
"""
import os
from unittest.mock import Mock

# Basic Django settings
DEBUG = True
SECRET_KEY = 'test-secret-key-for-legal-document-ai-backend'

# Database configuration for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Installed apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'rest_framework',
    'apps.documents',
    'apps.authz',
    'apps.ai_services',
]

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.authz.firebase_auth.FirebaseAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

# Mock Google Cloud settings to avoid authentication
GOOGLE_CLOUD_PROJECT = 'test-project'
GCS_BUCKET_NAME = 'test-bucket'

# Mock Firebase settings
FIREBASE_CONFIG = {
    'project_id': 'test-project',
    'credentials_path': '/fake/path/to/credentials.json'
}

# Mock Vertex AI settings
VERTEX_SETTINGS = {
    'location': 'us-central1',
    'model_id': 'text-bison@001',
    'max_output_tokens': 1024,
    'temperature': 0.2,
    'safety_settings': {}
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'apps.documents': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Time zone settings
USE_TZ = True
TIME_ZONE = 'UTC'

# URL configuration
ROOT_URLCONF = 'AteBit.urls'

# Test-specific settings
TESTING = True

# Set environment variable to indicate we're in test mode
import os
os.environ['TESTING'] = 'True'