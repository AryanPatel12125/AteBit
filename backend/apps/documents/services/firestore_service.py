"""
Firebase Firestore service for document operations.
"""
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from django.conf import settings

# Import firestore only if not in test mode
if not (getattr(settings, 'TESTING', False) or os.environ.get('TESTING')):
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
else:
    # Mock firestore for testing
    from unittest.mock import Mock
    firestore = Mock()
    FieldFilter = Mock()

logger = logging.getLogger(__name__)


class FirestoreService:
    """
    Service class for Firebase Firestore operations.
    Handles document CRUD operations and user-scoped queries.
    """
    
    def __init__(self):
        """Initialize Firestore client with project settings."""
        # Skip authentication in test mode
        if getattr(settings, 'TESTING', False) or os.environ.get('TESTING'):
            from unittest.mock import Mock
            self.db = Mock()
        else:
            self.db = firestore.Client(project=settings.GOOGLE_CLOUD_PROJECT)
        self.collection_name = 'documents'
    
    def create_document(
        self,
        document_id: str,
        title: str,
        owner_uid: str,
        file_type: str,
        storage_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new document in Firestore.
        
        Args:
            document_id: Unique document identifier
            title: Document title
            owner_uid: Firebase user ID of document owner
            file_type: MIME type of original document
            storage_path: GCS path for original document
            **kwargs: Additional document fields
            
        Returns:
            Created document data
        """
        try:
            doc_data = {
                'document_id': document_id,
                'title': title,
                'owner_uid': owner_uid,
                'file_type': file_type,
                'storage_path': storage_path,
                'extracted_text': kwargs.get('extracted_text'),
                'language_code': kwargs.get('language_code'),
                'status': kwargs.get('status', 'PENDING'),
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
            }
            
            # Remove None values
            doc_data = {k: v for k, v in doc_data.items() if v is not None}
            
            doc_ref = self.db.collection(self.collection_name).document(document_id)
            doc_ref.set(doc_data)
            
            logger.info(f"Created document {document_id} for user {owner_uid}")
            return doc_data
            
        except Exception as e:
            logger.error(f"Failed to create document {document_id}: {str(e)}")
            raise FirestoreError(f"Failed to create document: {str(e)}")
    
    def get_document(self, document_id: str, owner_uid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID with owner validation.
        
        Args:
            document_id: Document identifier
            owner_uid: Firebase user ID for authorization
            
        Returns:
            Document data if found and authorized, None otherwise
        """
        try:
            doc_ref = self.db.collection(self.collection_name).document(document_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
                
            doc_data = doc.to_dict()
            
            # Verify ownership
            if doc_data.get('owner_uid') != owner_uid:
                logger.warning(f"Unauthorized access attempt to document {document_id} by user {owner_uid}")
                return None
                
            return doc_data
            
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {str(e)}")
            raise FirestoreError(f"Failed to retrieve document: {str(e)}")
    
    def update_document(
        self,
        document_id: str,
        owner_uid: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a document with owner validation.
        
        Args:
            document_id: Document identifier
            owner_uid: Firebase user ID for authorization
            updates: Fields to update
            
        Returns:
            True if updated successfully, False if not found/unauthorized
        """
        try:
            doc_ref = self.db.collection(self.collection_name).document(document_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
                
            doc_data = doc.to_dict()
            
            # Verify ownership
            if doc_data.get('owner_uid') != owner_uid:
                logger.warning(f"Unauthorized update attempt to document {document_id} by user {owner_uid}")
                return False
            
            # Add updated timestamp
            updates['updated_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref.update(updates)
            logger.info(f"Updated document {document_id} for user {owner_uid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {str(e)}")
            raise FirestoreError(f"Failed to update document: {str(e)}")
    
    def delete_document(self, document_id: str, owner_uid: str) -> bool:
        """
        Delete a document with owner validation.
        
        Args:
            document_id: Document identifier
            owner_uid: Firebase user ID for authorization
            
        Returns:
            True if deleted successfully, False if not found/unauthorized
        """
        try:
            doc_ref = self.db.collection(self.collection_name).document(document_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
                
            doc_data = doc.to_dict()
            
            # Verify ownership
            if doc_data.get('owner_uid') != owner_uid:
                logger.warning(f"Unauthorized delete attempt to document {document_id} by user {owner_uid}")
                return False
            
            doc_ref.delete()
            logger.info(f"Deleted document {document_id} for user {owner_uid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            raise FirestoreError(f"Failed to delete document: {str(e)}")
    
    def list_user_documents(
        self,
        owner_uid: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List documents for a specific user with pagination.
        
        Args:
            owner_uid: Firebase user ID
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of document data
        """
        try:
            query = (
                self.db.collection(self.collection_name)
                .where(filter=FieldFilter('owner_uid', '==', owner_uid))
                .order_by('updated_at', direction=firestore.Query.DESCENDING)
                .limit(limit)
                .offset(offset)
            )
            
            docs = query.stream()
            documents = [doc.to_dict() for doc in docs]
            
            logger.info(f"Retrieved {len(documents)} documents for user {owner_uid}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to list documents for user {owner_uid}: {str(e)}")
            raise FirestoreError(f"Failed to list documents: {str(e)}")
    
    def store_analysis_result(
        self,
        document_id: str,
        owner_uid: str,
        analysis_type: str,
        result: Dict[str, Any],
        version: int = 1
    ) -> bool:
        """
        Store AI analysis results for a document.
        
        Args:
            document_id: Document identifier
            owner_uid: Firebase user ID for authorization
            analysis_type: Type of analysis (summary, key_points, risks, translation)
            result: Analysis result data
            version: Analysis version number
            
        Returns:
            True if stored successfully, False if unauthorized
        """
        try:
            # Verify document ownership first
            if not self.get_document(document_id, owner_uid):
                return False
            
            analysis_data = {
                'document_id': document_id,
                'analysis_type': analysis_type,
                'result': result,
                'version': version,
                'created_at': firestore.SERVER_TIMESTAMP,
            }
            
            # Store in analyses subcollection
            analysis_ref = (
                self.db.collection(self.collection_name)
                .document(document_id)
                .collection('analyses')
                .document(f"{analysis_type}_v{version}")
            )
            
            analysis_ref.set(analysis_data)
            
            logger.info(f"Stored {analysis_type} analysis v{version} for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store analysis for document {document_id}: {str(e)}")
            raise FirestoreError(f"Failed to store analysis: {str(e)}")
    
    def get_analysis_result(
        self,
        document_id: str,
        owner_uid: str,
        analysis_type: str,
        version: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve analysis results for a document.
        
        Args:
            document_id: Document identifier
            owner_uid: Firebase user ID for authorization
            analysis_type: Type of analysis
            version: Specific version (latest if None)
            
        Returns:
            Analysis result data if found and authorized
        """
        try:
            # Verify document ownership first
            if not self.get_document(document_id, owner_uid):
                return None
            
            if version:
                # Get specific version
                analysis_ref = (
                    self.db.collection(self.collection_name)
                    .document(document_id)
                    .collection('analyses')
                    .document(f"{analysis_type}_v{version}")
                )
                
                analysis_doc = analysis_ref.get()
                if analysis_doc.exists:
                    return analysis_doc.to_dict()
            else:
                # Get latest version
                query = (
                    self.db.collection(self.collection_name)
                    .document(document_id)
                    .collection('analyses')
                    .where(filter=FieldFilter('analysis_type', '==', analysis_type))
                    .order_by('version', direction=firestore.Query.DESCENDING)
                    .limit(1)
                )
                
                docs = list(query.stream())
                if docs:
                    return docs[0].to_dict()
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get analysis for document {document_id}: {str(e)}")
            raise FirestoreError(f"Failed to retrieve analysis: {str(e)}")


class FirestoreError(Exception):
    """Custom exception for Firestore operations."""
    pass


# Global service instance - lazy loaded to avoid authentication issues during import
firestore_service = None

def get_firestore_service():
    """Get or create the global firestore service instance."""
    global firestore_service
    if firestore_service is None:
        firestore_service = FirestoreService()
    return firestore_service