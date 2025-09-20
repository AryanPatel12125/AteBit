"""
Google Cloud Storage service for document file operations.
"""
import logging
import os
import time
from typing import Optional, BinaryIO, Dict, Any
from datetime import datetime, timedelta

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from ..logging_utils import services_logger, log_performance, log_storage_operation

logger = logging.getLogger(__name__)

# Import Google Cloud modules only if not in test mode
if not (getattr(settings, 'TESTING', False) or os.environ.get('TESTING')):
    from google.cloud import storage
    from google.cloud.exceptions import GoogleCloudError
    try:
        import magic
    except ImportError:
        # Handle missing libmagic dependency gracefully
        magic = None
        logger.warning("python-magic not available, MIME type detection will be limited")
else:
    # Mock for testing
    from unittest.mock import Mock
    storage = Mock()
    GoogleCloudError = Exception
    magic = Mock()


class GCSService:
    """
    Service class for Google Cloud Storage operations.
    Handles document file upload, download, and management with consistent document_id paths.
    """
    
    def __init__(self):
        """Initialize GCS client with project settings."""
        # Skip authentication in test mode
        if getattr(settings, 'TESTING', False) or os.environ.get('TESTING'):
            from unittest.mock import Mock
            self.client = Mock()
            self.bucket = Mock()
        else:
            self.client = storage.Client(project=settings.GOOGLE_CLOUD_PROJECT)
            self.bucket = self.client.bucket(self.bucket_name)
        
        self.bucket_name = getattr(settings, 'GCS_BUCKET_NAME', f"{settings.GOOGLE_CLOUD_PROJECT}-documents")
        
        # Supported file types and their extensions
        self.supported_mime_types = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/msword': '.doc',
            'text/plain': '.txt',
        }
        
        # Maximum file size (10MB)
        self.max_file_size = 10 * 1024 * 1024
    
    def _get_storage_path(self, owner_uid: str, document_id: str, filename: str) -> str:
        """
        Generate consistent storage path for document files.
        
        Args:
            owner_uid: Firebase user ID
            document_id: Document identifier
            filename: Original filename or file type
            
        Returns:
            GCS storage path
        """
        return f"documents/{owner_uid}/{document_id}/{filename}"
    
    def _validate_file(self, file_obj: BinaryIO, filename: str) -> Dict[str, Any]:
        """
        Validate uploaded file for type, size, and content.
        
        Args:
            file_obj: File object to validate
            filename: Original filename
            
        Returns:
            Validation result with mime_type and extension
            
        Raises:
            GCSError: If file validation fails
        """
        try:
            # Check file size
            file_obj.seek(0, os.SEEK_END)
            file_size = file_obj.tell()
            file_obj.seek(0)
            
            if file_size > self.max_file_size:
                raise GCSError(f"File size {file_size} bytes exceeds maximum allowed size of {self.max_file_size} bytes")
            
            if file_size == 0:
                raise GCSError("File is empty")
            
            # Detect MIME type using python-magic or fallback to content type
            if magic:
                file_content = file_obj.read(2048)  # Read first 2KB for MIME detection
                file_obj.seek(0)
                mime_type = magic.from_buffer(file_content, mime=True)
            else:
                # Fallback to uploaded file content type
                mime_type = getattr(file_obj, 'content_type', 'application/octet-stream')
                logger.warning(f"Using fallback MIME type detection: {mime_type}")
            
            # Validate supported file type
            if mime_type not in self.supported_mime_types:
                supported_types = ', '.join(self.supported_mime_types.keys())
                raise GCSError(f"Unsupported file type '{mime_type}'. Supported types: {supported_types}")
            
            # Get file extension
            extension = self.supported_mime_types[mime_type]
            
            logger.info(f"File validation successful: {filename} ({mime_type}, {file_size} bytes)")
            
            return {
                'mime_type': mime_type,
                'extension': extension,
                'file_size': file_size,
                'validated': True
            }
            
        except Exception as e:
            if isinstance(e, GCSError):
                raise
            logger.error(f"File validation failed for {filename}: {str(e)}")
            raise GCSError(f"File validation failed: {str(e)}")
    
    @log_performance("gcs_upload_document")
    def upload_document(
        self,
        file_obj: BinaryIO,
        document_id: str,
        owner_uid: str,
        original_filename: str
    ) -> Dict[str, Any]:
        """
        Upload document file to Google Cloud Storage with validation.
        
        Args:
            file_obj: File object to upload
            document_id: Unique document identifier
            owner_uid: Firebase user ID of document owner
            original_filename: Original filename from upload
            
        Returns:
            Upload result with storage_path, mime_type, and file_size
            
        Raises:
            GCSError: If upload fails or file validation fails
        """
        start_time = time.time()
        try:
            # Validate file first
            validation_result = self._validate_file(file_obj, original_filename)
            
            # Generate storage path with proper extension
            storage_filename = f"original{validation_result['extension']}"
            storage_path = self._get_storage_path(owner_uid, document_id, storage_filename)
            
            # Create blob and upload
            blob = self.bucket.blob(storage_path)
            
            # Set metadata
            blob.metadata = {
                'document_id': document_id,
                'owner_uid': owner_uid,
                'original_filename': original_filename,
                'uploaded_at': datetime.utcnow().isoformat(),
            }
            
            # Set content type
            blob.content_type = validation_result['mime_type']
            
            # Upload file
            file_obj.seek(0)
            blob.upload_from_file(file_obj)
            
            duration = time.time() - start_time
            
            # Log successful upload
            log_storage_operation(
                operation="upload_document",
                file_path=storage_path,
                duration=duration,
                file_size=validation_result['file_size'],
                extra={
                    'document_id': document_id,
                    'owner_uid': owner_uid,
                    'mime_type': validation_result['mime_type'],
                    'original_filename': original_filename
                }
            )
            
            return {
                'storage_path': storage_path,
                'mime_type': validation_result['mime_type'],
                'file_size': validation_result['file_size'],
                'bucket_name': self.bucket_name,
                'uploaded_at': datetime.utcnow().isoformat(),
            }
            
        except GoogleCloudError as e:
            duration = time.time() - start_time
            services_logger.error(
                f"GCS upload failed for document {document_id}: {str(e)}",
                extra={
                    'document_id': document_id,
                    'owner_uid': owner_uid,
                    'duration_ms': round(duration * 1000, 2),
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            raise GCSError(f"Failed to upload document to storage: {str(e)}")
        except Exception as e:
            if isinstance(e, GCSError):
                raise
            duration = time.time() - start_time
            services_logger.error(
                f"Unexpected error during upload for document {document_id}: {str(e)}",
                extra={
                    'document_id': document_id,
                    'owner_uid': owner_uid,
                    'duration_ms': round(duration * 1000, 2),
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            raise GCSError(f"Upload failed: {str(e)}")
    
    def upload_extracted_text(
        self,
        text_content: str,
        document_id: str,
        owner_uid: str
    ) -> str:
        """
        Upload extracted text content to GCS for backup/reference.
        
        Args:
            text_content: Extracted text content
            document_id: Document identifier
            owner_uid: Firebase user ID
            
        Returns:
            Storage path for extracted text
            
        Raises:
            GCSError: If upload fails
        """
        try:
            storage_path = self._get_storage_path(owner_uid, document_id, "extracted.txt")
            blob = self.bucket.blob(storage_path)
            
            # Set metadata
            blob.metadata = {
                'document_id': document_id,
                'owner_uid': owner_uid,
                'content_type': 'extracted_text',
                'extracted_at': datetime.utcnow().isoformat(),
            }
            
            blob.content_type = 'text/plain; charset=utf-8'
            
            # Upload text content
            blob.upload_from_string(text_content, content_type='text/plain; charset=utf-8')
            
            logger.info(f"Successfully uploaded extracted text for document {document_id}")
            return storage_path
            
        except GoogleCloudError as e:
            logger.error(f"Failed to upload extracted text for document {document_id}: {str(e)}")
            raise GCSError(f"Failed to upload extracted text: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error uploading extracted text for document {document_id}: {str(e)}")
            raise GCSError(f"Failed to upload extracted text: {str(e)}")
    
    def generate_signed_url(
        self,
        document_id: str,
        owner_uid: str,
        expiry_hours: int = 1
    ) -> str:
        """
        Generate signed URL for document download with 1-hour expiry.
        
        Args:
            document_id: Document identifier
            owner_uid: Firebase user ID for authorization
            expiry_hours: URL expiry time in hours (default: 1)
            
        Returns:
            Signed URL for document download
            
        Raises:
            GCSError: If URL generation fails or document not found
        """
        try:
            # Find the original document file (could be .pdf, .docx, .doc, or .txt)
            storage_path = None
            blob = None
            
            # Try each supported extension to find the original file
            for mime_type, extension in self.supported_mime_types.items():
                test_path = self._get_storage_path(owner_uid, document_id, f"original{extension}")
                test_blob = self.bucket.blob(test_path)
                
                if test_blob.exists():
                    storage_path = test_path
                    blob = test_blob
                    break
            
            if not blob or not blob.exists():
                raise GCSError(f"Document file not found for document {document_id}")
            
            # Verify ownership through metadata
            blob.reload()  # Refresh metadata
            if blob.metadata and blob.metadata.get('owner_uid') != owner_uid:
                raise GCSError(f"Unauthorized access to document {document_id}")
            
            # Generate signed URL with expiry
            expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)
            
            signed_url = blob.generate_signed_url(
                expiration=expiry_time,
                method='GET',
                version='v4'
            )
            
            logger.info(f"Generated signed URL for document {document_id}, expires at {expiry_time}")
            
            return signed_url
            
        except GoogleCloudError as e:
            logger.error(f"Failed to generate signed URL for document {document_id}: {str(e)}")
            raise GCSError(f"Failed to generate download URL: {str(e)}")
        except Exception as e:
            if isinstance(e, GCSError):
                raise
            logger.error(f"Unexpected error generating signed URL for document {document_id}: {str(e)}")
            raise GCSError(f"Failed to generate download URL: {str(e)}")
    
    def get_document_info(
        self,
        document_id: str,
        owner_uid: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get document file information from GCS.
        
        Args:
            document_id: Document identifier
            owner_uid: Firebase user ID for authorization
            
        Returns:
            Document file information or None if not found
        """
        try:
            # Find the original document file
            for mime_type, extension in self.supported_mime_types.items():
                storage_path = self._get_storage_path(owner_uid, document_id, f"original{extension}")
                blob = self.bucket.blob(storage_path)
                
                if blob.exists():
                    blob.reload()  # Refresh metadata and properties
                    
                    # Verify ownership
                    if blob.metadata and blob.metadata.get('owner_uid') != owner_uid:
                        return None
                    
                    return {
                        'storage_path': storage_path,
                        'content_type': blob.content_type,
                        'size': blob.size,
                        'created': blob.time_created.isoformat() if blob.time_created else None,
                        'updated': blob.updated.isoformat() if blob.updated else None,
                        'metadata': blob.metadata or {},
                    }
            
            return None
            
        except GoogleCloudError as e:
            logger.error(f"Failed to get document info for {document_id}: {str(e)}")
            raise GCSError(f"Failed to get document information: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting document info for {document_id}: {str(e)}")
            raise GCSError(f"Failed to get document information: {str(e)}")
    
    def delete_document(
        self,
        document_id: str,
        owner_uid: str
    ) -> bool:
        """
        Delete all files associated with a document from GCS.
        
        Args:
            document_id: Document identifier
            owner_uid: Firebase user ID for authorization
            
        Returns:
            True if deletion was successful, False if document not found
            
        Raises:
            GCSError: If deletion fails due to authorization or GCS errors
        """
        try:
            deleted_files = []
            
            # Delete original document file (try all supported extensions)
            for mime_type, extension in self.supported_mime_types.items():
                storage_path = self._get_storage_path(owner_uid, document_id, f"original{extension}")
                blob = self.bucket.blob(storage_path)
                
                if blob.exists():
                    blob.reload()  # Refresh metadata
                    
                    # Verify ownership
                    if blob.metadata and blob.metadata.get('owner_uid') != owner_uid:
                        raise GCSError(f"Unauthorized deletion attempt for document {document_id}")
                    
                    blob.delete()
                    deleted_files.append(storage_path)
            
            # Delete extracted text file if it exists
            text_path = self._get_storage_path(owner_uid, document_id, "extracted.txt")
            text_blob = self.bucket.blob(text_path)
            
            if text_blob.exists():
                text_blob.reload()
                
                # Verify ownership
                if text_blob.metadata and text_blob.metadata.get('owner_uid') != owner_uid:
                    raise GCSError(f"Unauthorized deletion attempt for document {document_id}")
                
                text_blob.delete()
                deleted_files.append(text_path)
            
            if deleted_files:
                logger.info(f"Successfully deleted {len(deleted_files)} files for document {document_id}: {deleted_files}")
                return True
            else:
                logger.info(f"No files found to delete for document {document_id}")
                return False
                
        except GoogleCloudError as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            raise GCSError(f"Failed to delete document files: {str(e)}")
        except Exception as e:
            if isinstance(e, GCSError):
                raise
            logger.error(f"Unexpected error deleting document {document_id}: {str(e)}")
            raise GCSError(f"Failed to delete document files: {str(e)}")
    
    def list_document_files(
        self,
        owner_uid: str,
        document_id: str = None
    ) -> list:
        """
        List all files for a user or specific document.
        
        Args:
            owner_uid: Firebase user ID
            document_id: Optional document ID to filter by
            
        Returns:
            List of file information dictionaries
        """
        try:
            prefix = f"documents/{owner_uid}/"
            if document_id:
                prefix += f"{document_id}/"
            
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
            
            files = []
            for blob in blobs:
                blob.reload()  # Get metadata
                
                files.append({
                    'name': blob.name,
                    'size': blob.size,
                    'content_type': blob.content_type,
                    'created': blob.time_created.isoformat() if blob.time_created else None,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'metadata': blob.metadata or {},
                })
            
            logger.info(f"Listed {len(files)} files for user {owner_uid}" + 
                       (f" document {document_id}" if document_id else ""))
            
            return files
            
        except GoogleCloudError as e:
            logger.error(f"Failed to list files for user {owner_uid}: {str(e)}")
            raise GCSError(f"Failed to list document files: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error listing files for user {owner_uid}: {str(e)}")
            raise GCSError(f"Failed to list document files: {str(e)}")


class GCSError(Exception):
    """Custom exception for Google Cloud Storage operations."""
    pass


# Global service instance - lazy loaded to avoid authentication issues during import
gcs_service = None

def get_gcs_service():
    """Get or create the global GCS service instance."""
    global gcs_service
    if gcs_service is None:
        gcs_service = GCSService()
    return gcs_service