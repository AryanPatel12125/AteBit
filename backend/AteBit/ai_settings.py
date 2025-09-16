"""
Custom settings for AteBit Legal Document Platform.
Contains configurations for Google Cloud, Vertex AI, Firebase, and GCS.
"""
import os
from typing import Dict, Any
from decouple import config

# Google Cloud Project Settings
GOOGLE_CLOUD_PROJECT = config('GOOGLE_CLOUD_PROJECT', default='')
GOOGLE_APPLICATION_CREDENTIALS = config('GOOGLE_APPLICATION_CREDENTIALS', 
                                     default=os.getenv('GOOGLE_APPLICATION_CREDENTIALS', ''))

# Vertex AI Settings
VERTEX_SETTINGS = {
    'location': config('VERTEX_LOCATION', default='us-central1'),
    'model_id': config('VERTEX_MODEL_ID', default='gemini-1.0-pro'),
    'max_output_tokens': config('VERTEX_MAX_OUTPUT_TOKENS', default=1024, cast=int),
    'temperature': config('VERTEX_TEMPERATURE', default=0.2, cast=float),
    'safety_settings': {
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_HIGH',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_HIGH',
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_HIGH',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_HIGH',
    }
}

# Firebase Settings
FIREBASE_SETTINGS = {
    'project_id': config('FIREBASE_PROJECT_ID', default=''),
    'credentials_path': config('FIREBASE_CREDENTIALS', default=''),
}

# Google Cloud Storage Settings
GCS_SETTINGS = {
    'bucket': config('GCS_BUCKET', default=''),
    'report_expiry_seconds': config('GCS_REPORT_EXPIRY_SECONDS', default=3600, cast=int),
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