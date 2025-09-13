"""
Django settings for AteBit Legal Document Platform.

Minimal hackathon boilerplate configuration.
CORS config, REST framework, Firebase placeholders included.
No actual AI/Firebase implementation yet - just infrastructure setup.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('DJANGO_SECRET_KEY', default="django-insecure-=x-oq&)yf#z&8&ssik)(pqq!@f=c3kj2@9#!ev7c@-1#u2!)oa")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # Third-party apps
    "rest_framework",
    "corsheaders",
    
    # Local Apps (Placeholder - TODO: Uncomment when apps are created)
    # "apps.documents",
    # "apps.ai_services",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "AteBit.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "AteBit.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # TODO: Add proper authentication
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS Settings for Frontend Development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Next.js development server
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# TODO: Firebase Configuration (Placeholder - not implemented yet)
# FIREBASE_CONFIG = {
#     'type': config('FIREBASE_TYPE', default=''),
#     'project_id': config('FIREBASE_PROJECT_ID', default=''),
#     'private_key_id': config('FIREBASE_PRIVATE_KEY_ID', default=''),
#     'private_key': config('FIREBASE_PRIVATE_KEY', default=''),
#     'client_email': config('FIREBASE_CLIENT_EMAIL', default=''),
#     'client_id': config('FIREBASE_CLIENT_ID', default=''),
#     'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
#     'token_uri': 'https://oauth2.googleapis.com/token',
# }

# TODO: Google Cloud AI Configuration (Placeholder - not implemented yet)  
# GOOGLE_CLOUD_PROJECT = config('GOOGLE_CLOUD_PROJECT', default='')
# GOOGLE_APPLICATION_CREDENTIALS = config('GOOGLE_APPLICATION_CREDENTIALS', default='')

# TODO: AI Services Configuration (Placeholder - not implemented yet)
# OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
# LANGCHAIN_API_KEY = config('LANGCHAIN_API_KEY', default='')
