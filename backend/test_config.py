#!/usr/bin/env python
"""
Quick test script to validate Django configuration.
Run this to check if settings are valid before Docker build.
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AteBit.dev_settings')

try:
    # Setup Django
    django.setup()
    
    print("✅ Django configuration is valid!")
    print(f"📋 Settings module: {settings.SETTINGS_MODULE}")
    print(f"🐛 Debug mode: {settings.DEBUG}")
    print(f"🗄️  Database: {settings.DATABASES['default']['ENGINE']}")
    print(f"📝 Logging handlers: {list(settings.LOGGING['handlers'].keys())}")
    
    # Test logging configuration
    import logging
    logger = logging.getLogger('apps.documents')
    logger.info("Test log message - configuration is working!")
    
    print("🎉 All checks passed!")
    
except Exception as e:
    print(f"❌ Configuration error: {e}")
    sys.exit(1)