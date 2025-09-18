"""
Custom permission classes for document management.
"""
from rest_framework import permissions


class IsDocumentOwner(permissions.BasePermission):
    """
    Custom permission to ensure users can only access their own documents.
    
    This permission class checks that:
    1. The user is authenticated (has user_uid from Firebase)
    2. The user owns the document being accessed
    
    Used by document API views to enforce owner-based access control.
    """
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated with Firebase.
        
        Args:
            request: The HTTP request object
            view: The view being accessed
            
        Returns:
            bool: True if user is authenticated, False otherwise
        """
        return hasattr(request, 'user_uid') and request.user_uid
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user owns the document.
        
        Args:
            request: The HTTP request object
            view: The view being accessed
            obj: The document object being accessed
            
        Returns:
            bool: True if user owns the document, False otherwise
        """
        if hasattr(obj, 'owner_uid'):
            return obj.owner_uid == request.user_uid
        return False


class IsAuthenticated(permissions.BasePermission):
    """
    Custom permission to require valid Firebase authentication.
    
    This is similar to DRF's IsAuthenticated but specifically
    checks for Firebase user_uid on the request.
    """
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated with Firebase.
        
        Args:
            request: The HTTP request object
            view: The view being accessed
            
        Returns:
            bool: True if user is authenticated, False otherwise
        """
        return hasattr(request, 'user_uid') and request.user_uid