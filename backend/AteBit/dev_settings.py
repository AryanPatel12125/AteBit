"""
Development settings for Docker environment.
Overrides production settings for local development.
"""

from .settings import *

# Override for development
DEBUG = True

# Simplified logging for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.documents': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.ai_services': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

# Disable file logging in development
# Override any file handlers that might cause issues in Docker

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Disable CSRF for development API testing
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
]