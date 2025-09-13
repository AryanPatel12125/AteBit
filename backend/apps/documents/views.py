from rest_framework.decorators import api_view
from rest_framework.response import Response

# TODO: Implement document upload endpoint
# TODO: Add AI analysis trigger
# TODO: Add Firebase integration
# TODO: Add document CRUD operations
# TODO: Add user authentication

@api_view(['GET'])
def placeholder_view(request):
    return Response({
        'message': 'Document API endpoints – Coming Soon',
        'todo': [
            'Upload documents',
            'AI analysis',
            'Firebase storage', 
            'User authentication'
        ]
    })
