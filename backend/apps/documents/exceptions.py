"""
Custom exception classes for the documents app.

This module defines custom exceptions for different service failures
and includes correlation ID generation for error tracking.
"""

import uuid
from typing import Optional, Dict, Any
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


class BaseDocumentException(Exception):
    """Base exception class for all document-related errors."""
    
    def __init__(
        self, 
        message: str, 
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.correlation_id = correlation_id or self.generate_correlation_id()
        self.details = details or {}
        super().__init__(self.message)
    
    @staticmethod
    def generate_correlation_id() -> str:
        """Generate a unique correlation ID for error tracking."""
        return f"req_{uuid.uuid4().hex[:12]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format for API responses."""
        return {
            "code": self.__class__.__name__.upper(),
            "message": self.message,
            "correlation_id": self.correlation_id,
            "details": self.details
        }


class VertexAIError(BaseDocumentException):
    """Exception raised when Vertex AI service operations fail."""
    
    def __init__(
        self, 
        message: str = "AI analysis service temporarily unavailable",
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, correlation_id, details)
        self.original_error = original_error
        
        # Add original error details if available
        if original_error:
            self.details["original_error"] = str(original_error)
            self.details["error_type"] = type(original_error).__name__


class GCSError(BaseDocumentException):
    """Exception raised when Google Cloud Storage operations fail."""
    
    def __init__(
        self, 
        message: str = "File storage operation failed",
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, correlation_id, details)
        self.operation = operation
        self.original_error = original_error
        
        # Add operation and error details
        if operation:
            self.details["operation"] = operation
        if original_error:
            self.details["original_error"] = str(original_error)
            self.details["error_type"] = type(original_error).__name__


class FirestoreError(BaseDocumentException):
    """Exception raised when Firestore database operations fail."""
    
    def __init__(
        self, 
        message: str = "Database operation failed",
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        operation: Optional[str] = None,
        document_id: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, correlation_id, details)
        self.operation = operation
        self.document_id = document_id
        self.original_error = original_error
        
        # Add operation and document details (without sensitive data)
        if operation:
            self.details["operation"] = operation
        if document_id:
            self.details["document_id"] = document_id
        if original_error:
            self.details["original_error"] = str(original_error)
            self.details["error_type"] = type(original_error).__name__


class DocumentNotFoundError(BaseDocumentException):
    """Exception raised when a requested document is not found."""
    
    def __init__(
        self, 
        document_id: str,
        correlation_id: Optional[str] = None
    ):
        message = f"Document not found"
        details = {"document_id": document_id}
        super().__init__(message, correlation_id, details)


class DocumentAccessDeniedError(BaseDocumentException):
    """Exception raised when user lacks permission to access a document."""
    
    def __init__(
        self, 
        document_id: str,
        user_uid: str,
        correlation_id: Optional[str] = None
    ):
        message = "Access denied to document"
        details = {
            "document_id": document_id,
            "user_uid": user_uid
        }
        super().__init__(message, correlation_id, details)


class FileProcessingError(BaseDocumentException):
    """Exception raised when file processing operations fail."""
    
    def __init__(
        self, 
        message: str = "File processing failed",
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        file_type: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, correlation_id, details)
        self.file_type = file_type
        self.original_error = original_error
        
        # Add file type and error details
        if file_type:
            self.details["file_type"] = file_type
        if original_error:
            self.details["original_error"] = str(original_error)
            self.details["error_type"] = type(original_error).__name__


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that handles our custom exceptions.
    
    This handler provides consistent error response format and logging
    for all custom document exceptions.
    """
    # Get the standard DRF response first
    response = exception_handler(exc, context)
    
    # Handle our custom exceptions
    if isinstance(exc, BaseDocumentException):
        # Log the error with correlation ID
        logger.error(
            f"Document service error [{exc.correlation_id}]: {exc.message}",
            extra={
                "correlation_id": exc.correlation_id,
                "exception_type": type(exc).__name__,
                "details": exc.details,
                "view": context.get('view').__class__.__name__ if context.get('view') else None,
                "request_method": context.get('request').method if context.get('request') else None,
            },
            exc_info=exc.original_error if hasattr(exc, 'original_error') and exc.original_error else None
        )
        
        # Determine HTTP status code based on exception type
        if isinstance(exc, DocumentNotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, DocumentAccessDeniedError):
            status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, (VertexAIError, GCSError, FirestoreError)):
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif isinstance(exc, FileProcessingError):
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Create custom error response
        error_response = {
            "error": exc.to_dict()
        }
        
        return Response(error_response, status=status_code)
    
    # For non-custom exceptions, add correlation ID if not already present
    if response is not None and hasattr(exc, '__dict__'):
        correlation_id = BaseDocumentException.generate_correlation_id()
        
        # Log non-custom exceptions with correlation ID
        logger.error(
            f"Unhandled exception [{correlation_id}]: {str(exc)}",
            extra={
                "correlation_id": correlation_id,
                "exception_type": type(exc).__name__,
                "view": context.get('view').__class__.__name__ if context.get('view') else None,
                "request_method": context.get('request').method if context.get('request') else None,
            },
            exc_info=True
        )
        
        # Add correlation ID to existing response
        if isinstance(response.data, dict):
            if 'error' not in response.data:
                response.data = {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": response.data.get('detail', str(exc)),
                        "correlation_id": correlation_id,
                        "details": {}
                    }
                }
            elif isinstance(response.data['error'], dict):
                response.data['error']['correlation_id'] = correlation_id
    
    return response


# Utility functions for raising exceptions with context
def raise_vertex_ai_error(
    message: str = None,
    original_error: Exception = None,
    operation: str = None
) -> None:
    """Utility function to raise VertexAIError with context."""
    details = {}
    if operation:
        details["operation"] = operation
    
    raise VertexAIError(
        message=message or "AI analysis service temporarily unavailable",
        details=details,
        original_error=original_error
    )


def raise_gcs_error(
    message: str = None,
    original_error: Exception = None,
    operation: str = None,
    file_path: str = None
) -> None:
    """Utility function to raise GCSError with context."""
    details = {}
    if file_path:
        details["file_path"] = file_path
    
    raise GCSError(
        message=message or "File storage operation failed",
        details=details,
        operation=operation,
        original_error=original_error
    )


def raise_firestore_error(
    message: str = None,
    original_error: Exception = None,
    operation: str = None,
    document_id: str = None
) -> None:
    """Utility function to raise FirestoreError with context."""
    raise FirestoreError(
        message=message or "Database operation failed",
        operation=operation,
        document_id=document_id,
        original_error=original_error
    )