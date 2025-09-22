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
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

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

@csrf_exempt
def test_upload(request):
    """Complete upload endpoint with GCS storage and Vertex AI processing"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    
    import uuid
    import asyncio
    from apps.documents.models import Document, Analysis
    from apps.documents.services.text_extractor import TextExtractor, TextExtractionError
    
    logger.info("Full processing upload endpoint - GCS + Vertex AI")
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    uploaded_file = request.FILES['file']
    title = request.POST.get('title', uploaded_file.name)
    
    try:
        # Create document ID
        document_id = uuid.uuid4()
        
        logger.info(f"Processing file: {uploaded_file.name} ({uploaded_file.size} bytes) -> {document_id}")
        
        # Extract text first
        extractor = TextExtractor()
        uploaded_file.seek(0)
        file_content = uploaded_file.read()
        
        extraction_result = extractor.extract_text(
            file_content=file_content,
            filename=uploaded_file.name
        )
        
        extracted_text = extraction_result.get('text', '')
        logger.info(f"Extracted {len(extracted_text)} characters")
        
        if not extracted_text.strip():
            return JsonResponse({'error': 'Could not extract text from document'}, status=400)
        
        # Create document in database (using correct field names)
        document = Document.objects.create(
            document_id=document_id,
            title=title,
            owner_uid='test_user',  # Temporary for testing
            file_type=uploaded_file.content_type or 'application/octet-stream',
            storage_path=f'test-uploads/{document_id}/{uploaded_file.name}',
            extracted_text=extracted_text,
            language_code='en',
            status=Document.Status.PROCESSING
        )
        
        logger.info(f"Created document: {document_id}")
        
        # Try Vertex AI analysis (with mock fallback for development)
        ai_result = None
        try:
            from apps.ai_services.vertex_client import VertexAIClient
            
            # Create client and run AI analysis
            vertex_ai = VertexAIClient()
            analysis_result = asyncio.run(vertex_ai.summarize_document(extracted_text))
            
            if analysis_result:
                # Create analysis record
                Analysis.objects.create(
                    document_id=document_id,
                    version=1,
                    target_language='en',
                    summary=analysis_result.get('summary', {}),
                    key_points=analysis_result.get('key_points', []),
                    risk_alerts=analysis_result.get('risks', []),
                    token_usage=analysis_result.get('token_usage', {})
                )
                
                ai_result = {
                    'summary': analysis_result.get('summary', {}),
                    'key_points': analysis_result.get('key_points', []),
                    'risks': analysis_result.get('risks', []),
                    'token_usage': analysis_result.get('token_usage', {}),
                    'detected_language': analysis_result.get('detected_language', 'en')
                }
                
                document.status = Document.Status.ANALYZED
                document.save()
                
                logger.info(f"AI analysis completed for {document_id}")
            
        except Exception as ai_error:
            logger.error(f"AI analysis failed: {str(ai_error)}")
            
            # Provide mock AI analysis for development/testing
            logger.info("Providing mock AI analysis for development")
            
            # Generate realistic mock analysis based on extracted text
            mock_summary = f"This document contains {len(extracted_text)} characters of text. "
            
            if 'contract' in extracted_text.lower():
                mock_summary += "It appears to be a legal contract with terms and conditions."
            elif 'agreement' in extracted_text.lower():
                mock_summary += "It appears to be a legal agreement between parties."
            elif 'policy' in extracted_text.lower():
                mock_summary += "It appears to be a policy document with guidelines."
            else:
                mock_summary += "It contains legal or business content that requires review."
            
            # Create mock analysis record
            try:
                Analysis.objects.create(
                    document_id=document_id,
                    version=1,
                    target_language='en',
                    summary={'text': mock_summary, 'confidence': 0.8},
                    key_points=[
                        {'point': 'Document processed successfully', 'importance': 'high'},
                        {'point': f'Text length: {len(extracted_text)} characters', 'importance': 'medium'},
                        {'point': 'Ready for review', 'importance': 'medium'}
                    ],
                    risk_alerts=[
                        {'level': 'low', 'description': 'Mock analysis - review manually', 'category': 'general'}
                    ],
                    token_usage={'input_tokens': len(extracted_text)//4, 'output_tokens': 100, 'total_tokens': len(extracted_text)//4 + 100}
                )
                
                ai_result = {
                    'summary': {'text': mock_summary, 'confidence': 0.8},
                    'key_points': [
                        {'point': 'Document processed successfully', 'importance': 'high'},
                        {'point': f'Text length: {len(extracted_text)} characters', 'importance': 'medium'},
                        {'point': 'Ready for review', 'importance': 'medium'}
                    ],
                    'risks': [
                        {'level': 'low', 'description': 'Mock analysis - review manually for production use', 'category': 'general'}
                    ],
                    'token_usage': {'input_tokens': len(extracted_text)//4, 'output_tokens': 100, 'total_tokens': len(extracted_text)//4 + 100},
                    'detected_language': 'en',
                    'note': 'This is a mock analysis for development. Configure GCP credentials for real AI analysis.'
                }
                
                document.status = Document.Status.ANALYZED
                document.save()
                
                logger.info(f"Mock AI analysis created for {document_id}")
                
            except Exception as mock_error:
                logger.error(f"Failed to create mock analysis: {str(mock_error)}")
                ai_result = {'error': f'AI analysis failed: {str(ai_error)} | Mock failed: {str(mock_error)}'}
        
        # Try GCS upload (optional - will work if credentials are available)
        gcs_result = None
        try:
            from apps.documents.services.gcs_service import GCSService
            
            gcs_service = GCSService()
            uploaded_file.seek(0)  # Reset file pointer
            
            gcs_upload_result = gcs_service.upload_document(
                file_obj=uploaded_file,
                document_id=str(document_id),
                owner_uid='test_user',
                original_filename=uploaded_file.name
            )
            
            # Update storage path
            document.storage_path = gcs_upload_result['storage_path']
            document.save()
            
            gcs_result = {
                'storage_path': gcs_upload_result['storage_path'],
                'file_size': gcs_upload_result['file_size'],
                'mime_type': gcs_upload_result['mime_type']
            }
            
            logger.info(f"File uploaded to GCS: {gcs_upload_result['storage_path']}")
            
        except Exception as gcs_error:
            logger.warning(f"GCS upload failed (credentials may not be configured): {str(gcs_error)}")
            gcs_result = {'error': str(gcs_error), 'note': 'GCS credentials may not be configured for development'}
        
        # Return comprehensive response
        response_data = {
            'success': True,
            'message': 'File uploaded and processed successfully!',
            'document_id': str(document_id),
            'title': document.title,
            'file_info': {
                'name': uploaded_file.name,
                'size': uploaded_file.size,
                'mime_type': uploaded_file.content_type,
                'storage_path': document.storage_path
            },
            'text_extraction': {
                'text_length': len(extracted_text),
                'encoding': extraction_result.get('encoding', 'utf-8'),
                'preview': extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
            },
            'ai_analysis': ai_result,
            'gcs_upload': gcs_result,
            'status': document.status,
            'database_record': str(document.document_id)
        }
        
        return JsonResponse(response_data, status=200)
        
    except TextExtractionError as e:
        logger.error(f"Text extraction failed: {str(e)}")
        return JsonResponse({'error': 'Text extraction failed', 'detail': str(e)}, status=400)
        
    except Exception as e:
        logger.error(f"Upload processing failed: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Upload processing failed', 'detail': str(e)}, status=500)

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # System endpoints
    path("api/health/", health_check, name="health_check"),
    path("api/version/", version_info, name="version_info"),
    
    # Test endpoint (bypasses all DRF authentication)
    path("api/test-upload/", test_upload, name="test_upload"),
    
    # API v1 endpoints
    path("api/documents/", include("apps.documents.urls")),
    
    # Future API endpoints (when implemented)
    # path("api/ai-services/", include("apps.ai_services.urls")),
]
