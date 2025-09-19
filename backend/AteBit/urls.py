"""
URL configuration for AteBit project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    """Health check endpoint for development"""
    return JsonResponse({
        'status': 'healthy',
        'message': 'Backend running - AteBit Legal Document Platform',
        'version': '1.0.0-dev'
    })

def version_info(request):
    """Version information endpoint"""
    return JsonResponse({
        'version': '1.0.0-dev',
        'api_version': 'v1',
        'platform': 'AteBit Legal Document AI Platform'
    })

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # System endpoints
    path("api/health/", health_check, name="health_check"),
    path("api/version/", version_info, name="version_info"),
    
    # API v1 endpoints
    path("api/documents/", include("apps.documents.urls")),
    
    # Future API endpoints (when implemented)
    # path("api/ai-services/", include("apps.ai_services.urls")),
]
