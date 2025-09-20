"""
Logging utilities for the documents app.

This module provides consistent logging functionality across the application
with performance metrics, request/response logging, and security considerations.
"""

import logging
import time
import json
from typing import Any, Dict, Optional, Union
from functools import wraps
from django.http import HttpRequest
from rest_framework.request import Request


class DocumentLogger:
    """Centralized logger for document operations with security filtering."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.performance_logger = logging.getLogger('performance')
    
    def _sanitize_data(self, data: Any) -> Any:
        """
        Sanitize data to remove sensitive information before logging.
        
        Removes document text content and other sensitive fields to ensure
        no document content appears in production logs.
        """
        if isinstance(data, dict):
            sanitized = {}
            sensitive_fields = {
                'extracted_text', 'text_content', 'document_text', 'content',
                'summary', 'analysis_result', 'password', 'token', 'key'
            }
            
            for key, value in data.items():
                if key.lower() in sensitive_fields:
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, (dict, list)):
                    sanitized[key] = self._sanitize_data(value)
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        else:
            return data
    
    def _get_request_context(self, request: Optional[Union[HttpRequest, Request]]) -> Dict[str, Any]:
        """Extract safe context information from request."""
        if not request:
            return {}
        
        context = {
            'method': getattr(request, 'method', 'UNKNOWN'),
            'path': getattr(request, 'path', 'UNKNOWN'),
        }
        
        # Add user context if available
        if hasattr(request, 'user_uid'):
            context['user_uid'] = request.user_uid
        
        # Add correlation ID if available in headers
        if hasattr(request, 'META'):
            correlation_id = request.META.get('HTTP_X_CORRELATION_ID')
            if correlation_id:
                context['correlation_id'] = correlation_id
        
        return context
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None, request: Optional[Union[HttpRequest, Request]] = None):
        """Log info message with sanitized extra data."""
        extra = extra or {}
        extra.update(self._get_request_context(request))
        extra = self._sanitize_data(extra)
        self.logger.info(message, extra=extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, request: Optional[Union[HttpRequest, Request]] = None, exc_info: bool = False):
        """Log error message with sanitized extra data."""
        extra = extra or {}
        extra.update(self._get_request_context(request))
        extra = self._sanitize_data(extra)
        self.logger.error(message, extra=extra, exc_info=exc_info)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None, request: Optional[Union[HttpRequest, Request]] = None):
        """Log warning message with sanitized extra data."""
        extra = extra or {}
        extra.update(self._get_request_context(request))
        extra = self._sanitize_data(extra)
        self.logger.warning(message, extra=extra)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None, request: Optional[Union[HttpRequest, Request]] = None):
        """Log debug message with sanitized extra data."""
        extra = extra or {}
        extra.update(self._get_request_context(request))
        extra = self._sanitize_data(extra)
        self.logger.debug(message, extra=extra)
    
    def log_performance(self, operation: str, duration: float, extra: Optional[Dict[str, Any]] = None):
        """Log performance metrics for operations."""
        extra = extra or {}
        extra.update({
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'duration_seconds': round(duration, 3)
        })
        extra = self._sanitize_data(extra)
        
        self.performance_logger.info(
            f"Performance: {operation} completed in {duration:.3f}s",
            extra=extra
        )


def log_performance(operation_name: str = None):
    """
    Decorator to automatically log performance metrics for functions.
    
    Args:
        operation_name: Custom name for the operation. If not provided,
                       uses the function name.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            logger = DocumentLogger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log successful operation
                logger.log_performance(
                    operation=operation,
                    duration=duration,
                    extra={
                        'status': 'success',
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # Log failed operation
                logger.log_performance(
                    operation=operation,
                    duration=duration,
                    extra={
                        'status': 'error',
                        'function': func.__name__,
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                )
                
                raise
        
        return wrapper
    return decorator


def log_api_request(view_func):
    """
    Decorator to log API requests and responses.
    
    Logs request method, path, user, and response status while
    ensuring no sensitive document content is logged.
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        start_time = time.time()
        logger = DocumentLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        # Log request start
        request_data = {
            'view': self.__class__.__name__,
            'action': getattr(self, 'action', 'unknown'),
            'document_id': kwargs.get('pk') or kwargs.get('document_id'),
        }
        
        logger.info(
            f"API Request: {request.method} {request.path}",
            extra=request_data,
            request=request
        )
        
        try:
            response = view_func(self, request, *args, **kwargs)
            duration = time.time() - start_time
            
            # Log successful response
            response_data = {
                'view': self.__class__.__name__,
                'action': getattr(self, 'action', 'unknown'),
                'status_code': getattr(response, 'status_code', 'unknown'),
                'document_id': kwargs.get('pk') or kwargs.get('document_id'),
                'response_time_ms': round(duration * 1000, 2)
            }
            
            logger.info(
                f"API Response: {response.status_code} in {duration:.3f}s",
                extra=response_data,
                request=request
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log error response
            error_data = {
                'view': self.__class__.__name__,
                'action': getattr(self, 'action', 'unknown'),
                'error_type': type(e).__name__,
                'document_id': kwargs.get('pk') or kwargs.get('document_id'),
                'response_time_ms': round(duration * 1000, 2)
            }
            
            logger.error(
                f"API Error: {type(e).__name__} in {duration:.3f}s",
                extra=error_data,
                request=request,
                exc_info=True
            )
            
            raise
    
    return wrapper


# Pre-configured loggers for different modules
documents_logger = DocumentLogger('apps.documents')
ai_services_logger = DocumentLogger('apps.ai_services')
services_logger = DocumentLogger('apps.documents.services')


# Utility functions for common logging patterns
def log_document_operation(operation: str, document_id: str, user_uid: str, extra: Optional[Dict[str, Any]] = None):
    """Log document operations with consistent format."""
    log_data = {
        'operation': operation,
        'document_id': document_id,
        'user_uid': user_uid
    }
    if extra:
        log_data.update(extra)
    
    documents_logger.info(f"Document operation: {operation}", extra=log_data)


def log_ai_service_call(service: str, operation: str, duration: float, tokens_used: Optional[int] = None, extra: Optional[Dict[str, Any]] = None):
    """Log AI service calls with performance and usage metrics."""
    log_data = {
        'service': service,
        'operation': operation,
        'duration_ms': round(duration * 1000, 2),
        'tokens_used': tokens_used
    }
    if extra:
        log_data.update(extra)
    
    ai_services_logger.info(f"AI Service: {service}.{operation}", extra=log_data)


def log_storage_operation(operation: str, file_path: str, duration: float, file_size: Optional[int] = None, extra: Optional[Dict[str, Any]] = None):
    """Log storage operations with performance metrics."""
    log_data = {
        'operation': operation,
        'file_path': file_path,
        'duration_ms': round(duration * 1000, 2),
        'file_size_bytes': file_size
    }
    if extra:
        log_data.update(extra)
    
    services_logger.info(f"Storage operation: {operation}", extra=log_data)