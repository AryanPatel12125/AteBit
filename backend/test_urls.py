"""
Test URL configuration for AteBit project.
Simplified URLs for testing without admin interface.
"""

from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    """Health check endpoint for testing"""
    return JsonResponse({
        'status': 'healthy',
        'message': 'Backend running - AteBit Legal Document Platform',
        'version': '1.0.0-test'
    })

def version_info(request):
    """Version information endpoint"""
    return JsonResponse({
        'version': '1.0.0-test',
        'api_version': 'v1',
        'platform': 'AteBit Legal Document AI Platform'
    })

urlpatterns = [
    # System endpoints
    path("api/health/", health_check, name="health_check"),
    path("api/version/", version_info, name="version_info"),
    
    # API v1 endpoints
    path("api/documents/", include("apps.documents.urls")),
]