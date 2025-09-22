"""
URL configuration for documents app.

Provides URL patterns for all document management and AI analysis endpoints
with proper parameter validation and API versioning.

Requirements: All endpoint requirements
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSet-based endpoints
router = DefaultRouter()
router.register(r'', views.DocumentViewSet, basename='document')

# URL patterns for documents app
urlpatterns = [
    # Document CRUD operations (via ViewSet)
    # POST /api/documents/ - Create document metadata
    # GET /api/documents/ - List user's documents  
    # GET /api/documents/{id}/ - Retrieve document details
    # DELETE /api/documents/{id}/ - Delete document
    path('', include(router.urls)),
    
    # Document file operations
    # POST /api/documents/{id}/upload/ - Upload file content
    path('<uuid:document_id>/upload/', 
         views.DocumentUploadView.as_view(), 
         name='document-upload'),
    
    # Document AI analysis
    # POST /api/documents/{id}/analyze/ - Trigger AI analysis
    path('<uuid:document_id>/analyze/', 
         views.DocumentAnalyzeView.as_view(), 
         name='document-analyze'),
    
    # Document file download
    # GET /api/documents/{id}/download/ - Get signed download URL
    path('<uuid:document_id>/download/', 
         views.DocumentDownloadView.as_view(), 
         name='document-download'),
    
    # Analysis history endpoints
    # GET /api/documents/{id}/analysis/ - Get latest analysis
    path('<uuid:document_id>/analysis/', 
         views.DocumentAnalysisHistoryView.as_view(), 
         name='document-analysis-latest'),
    
    # GET /api/documents/{id}/analysis/{version}/ - Get specific analysis version
    path('<uuid:document_id>/analysis/<int:version>/', 
         views.DocumentAnalysisHistoryView.as_view(), 
         name='document-analysis-version'),
    
    # Simple upload endpoint for frontend testing
    path('simple-upload/', 
         views.SimpleDocumentUploadView.as_view(), 
         name='simple-upload'),
    
    # Test upload endpoint (plain Django - no DRF authentication)
    path('simple-upload-test/', 
         views.simple_upload_test, 
         name='simple-upload-test'),
]

# URL pattern names for reference:
# - document-list (GET /api/documents/)
# - document-detail (GET /api/documents/{id}/)
# - document-create (POST /api/documents/)
# - document-delete (DELETE /api/documents/{id}/)
# - document-upload (POST /api/documents/{id}/upload/)
# - document-analyze (POST /api/documents/{id}/analyze/)
# - document-download (GET /api/documents/{id}/download/)
# - document-analysis-latest (GET /api/documents/{id}/analysis/)
# - document-analysis-version (GET /api/documents/{id}/analysis/{version}/)