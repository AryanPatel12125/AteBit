"""
Custom settings for AteBit Legal Document Platform.
Contains configurations for Google Cloud, Vertex AI, Firebase, and GCS.
"""
import os
from typing import Dict, Any
from decouple import config

# FORCE LOAD HARDCODED GCP SETTINGS - INSECURE BUT WORKS
print("🔥 FORCE LOADING GCP CREDENTIALS - INSECURE MODE")

# Google Cloud Project Settings - HARDCODED
GOOGLE_CLOUD_PROJECT = 'atebit'
GOOGLE_APPLICATION_CREDENTIALS = 'credentials/service-account-key.json'

# Force set environment variables
os.environ['GOOGLE_CLOUD_PROJECT'] = 'atebit'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials/service-account-key.json')

print(f"🚀 FORCED GCP PROJECT: {GOOGLE_CLOUD_PROJECT}")
print(f"🔑 FORCED CREDENTIALS PATH: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
print(f"📁 CREDENTIALS EXIST: {os.path.exists(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])}")

# Validate credentials on startup
credentials_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
if os.path.exists(credentials_path):
    print("✅ CREDENTIALS FILE FOUND - GCP INTEGRATION ACTIVE")
else:
    print(f"❌ CREDENTIAL FILE NOT FOUND AT: {credentials_path}")

# Vertex AI Settings - HARDCODED
VERTEX_SETTINGS = {
    'location': 'us-central1',
    'model_id': 'gemini-1.5-pro',
    'max_output_tokens': 2048,
    'temperature': 0.2,
    'safety_settings': {
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_HIGH',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_HIGH',
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_HIGH',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_HIGH',
    }
}

# Firebase Settings - HARDCODED
FIREBASE_SETTINGS = {
    'project_id': 'atebit',
    'credentials_path': 'credentials/service-account-key.json',
}

# Google Cloud Storage Settings - HARDCODED
GCS_SETTINGS = {
    'bucket': 'atebit-documents',
    'report_expiry_seconds': 3600,
}

# Default prompt settings
DEFAULT_PROMPT_SETTINGS: Dict[str, Any] = {
    'summarize': {
        'system_prompt': """You are a helpful assistant tasked with summarizing legal documents 
        in extremely simple language suitable for a 12-year-old reader. Focus on clarity and 
        brevity. Always maintain factual accuracy while simplifying complex terms.""",
        'max_tokens': 512,
    },
    'key_points': {
        'system_prompt': """Extract 5-10 key points from the legal document. For each point:
        1. Use simple language
        2. Provide a brief explanation
        3. Include relevant text spans if available
        4. Focus on material terms and obligations""",
        'max_tokens': 768,
    },
    'risk_compliance': {
        'system_prompt': """Analyze the document for potential legal risks and compliance issues.
        For each issue found:
        1. Indicate severity (HIGH, MEDIUM, LOW)
        2. Explain the concern in simple terms
        3. Suggest potential remediation
        4. Reference specific clauses where applicable""",
        'max_tokens': 1024,
    }
}

# Logging configuration for AI operations
AI_LOGGING = {
    'enabled': config('ENABLE_VERTEX_LOGGING', default=True, cast=bool),
    'log_level': config('LOG_LEVEL', default='INFO'),
    # Never log full document text in production
    'log_prompts': False if not config('DEBUG', default=False, cast=bool) else True,
}