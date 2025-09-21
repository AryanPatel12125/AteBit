"""
Minimal Django settings for testing without admin interface.
"""
import os

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

# Minimal installed apps
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
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
}

# Time zone settings
USE_TZ = True
TIME_ZONE = 'UTC'

# URL configuration
ROOT_URLCONF = 'test_urls'

# Test-specific settings
TESTING = True

# Set environment variable to indicate we're in test mode
os.environ['TESTING'] = 'True'