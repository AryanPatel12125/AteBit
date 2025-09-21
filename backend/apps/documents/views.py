"""
Document API views for legal document management and AI analysis.
"""
import logging
import uuid
from typing import Dict, Any, Optional
from django.http import Http404
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.authz.firebase_auth import FirebaseAuthentication
from .models import Document, Analysis, History
from .permissions import IsDocumentOwner
from .serializers import (
    DocumentSerializer,
    DocumentListSerializer,
    DocumentUploadSerializer,
    AnalysisRequestSerializer,
    AnalysisResultSerializer,
    DocumentAnalysisSerializer
)
from .services import firestore_service, gcs_service, vertex_client
from .services.firestore_service import FirestoreError
from .services.gcs_service import GCSError
from .services.text_extractor import TextExtractor, TextExtractionError
from .logging_utils import log_api_request, documents_logger, log_document_operation
from .exceptions import (
    DocumentNotFoundError,
    DocumentAccessDeniedError,
    VertexAIError,
    GCSError as DocumentGCSError,
    FirestoreError as DocumentFirestoreError,
    FileProcessingError
)

logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Document CRUD operations with Firestore integration.
    
    Provides:
    - POST /api/documents/ - Create document metadata (accepts document_id from frontend)
    - GET /api/documents/ - List user's documents
    - GET /api/documents/{id}/ - Retrieve document details
    - DELETE /api/documents/{id}/ - Delete document
    
    Requirements: 1.1, 7.3, 7.4
    """
    
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsDocumentOwner]
    
    def get_queryset(self):
        """Return documents scoped to the authenticated user."""
        if not hasattr(self.request, 'user_uid'):
            return Document.objects.none()
        
        # For now, we'll use Django ORM but sync with Firestore
        return Document.objects.filter(owner_uid=self.request.user_uid)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DocumentListSerializer
        return DocumentSerializer
    
    def get_object(self):
        """Get document by document_id with owner validation."""
        document_id = self.kwargs.get('pk')
        
        if not document_id:
            raise Http404("Document ID not provided")
        
        try:
            # Convert string to UUID if needed
            if isinstance(document_id, str):
                document_id = uuid.UUID(document_id)
        except ValueError:
            raise Http404("Invalid document ID format")
        
        try:
            # First check Firestore for authoritative data
            firestore_doc = firestore_service.get_document(
                str(document_id), 
                self.request.user_uid
            )
            
            if not firestore_doc:
                raise Http404("Document not found")
            
            # Get or create Django model instance for ORM compatibility
            document, created = Document.objects.get_or_create(
                document_id=document_id,
                defaults={
                    'title': firestore_doc.get('title', ''),
                    'owner_uid': firestore_doc.get('owner_uid', ''),
                    'file_type': firestore_doc.get('file_type', ''),
                    'storage_path': firestore_doc.get('storage_path', ''),
                    'extracted_text': firestore_doc.get('extracted_text'),
                    'language_code': firestore_doc.get('language_code'),
                    'status': firestore_doc.get('status', 'PENDING'),
                }
            )
            
            # Update Django model with latest Firestore data if not created
            if not created:
                for field, value in firestore_doc.items():
                    if hasattr(document, field) and field not in ['document_id', 'created_at']:
                        setattr(document, field, value)
                document.save()
            
            return document
            
        except FirestoreError as e:
            logger.error(f"Firestore error retrieving document {document_id}: {str(e)}")
            raise Http404("Document not found")
    
    @log_api_request
    def create(self, request: Request) -> Response:
        """
        Create a new document with metadata.
        Accepts document_id from frontend for consistency across Firebase services.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Extract validated data
            validated_data = serializer.validated_data
            document_id = str(validated_data['document_id'])
            
            # Create document in Firestore first (authoritative)
            firestore_doc = firestore_service.create_document(
                document_id=document_id,
                title=validated_data['title'],
                owner_uid=request.user_uid,
                file_type=validated_data['file_type'],
                storage_path=validated_data.get('storage_path', ''),
                status=validated_data.get('status', 'PENDING')
            )
            
            # Create Django model instance for ORM compatibility
            document = Document.objects.create(
                document_id=validated_data['document_id'],
                title=validated_data['title'],
                owner_uid=request.user_uid,
                file_type=validated_data['file_type'],
                storage_path=validated_data.get('storage_path', ''),
                status=validated_data.get('status', 'PENDING')
            )
            
            # Log the creation
            History.log_action(
                document_id=document.document_id,
                action=History.Action.CREATED,
                actor_uid=request.user_uid
            )
            
            log_document_operation(
                operation="create",
                document_id=document_id,
                user_uid=request.user_uid,
                extra={'title': validated_data['title'], 'file_type': validated_data['file_type']}
            )
            
            response_serializer = DocumentSerializer(document, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except FirestoreError as e:
            raise DocumentFirestoreError(
                message="Failed to create document in Firestore",
                operation="create_document",
                document_id=document_id,
                original_error=e
            )
        except Exception as e:
            documents_logger.error(
                f"Unexpected error creating document: {str(e)}",
                extra={'document_id': document_id, 'user_uid': request.user_uid},
                request=request,
                exc_info=True
            )
            raise
    
    @log_api_request
    def list(self, request: Request) -> Response:
        """
        List documents for the authenticated user with pagination.
        """
        try:
            # Get pagination parameters
            limit = min(int(request.query_params.get('limit', 20)), 100)
            offset = int(request.query_params.get('offset', 0))
            
            # Get documents from Firestore (authoritative)
            firestore_docs = firestore_service.list_user_documents(
                owner_uid=request.user_uid,
                limit=limit,
                offset=offset
            )
            
            # Convert to Django model instances for serialization
            documents = []
            for doc_data in firestore_docs:
                document, created = Document.objects.get_or_create(
                    document_id=doc_data['document_id'],
                    defaults={
                        'title': doc_data.get('title', ''),
                        'owner_uid': doc_data.get('owner_uid', ''),
                        'file_type': doc_data.get('file_type', ''),
                        'storage_path': doc_data.get('storage_path', ''),
                        'language_code': doc_data.get('language_code'),
                        'status': doc_data.get('status', 'PENDING'),
                    }
                )
                
                # Update with latest data if not created
                if not created:
                    for field, value in doc_data.items():
                        if hasattr(document, field) and field not in ['document_id', 'created_at']:
                            setattr(document, field, value)
                    document.save()
                
                documents.append(document)
            
            serializer = self.get_serializer(documents, many=True)
            
            response_data = {
                'results': serializer.data,
                'count': len(documents),
                'limit': limit,
                'offset': offset,
                'has_more': len(documents) == limit  # Simple check for more data
            }
            
            return Response(response_data)
            
        except FirestoreError as e:
            raise DocumentFirestoreError(
                message="Failed to retrieve documents from Firestore",
                operation="list_documents",
                original_error=e
            )
        except Exception as e:
            documents_logger.error(
                f"Unexpected error listing documents: {str(e)}",
                extra={'user_uid': request.user_uid},
                request=request,
                exc_info=True
            )
            raise
    
    @log_api_request
    def retrieve(self, request: Request, pk=None) -> Response:
        """
        Retrieve a specific document by ID.
        """
        try:
            document = self.get_object()
            serializer = self.get_serializer(document)
            return Response(serializer.data)
            
        except Http404:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error retrieving document {pk}: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request: Request, pk=None) -> Response:
        """
        Delete a document and all associated files.
        """
        try:
            document = self.get_object()
            document_id = str(document.document_id)
            
            # Delete from GCS first
            try:
                gcs_service.delete_document(document_id, request.user_uid)
            except GCSError as e:
                logger.warning(f"Failed to delete GCS files for document {document_id}: {str(e)}")
                # Continue with deletion even if GCS fails
            
            # Delete from Firestore
            firestore_deleted = firestore_service.delete_document(document_id, request.user_uid)
            
            if not firestore_deleted:
                return Response(
                    {'error': 'Document not found or unauthorized'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Delete Django model instance
            document.delete()
            
            # Log the deletion
            History.log_action(
                document_id=uuid.UUID(document_id),
                action=History.Action.ERROR,  # Using ERROR as closest to deletion
                actor_uid=request.user_uid,
                payload={'action': 'deleted'}
            )
            
            logger.info(f"Deleted document {document_id} for user {request.user_uid}")
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Http404:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except FirestoreError as e:
            logger.error(f"Failed to delete document from Firestore: {str(e)}")
            return Response(
                {'error': 'Failed to delete document', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error deleting document {pk}: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentUploadView(APIView):
    """
    API view for document file upload and processing.
    
    Provides:
    - POST /api/documents/{id}/upload/ - Upload file content
    
    Integrates text extraction and GCS storage, updates document status
    after successful processing.
    
    Requirements: 1.2, 1.4, 8.2
    """
    
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsDocumentOwner]
    parser_classes = [MultiPartParser, FormParser]
    
    @log_api_request
    def post(self, request: Request, document_id: str) -> Response:
        """
        Upload and process a document file.
        
        Args:
            request: HTTP request with file upload
            document_id: UUID of the document to upload file for
            
        Returns:
            Response with processing results
        """
        try:
            # Validate document_id format
            try:
                doc_uuid = uuid.UUID(document_id)
            except ValueError:
                return Response(
                    {'error': 'Invalid document ID format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if document exists and user has access
            firestore_doc = firestore_service.get_document(document_id, request.user_uid)
            if not firestore_doc:
                return Response(
                    {'error': 'Document not found or unauthorized'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Validate file upload
            upload_serializer = DocumentUploadSerializer(data=request.data)
            upload_serializer.is_valid(raise_exception=True)
            
            uploaded_file = upload_serializer.validated_data['file']
            
            logger.info(f"Starting file upload for document {document_id}, file: {uploaded_file.name}")
            
            # Update document status to PROCESSING
            firestore_service.update_document(
                document_id,
                request.user_uid,
                {'status': 'PROCESSING'}
            )
            
            try:
                # Upload file to GCS
                upload_result = gcs_service.upload_document(
                    file_obj=uploaded_file,
                    document_id=document_id,
                    owner_uid=request.user_uid,
                    original_filename=uploaded_file.name
                )
                
                logger.info(f"File uploaded to GCS: {upload_result['storage_path']}")
                
                # Extract text from uploaded file
                text_extractor = TextExtractor()
                uploaded_file.seek(0)  # Reset file pointer
                file_content = uploaded_file.read()
                
                extraction_result = text_extractor.extract_text(
                    file_content=file_content,
                    filename=uploaded_file.name
                )
                
                extracted_text = extraction_result['text']
                detected_encoding = extraction_result.get('encoding')
                
                logger.info(f"Text extracted: {len(extracted_text)} characters")
                
                # Upload extracted text to GCS for backup
                try:
                    text_storage_path = gcs_service.upload_extracted_text(
                        text_content=extracted_text,
                        document_id=document_id,
                        owner_uid=request.user_uid
                    )
                    logger.info(f"Extracted text uploaded to: {text_storage_path}")
                except GCSError as e:
                    logger.warning(f"Failed to upload extracted text: {str(e)}")
                    # Continue processing even if text backup fails
                
                # Detect document language using Vertex AI
                try:
                    import asyncio
                    detected_language = asyncio.run(vertex_client.detect_language(extracted_text[:1000]))
                    logger.info(f"Detected language: {detected_language}")
                except Exception as e:
                    logger.warning(f"Language detection failed: {str(e)}")
                    detected_language = 'en'  # Default to English
                
                # Update document with processing results
                update_data = {
                    'storage_path': upload_result['storage_path'],
                    'extracted_text': extracted_text,
                    'language_code': detected_language,
                    'file_type': upload_result['mime_type'],
                    'status': 'ANALYZED'
                }
                
                firestore_service.update_document(
                    document_id,
                    request.user_uid,
                    update_data
                )
                
                # Update Django model
                try:
                    document = Document.objects.get(document_id=doc_uuid)
                    for field, value in update_data.items():
                        if hasattr(document, field):
                            setattr(document, field, value)
                    document.save()
                except Document.DoesNotExist:
                    # Create Django model if it doesn't exist
                    Document.objects.create(
                        document_id=doc_uuid,
                        title=firestore_doc.get('title', uploaded_file.name),
                        owner_uid=request.user_uid,
                        **update_data
                    )
                
                # Log the upload
                History.log_action(
                    document_id=doc_uuid,
                    action=History.Action.UPLOADED,
                    actor_uid=request.user_uid,
                    payload={
                        'filename': uploaded_file.name,
                        'file_size': upload_result['file_size'],
                        'mime_type': upload_result['mime_type'],
                        'text_length': len(extracted_text),
                        'detected_language': detected_language
                    }
                )
                
                logger.info(f"Document {document_id} processing completed successfully")
                
                # Return processing results
                return Response({
                    'message': 'File uploaded and processed successfully',
                    'document_id': document_id,
                    'file_info': {
                        'original_filename': uploaded_file.name,
                        'file_size': upload_result['file_size'],
                        'mime_type': upload_result['mime_type'],
                        'storage_path': upload_result['storage_path']
                    },
                    'processing_results': {
                        'text_length': len(extracted_text),
                        'detected_language': detected_language,
                        'detected_encoding': detected_encoding,
                        'extraction_metadata': extraction_result.get('metadata', {})
                    },
                    'status': 'ANALYZED'
                }, status=status.HTTP_200_OK)
                
            except GCSError as e:
                logger.error(f"GCS upload failed for document {document_id}: {str(e)}")
                
                # Update document status to ERROR
                firestore_service.update_document(
                    document_id,
                    request.user_uid,
                    {'status': 'ERROR'}
                )
                
                return Response(
                    {'error': 'File upload failed', 'detail': str(e)},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
            except TextExtractionError as e:
                logger.error(f"Text extraction failed for document {document_id}: {str(e)}")
                
                # Update document status to ERROR
                firestore_service.update_document(
                    document_id,
                    request.user_uid,
                    {'status': 'ERROR'}
                )
                
                return Response(
                    {'error': 'Text extraction failed', 'detail': str(e)},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )
                
        except FirestoreError as e:
            logger.error(f"Firestore error during upload for document {document_id}: {str(e)}")
            return Response(
                {'error': 'Database error', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
        except Exception as e:
            logger.error(f"Unexpected error during upload for document {document_id}: {str(e)}")
            
            # Try to update document status to ERROR
            try:
                firestore_service.update_document(
                    document_id,
                    request.user_uid,
                    {'status': 'ERROR'}
                )
            except:
                pass  # Don't fail if we can't update status
            
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentAnalyzeView(APIView):
    """
    API view for AI-powered document analysis.
    
    Provides:
    - POST /api/documents/{id}/analyze/ - Trigger AI analysis
    
    Supports analysis type parameters (summary, key_points, risks, translation)
    and integrates with enhanced Vertex AI client. Stores analysis results in Firestore.
    
    Requirements: 2.1, 3.1, 4.1, 5.1
    """
    
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsDocumentOwner]
    parser_classes = [JSONParser]
    
    @log_api_request
    def post(self, request: Request, document_id: str) -> Response:
        """
        Perform AI analysis on a document.
        
        Args:
            request: HTTP request with analysis parameters
            document_id: UUID of the document to analyze
            
        Returns:
            Response with analysis results
        """
        try:
            # Validate document_id format
            try:
                doc_uuid = uuid.UUID(document_id)
            except ValueError:
                return Response(
                    {'error': 'Invalid document ID format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if document exists and user has access
            firestore_doc = firestore_service.get_document(document_id, request.user_uid)
            if not firestore_doc:
                return Response(
                    {'error': 'Document not found or unauthorized'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if document has extracted text
            extracted_text = firestore_doc.get('extracted_text')
            if not extracted_text:
                return Response(
                    {'error': 'Document has no extracted text. Please upload a file first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate analysis request parameters
            analysis_serializer = AnalysisRequestSerializer(data=request.data)
            analysis_serializer.is_valid(raise_exception=True)
            
            analysis_params = analysis_serializer.validated_data
            analysis_type = analysis_params['analysis_type']
            target_language = analysis_params.get('target_language')
            
            logger.info(f"Starting {analysis_type} analysis for document {document_id}")
            
            try:
                import asyncio
                
                # Perform AI analysis based on type
                if analysis_type == 'all':
                    # Perform all analysis types
                    analysis_results = {}
                    
                    # Summary
                    summary_result = asyncio.run(vertex_client.summarize_document(
                        extracted_text, target_language
                    ))
                    analysis_results['summary'] = summary_result
                    
                    # Key points
                    key_points_result = asyncio.run(vertex_client.extract_key_points(
                        extracted_text, target_language
                    ))
                    analysis_results['key_points'] = key_points_result
                    
                    # Risk analysis
                    risks_result = asyncio.run(vertex_client.detect_risks(
                        extracted_text, target_language
                    ))
                    analysis_results['risks'] = risks_result
                    
                    # Translation (if target language specified)
                    if target_language:
                        translation_result = asyncio.run(vertex_client.translate_content(
                            extracted_text[:2000],  # Limit for translation
                            target_language
                        ))
                        analysis_results['translation'] = translation_result
                    
                    # Combine token usage
                    total_tokens = {
                        'input_tokens': sum(r.get('token_usage', {}).get('input_tokens', 0) for r in analysis_results.values()),
                        'output_tokens': sum(r.get('token_usage', {}).get('output_tokens', 0) for r in analysis_results.values())
                    }
                    total_tokens['total_tokens'] = total_tokens['input_tokens'] + total_tokens['output_tokens']
                    
                    # Use summary's detected language as primary
                    detected_language = summary_result.get('detected_language', 'en')
                    
                else:
                    # Single analysis type
                    if analysis_type == 'summary':
                        analysis_results = asyncio.run(vertex_client.summarize_document(
                            extracted_text, target_language
                        ))
                    elif analysis_type == 'key_points':
                        analysis_results = asyncio.run(vertex_client.extract_key_points(
                            extracted_text, target_language
                        ))
                    elif analysis_type == 'risks':
                        analysis_results = asyncio.run(vertex_client.detect_risks(
                            extracted_text, target_language
                        ))
                    elif analysis_type == 'translation':
                        if not target_language:
                            return Response(
                                {'error': 'target_language is required for translation analysis'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        analysis_results = asyncio.run(vertex_client.translate_content(
                            extracted_text[:2000],  # Limit for translation
                            target_language
                        ))
                    else:
                        return Response(
                            {'error': f'Unsupported analysis type: {analysis_type}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    total_tokens = analysis_results.get('token_usage', {})
                    detected_language = analysis_results.get('detected_language', 'en')
                
                logger.info(f"AI analysis completed, tokens used: {total_tokens.get('total_tokens', 0)}")
                
                # Get next version number for this document
                try:
                    latest_analysis = Analysis.objects.filter(
                        document_id=doc_uuid
                    ).order_by('-version').first()
                    
                    next_version = (latest_analysis.version + 1) if latest_analysis else 1
                except:
                    next_version = 1
                
                # Prepare analysis data for storage
                analysis_data = {
                    'document_id': document_id,
                    'version': next_version,
                    'target_language': target_language,
                    'summary': {},
                    'key_points': [],
                    'risk_alerts': [],
                    'token_usage': total_tokens
                }
                
                # Extract data based on analysis type
                if analysis_type == 'all':
                    # Extract from combined results
                    if 'summary' in analysis_results:
                        analysis_data['summary'] = analysis_results['summary'].get('summary', {})
                    if 'key_points' in analysis_results:
                        analysis_data['key_points'] = analysis_results['key_points'].get('key_points', [])
                    if 'risks' in analysis_results:
                        analysis_data['risk_alerts'] = analysis_results['risks'].get('risks', [])
                else:
                    # Extract from single analysis
                    if analysis_type == 'summary':
                        analysis_data['summary'] = analysis_results.get('summary', {})
                    elif analysis_type == 'key_points':
                        analysis_data['key_points'] = analysis_results.get('key_points', [])
                    elif analysis_type == 'risks':
                        analysis_data['risk_alerts'] = analysis_results.get('risks', [])
                    elif analysis_type == 'translation':
                        # Store translation in summary field with language keys
                        original_lang = analysis_results.get('original_language', 'en')
                        analysis_data['summary'] = {
                            original_lang: analysis_results.get('original_content', ''),
                            target_language: analysis_results.get('translated_content', '')
                        }
                
                # Store analysis results in Firestore
                firestore_service.store_analysis_result(
                    document_id=document_id,
                    owner_uid=request.user_uid,
                    analysis_type=analysis_type,
                    result=analysis_data,
                    version=next_version
                )
                
                # Store in Django model for ORM compatibility
                Analysis.objects.create(
                    document_id=doc_uuid,
                    version=next_version,
                    target_language=target_language,
                    summary=analysis_data['summary'],
                    key_points=analysis_data['key_points'],
                    risk_alerts=analysis_data['risk_alerts'],
                    token_usage=analysis_data['token_usage']
                )
                
                # Log the analysis
                History.log_action(
                    document_id=doc_uuid,
                    action=History.Action.ANALYZED,
                    actor_uid=request.user_uid,
                    version=next_version,
                    payload={
                        'analysis_type': analysis_type,
                        'target_language': target_language,
                        'token_usage': total_tokens
                    }
                )
                
                logger.info(f"Analysis results stored for document {document_id}, version {next_version}")
                
                # Prepare response data
                response_data = {
                    'document_id': document_id,
                    'version': next_version,
                    'analysis_type': analysis_type,
                    'detected_language': detected_language,
                    'target_language': target_language,
                    'token_usage': total_tokens,
                    'completion_time': analysis_data.get('completion_time'),
                    'results': analysis_results if analysis_type != 'all' else {
                        'summary': analysis_results.get('summary', {}),
                        'key_points': analysis_results.get('key_points', {}),
                        'risks': analysis_results.get('risks', {}),
                        'translation': analysis_results.get('translation', {}) if target_language else None
                    }
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
                
            except ValueError as e:
                logger.error(f"AI analysis validation error for document {document_id}: {str(e)}")
                return Response(
                    {'error': 'Analysis request invalid', 'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            except Exception as e:
                logger.error(f"AI analysis failed for document {document_id}: {str(e)}")
                return Response(
                    {'error': 'AI analysis failed', 'detail': str(e)},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
        except FirestoreError as e:
            logger.error(f"Firestore error during analysis for document {document_id}: {str(e)}")
            return Response(
                {'error': 'Database error', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
        except Exception as e:
            logger.error(f"Unexpected error during analysis for document {document_id}: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentDownloadView(APIView):
    """
    API view for document file download.
    
    Provides:
    - GET /api/documents/{id}/download/ - Get signed download URL
    
    Generates signed URLs using GCS service with proper authorization
    and owner validation. Returns appropriate content-type headers.
    
    Requirements: 6.1, 6.3, 7.4
    """
    
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsDocumentOwner]
    
    @log_api_request
    def get(self, request: Request, document_id: str) -> Response:
        """
        Generate signed URL for document download.
        
        Args:
            request: HTTP request
            document_id: UUID of the document to download
            
        Returns:
            Response with signed download URL and metadata
        """
        try:
            # Validate document_id format
            try:
                doc_uuid = uuid.UUID(document_id)
            except ValueError:
                return Response(
                    {'error': 'Invalid document ID format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if document exists and user has access
            firestore_doc = firestore_service.get_document(document_id, request.user_uid)
            if not firestore_doc:
                return Response(
                    {'error': 'Document not found or unauthorized'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if document has been uploaded (has storage_path)
            storage_path = firestore_doc.get('storage_path')
            if not storage_path:
                return Response(
                    {'error': 'Document file not uploaded yet'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                # Get document file information from GCS
                file_info = gcs_service.get_document_info(document_id, request.user_uid)
                
                if not file_info:
                    return Response(
                        {'error': 'Document file not found in storage'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Generate signed URL with 1-hour expiry
                expiry_hours = int(request.query_params.get('expiry_hours', 1))
                expiry_hours = min(max(expiry_hours, 1), 24)  # Limit between 1-24 hours
                
                signed_url = gcs_service.generate_signed_url(
                    document_id=document_id,
                    owner_uid=request.user_uid,
                    expiry_hours=expiry_hours
                )
                
                # Log the download request
                History.log_action(
                    document_id=doc_uuid,
                    action=History.Action.DOWNLOADED,
                    actor_uid=request.user_uid,
                    payload={
                        'expiry_hours': expiry_hours,
                        'file_size': file_info.get('size'),
                        'content_type': file_info.get('content_type')
                    }
                )
                
                logger.info(f"Generated download URL for document {document_id}, expires in {expiry_hours} hours")
                
                # Prepare response with download information
                response_data = {
                    'document_id': document_id,
                    'download_url': signed_url,
                    'expires_in_hours': expiry_hours,
                    'file_info': {
                        'filename': firestore_doc.get('title', 'document'),
                        'content_type': file_info.get('content_type'),
                        'size': file_info.get('size'),
                        'storage_path': file_info.get('storage_path'),
                        'created': file_info.get('created'),
                        'updated': file_info.get('updated')
                    },
                    'metadata': file_info.get('metadata', {})
                }
                
                # Set appropriate response headers
                response = Response(response_data, status=status.HTTP_200_OK)
                
                # Add content-type header based on file type
                content_type = file_info.get('content_type', 'application/octet-stream')
                response['X-Content-Type'] = content_type
                
                # Add content-disposition header for download
                filename = firestore_doc.get('title', 'document')
                # Sanitize filename for header
                safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).strip()
                response['X-Content-Disposition'] = f'attachment; filename="{safe_filename}"'
                
                return response
                
            except GCSError as e:
                logger.error(f"GCS error generating download URL for document {document_id}: {str(e)}")
                return Response(
                    {'error': 'Failed to generate download URL', 'detail': str(e)},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
        except FirestoreError as e:
            logger.error(f"Firestore error during download for document {document_id}: {str(e)}")
            return Response(
                {'error': 'Database error', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
        except Exception as e:
            logger.error(f"Unexpected error during download for document {document_id}: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Additional utility views for document management

class DocumentAnalysisHistoryView(APIView):
    """
    API view to retrieve analysis history for a document.
    
    Provides:
    - GET /api/documents/{id}/analysis/ - Get latest analysis
    - GET /api/documents/{id}/analysis/{version}/ - Get specific analysis version
    """
    
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsDocumentOwner]
    
    def get(self, request: Request, document_id: str, version: int = None) -> Response:
        """
        Get analysis results for a document.
        
        Args:
            request: HTTP request
            document_id: UUID of the document
            version: Optional specific version number
            
        Returns:
            Response with analysis results
        """
        try:
            # Validate document_id format
            try:
                doc_uuid = uuid.UUID(document_id)
            except ValueError:
                return Response(
                    {'error': 'Invalid document ID format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if document exists and user has access
            firestore_doc = firestore_service.get_document(document_id, request.user_uid)
            if not firestore_doc:
                return Response(
                    {'error': 'Document not found or unauthorized'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            try:
                if version:
                    # Get specific version
                    analysis = Analysis.objects.filter(
                        document_id=doc_uuid,
                        version=version
                    ).first()
                else:
                    # Get latest version
                    analysis = Analysis.objects.filter(
                        document_id=doc_uuid
                    ).order_by('-version').first()
                
                if not analysis:
                    return Response(
                        {'error': 'Analysis not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                serializer = AnalysisResultSerializer({
                    'document_id': analysis.document_id,
                    'version': analysis.version,
                    'detected_language': firestore_doc.get('language_code', 'en'),
                    'target_language': analysis.target_language,
                    'summary': analysis.summary,
                    'key_points': analysis.key_points,
                    'risk_alerts': analysis.risk_alerts,
                    'token_usage': analysis.token_usage,
                    'completion_time': analysis.completion_time
                })
                
                return Response(serializer.data, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Error retrieving analysis for document {document_id}: {str(e)}")
                return Response(
                    {'error': 'Failed to retrieve analysis'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except FirestoreError as e:
            logger.error(f"Firestore error retrieving analysis for document {document_id}: {str(e)}")
            return Response(
                {'error': 'Database error', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
        except Exception as e:
            logger.error(f"Unexpected error retrieving analysis for document {document_id}: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )