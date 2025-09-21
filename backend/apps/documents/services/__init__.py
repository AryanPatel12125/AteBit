"""
Service layer initialization with lazy loading for testing.
"""

# Lazy-loaded service instances to avoid authentication during import
_firestore_service = None
_gcs_service = None
_vertex_client = None


def get_firestore_service():
    """Get or create the global firestore service instance."""
    global _firestore_service
    if _firestore_service is None:
        from .firestore_service import FirestoreService
        _firestore_service = FirestoreService()
    return _firestore_service


def get_gcs_service():
    """Get or create the global GCS service instance."""
    global _gcs_service
    if _gcs_service is None:
        from .gcs_service import GCSService
        _gcs_service = GCSService()
    return _gcs_service


def get_vertex_client():
    """Get or create the global Vertex AI client instance."""
    global _vertex_client
    if _vertex_client is None:
        from apps.ai_services.vertex_client import VertexAIClient
        _vertex_client = VertexAIClient()
    return _vertex_client


# For backward compatibility, provide the service instances
# These will be lazy-loaded when first accessed
class LazyServiceProxy:
    """Proxy that lazy-loads services on first access."""
    
    def __init__(self, getter_func):
        self._getter = getter_func
        self._service = None
    
    def __getattr__(self, name):
        if self._service is None:
            self._service = self._getter()
        return getattr(self._service, name)


# Create lazy proxies for backward compatibility
firestore_service = LazyServiceProxy(get_firestore_service)
gcs_service = LazyServiceProxy(get_gcs_service)
vertex_client = LazyServiceProxy(get_vertex_client)