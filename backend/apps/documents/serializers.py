"""
Serializers for document management API endpoints.
"""

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from typing import Dict, Any, List
import uuid

from .models import Document, Analysis, History


class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for Document CRUD operations.
    
    Handles document metadata serialization with proper validation
    for required fields and file types. Includes owner_uid scoping
    to ensure users can only access their own documents.
    
    Requirements: 1.1, 7.3
    """
    
    # Supported file types for document upload
    SUPPORTED_FILE_TYPES = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/msword',  # .doc
        'text/plain',  # .txt
    ]
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    class Meta:
        model = Document
        fields = [
            'document_id',
            'title', 
            'owner_uid',
            'file_type',
            'storage_path',
            'extracted_text',
            'language_code',
            'status',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'owner_uid',  # Set from request context
            'storage_path',  # Set during file upload
            'extracted_text',  # Set during text extraction
            'language_code',  # Set during AI analysis
            'created_at',
            'updated_at'
        ]
    
    def validate_document_id(self, value):
        """
        Validate that document_id is a valid UUID.
        """
        if not isinstance(value, uuid.UUID):
            try:
                uuid.UUID(str(value))
            except ValueError:
                raise ValidationError("document_id must be a valid UUID")
        return value
    
    def validate_title(self, value):
        """
        Validate document title is not empty and within length limits.
        """
        if not value or not value.strip():
            raise ValidationError("Title cannot be empty")
        
        if len(value.strip()) > 255:
            raise ValidationError("Title cannot exceed 255 characters")
            
        return value.strip()
    
    def validate_file_type(self, value):
        """
        Validate that file_type is supported.
        """
        if value not in self.SUPPORTED_FILE_TYPES:
            raise ValidationError(
                f"Unsupported file type: {value}. "
                f"Supported types: {', '.join(self.SUPPORTED_FILE_TYPES)}"
            )
        return value
    
    def validate_status(self, value):
        """
        Validate status is a valid choice.
        """
        if value not in [choice[0] for choice in Document.Status.choices]:
            raise ValidationError(f"Invalid status: {value}")
        return value
    
    def create(self, validated_data):
        """
        Create a new document with owner_uid from request context.
        """
        # Set owner_uid from authenticated user
        request = self.context.get('request')
        if request and hasattr(request, 'user_uid'):
            validated_data['owner_uid'] = request.user_uid
        else:
            raise ValidationError("Authentication required to create documents")
        
        # Generate storage path based on document_id and owner_uid
        document_id = validated_data['document_id']
        owner_uid = validated_data['owner_uid']
        file_extension = self._get_file_extension(validated_data.get('file_type', ''))
        validated_data['storage_path'] = f"documents/{owner_uid}/{document_id}/original{file_extension}"
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """
        Update document ensuring owner_uid scoping.
        """
        # Ensure user can only update their own documents
        request = self.context.get('request')
        if request and hasattr(request, 'user_uid'):
            if instance.owner_uid != request.user_uid:
                raise ValidationError("You can only update your own documents")
        
        # Don't allow changing document_id or owner_uid
        validated_data.pop('document_id', None)
        validated_data.pop('owner_uid', None)
        
        return super().update(instance, validated_data)
    
    def _get_file_extension(self, file_type: str) -> str:
        """
        Get file extension from MIME type.
        """
        extension_map = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/msword': '.doc',
            'text/plain': '.txt',
        }
        return extension_map.get(file_type, '')
    
    def to_representation(self, instance):
        """
        Customize serialized output.
        """
        data = super().to_representation(instance)
        
        # Don't expose extracted_text in list views for performance
        request = self.context.get('request')
        if request and request.resolver_match.url_name == 'document-list':
            data.pop('extracted_text', None)
        
        # Convert document_id to string for JSON serialization
        if 'document_id' in data:
            data['document_id'] = str(data['document_id'])
            
        return data


class DocumentListSerializer(DocumentSerializer):
    """
    Lightweight serializer for document list views.
    Excludes heavy fields like extracted_text for better performance.
    """
    
    class Meta(DocumentSerializer.Meta):
        fields = [
            'document_id',
            'title',
            'file_type', 
            'language_code',
            'status',
            'created_at',
            'updated_at'
        ]


class AnalysisSerializer(serializers.ModelSerializer):
    """
    Serializer for Analysis model to handle AI analysis results.
    """
    
    class Meta:
        model = Analysis
        fields = [
            'document_id',
            'version',
            'target_language',
            'summary',
            'key_points',
            'risk_alerts',
            'token_usage',
            'completion_time'
        ]
        read_only_fields = ['completion_time']
    
    def validate_target_language(self, value):
        """
        Validate target language is a valid ISO 639-1 code.
        """
        if value:
            # Common legal languages supported
            supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja']
            if value not in supported_languages:
                raise ValidationError(
                    f"Unsupported language: {value}. "
                    f"Supported languages: {', '.join(supported_languages)}"
                )
        return value
    
    def validate_summary(self, value):
        """
        Validate summary structure.
        """
        if not isinstance(value, dict):
            raise ValidationError("Summary must be a dictionary")
        
        # Ensure at least one language is present
        if not value:
            raise ValidationError("Summary cannot be empty")
            
        return value
    
    def validate_key_points(self, value):
        """
        Validate key points structure.
        """
        if not isinstance(value, list):
            raise ValidationError("Key points must be a list")
        
        required_fields = ['text', 'explanation', 'party_benefit', 'citation']
        for i, point in enumerate(value):
            if not isinstance(point, dict):
                raise ValidationError(f"Key point {i} must be a dictionary")
            
            for field in required_fields:
                if field not in point:
                    raise ValidationError(f"Key point {i} missing required field: {field}")
                    
            # Validate party_benefit values
            if point['party_benefit'] not in ['first_party', 'opposing_party', 'both']:
                raise ValidationError(f"Invalid party_benefit in key point {i}")
                
        return value
    
    def validate_risk_alerts(self, value):
        """
        Validate risk alerts structure.
        """
        if not isinstance(value, list):
            raise ValidationError("Risk alerts must be a list")
        
        required_fields = ['severity', 'clause', 'rationale', 'location']
        valid_severities = ['HIGH', 'MEDIUM', 'LOW']
        
        for i, risk in enumerate(value):
            if not isinstance(risk, dict):
                raise ValidationError(f"Risk alert {i} must be a dictionary")
            
            for field in required_fields:
                if field not in risk:
                    raise ValidationError(f"Risk alert {i} missing required field: {field}")
            
            if risk['severity'] not in valid_severities:
                raise ValidationError(f"Invalid severity in risk alert {i}: {risk['severity']}")
                
        return value
    
    def to_representation(self, instance):
        """
        Customize serialized output.
        """
        data = super().to_representation(instance)
        
        # Convert document_id to string
        if 'document_id' in data:
            data['document_id'] = str(data['document_id'])
            
        return data


class HistorySerializer(serializers.ModelSerializer):
    """
    Serializer for History model to track document actions.
    """
    
    class Meta:
        model = History
        fields = [
            'document_id',
            'action',
            'actor_uid',
            'version',
            'payload',
            'timestamp'
        ]
        read_only_fields = ['timestamp']
    
    def to_representation(self, instance):
        """
        Customize serialized output.
        """
        data = super().to_representation(instance)
        
        # Convert document_id to string
        if 'document_id' in data:
            data['document_id'] = str(data['document_id'])
            
        return data


class DocumentUploadSerializer(serializers.Serializer):
    """
    Serializer for document file upload validation.
    
    Handles file upload validation including file type checking,
    size limits, and MIME type validation for document processing.
    
    Requirements: 1.2, 1.4, 8.2
    """
    
    file = serializers.FileField(
        help_text="Document file to upload (PDF, DOCX, TXT)"
    )
    
    # Supported file types
    SUPPORTED_MIME_TYPES = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/msword',  # .doc
        'text/plain',  # .txt
    ]
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt']
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def validate_file(self, value):
        """
        Validate uploaded file type, size, and content.
        """
        if not value:
            raise ValidationError("No file provided")
        
        # Check file size
        if value.size > self.MAX_FILE_SIZE:
            raise ValidationError(
                f"File size ({value.size} bytes) exceeds maximum allowed size "
                f"({self.MAX_FILE_SIZE} bytes / 10MB)"
            )
        
        # Check file extension
        file_name = value.name.lower()
        if not any(file_name.endswith(ext) for ext in self.SUPPORTED_EXTENSIONS):
            raise ValidationError(
                f"Unsupported file extension. Supported extensions: "
                f"{', '.join(self.SUPPORTED_EXTENSIONS)}"
            )
        
        # Check MIME type if available
        if hasattr(value, 'content_type') and value.content_type:
            if value.content_type not in self.SUPPORTED_MIME_TYPES:
                raise ValidationError(
                    f"Unsupported file type: {value.content_type}. "
                    f"Supported types: {', '.join(self.SUPPORTED_MIME_TYPES)}"
                )
        
        # Basic file content validation
        try:
            # Read first few bytes to ensure file is readable
            value.seek(0)
            first_bytes = value.read(1024)
            value.seek(0)  # Reset file pointer
            
            if not first_bytes:
                raise ValidationError("File appears to be empty")
                
        except Exception as e:
            raise ValidationError(f"Error reading file: {str(e)}")
        
        return value
    
    def validate(self, attrs):
        """
        Additional cross-field validation.
        """
        file = attrs.get('file')
        
        if file:
            # Ensure file name is reasonable
            if len(file.name) > 255:
                raise ValidationError("File name too long (max 255 characters)")
            
            # Check for potentially malicious file names
            dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
            if any(char in file.name for char in dangerous_chars):
                raise ValidationError("File name contains invalid characters")
        
        return attrs


class AnalysisRequestSerializer(serializers.Serializer):
    """
    Serializer for AI analysis request parameters.
    
    Handles validation of analysis request parameters including
    analysis types, target languages, and processing options.
    
    Requirements: 2.3, 3.3, 4.4, 5.4
    """
    
    # Analysis types that can be requested
    ANALYSIS_TYPES = [
        'summary',      # Document summarization
        'key_points',   # Key points extraction
        'risks',        # Risk and clause analysis
        'translation',  # Multi-language translation
        'all'          # All analysis types
    ]
    
    # Supported target languages for translation
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'es': 'Spanish', 
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'zh': 'Chinese',
        'ja': 'Japanese'
    }
    
    analysis_type = serializers.ChoiceField(
        choices=[(t, t.title()) for t in ANALYSIS_TYPES],
        default='summary',
        help_text="Type of analysis to perform"
    )
    
    target_language = serializers.ChoiceField(
        choices=[(code, name) for code, name in SUPPORTED_LANGUAGES.items()],
        required=False,
        allow_null=True,
        help_text="Target language for translation (ISO 639-1 code)"
    )
    
    include_original = serializers.BooleanField(
        default=True,
        help_text="Include original language content in response"
    )
    
    max_summary_length = serializers.IntegerField(
        default=500,
        min_value=100,
        max_value=2000,
        help_text="Maximum length for summary in words"
    )
    
    max_key_points = serializers.IntegerField(
        default=10,
        min_value=3,
        max_value=20,
        help_text="Maximum number of key points to extract"
    )
    
    risk_threshold = serializers.ChoiceField(
        choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')],
        default='MEDIUM',
        help_text="Minimum risk severity to include in results"
    )
    
    def validate(self, attrs):
        """
        Cross-field validation for analysis parameters.
        """
        analysis_type = attrs.get('analysis_type')
        target_language = attrs.get('target_language')
        
        # Translation requires target language
        if analysis_type in ['translation', 'all'] and not target_language:
            raise ValidationError(
                "target_language is required for translation analysis"
            )
        
        # Validate language combination
        if target_language:
            # For now, we assume source language detection will happen
            # Could add source_language validation here if needed
            pass
        
        return attrs
    
    def to_internal_value(self, data):
        """
        Convert input data to internal representation.
        """
        # Handle legacy analysis_types parameter (array)
        if 'analysis_types' in data and 'analysis_type' not in data:
            analysis_types = data.get('analysis_types', [])
            if isinstance(analysis_types, list) and analysis_types:
                # Convert array to single type or 'all'
                if len(analysis_types) > 1 or 'all' in analysis_types:
                    data['analysis_type'] = 'all'
                else:
                    data['analysis_type'] = analysis_types[0]
        
        return super().to_internal_value(data)


class AnalysisResultSerializer(serializers.Serializer):
    """
    Serializer for structured AI analysis output.
    
    Handles serialization of AI analysis results including summaries,
    key points, risk alerts, and translation data with proper structure
    validation and formatting.
    
    Requirements: 2.3, 3.3, 4.4, 5.4
    """
    
    document_id = serializers.UUIDField(
        help_text="UUID of the analyzed document"
    )
    
    version = serializers.IntegerField(
        help_text="Analysis version number"
    )
    
    detected_language = serializers.CharField(
        max_length=10,
        help_text="Detected source language (ISO 639-1)"
    )
    
    target_language = serializers.CharField(
        max_length=10,
        required=False,
        allow_null=True,
        help_text="Target language for translation (ISO 639-1)"
    )
    
    summary = serializers.DictField(
        child=serializers.CharField(),
        help_text="Summary in multiple languages: {'en': 'text', 'es': 'texto'}"
    )
    
    key_points = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Key points with party analysis"
    )
    
    risk_alerts = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Risk alerts with severity classification"
    )
    
    token_usage = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Token usage statistics"
    )
    
    confidence = serializers.FloatField(
        min_value=0.0,
        max_value=1.0,
        required=False,
        help_text="Analysis confidence score"
    )
    
    completion_time = serializers.DateTimeField(
        help_text="Analysis completion timestamp"
    )
    
    def validate_summary(self, value):
        """
        Validate summary structure and content.
        """
        if not isinstance(value, dict):
            raise ValidationError("Summary must be a dictionary")
        
        if not value:
            raise ValidationError("Summary cannot be empty")
        
        # Ensure all values are strings
        for lang, text in value.items():
            if not isinstance(text, str):
                raise ValidationError(f"Summary text for language '{lang}' must be a string")
            
            if not text.strip():
                raise ValidationError(f"Summary text for language '{lang}' cannot be empty")
        
        return value
    
    def validate_key_points(self, value):
        """
        Validate key points structure.
        """
        if not isinstance(value, list):
            raise ValidationError("Key points must be a list")
        
        required_fields = ['text', 'explanation', 'party_benefit', 'citation']
        valid_party_benefits = ['first_party', 'opposing_party', 'both']
        
        for i, point in enumerate(value):
            if not isinstance(point, dict):
                raise ValidationError(f"Key point {i} must be a dictionary")
            
            # Check required fields
            for field in required_fields:
                if field not in point:
                    raise ValidationError(f"Key point {i} missing required field: {field}")
                
                if not isinstance(point[field], str) or not point[field].strip():
                    raise ValidationError(f"Key point {i} field '{field}' must be a non-empty string")
            
            # Validate party_benefit
            if point['party_benefit'] not in valid_party_benefits:
                raise ValidationError(
                    f"Key point {i} has invalid party_benefit: {point['party_benefit']}. "
                    f"Must be one of: {', '.join(valid_party_benefits)}"
                )
        
        return value
    
    def validate_risk_alerts(self, value):
        """
        Validate risk alerts structure.
        """
        if not isinstance(value, list):
            raise ValidationError("Risk alerts must be a list")
        
        required_fields = ['severity', 'clause', 'rationale', 'location']
        valid_severities = ['HIGH', 'MEDIUM', 'LOW']
        
        for i, risk in enumerate(value):
            if not isinstance(risk, dict):
                raise ValidationError(f"Risk alert {i} must be a dictionary")
            
            # Check required fields
            for field in required_fields:
                if field not in risk:
                    raise ValidationError(f"Risk alert {i} missing required field: {field}")
                
                if not isinstance(risk[field], str) or not risk[field].strip():
                    raise ValidationError(f"Risk alert {i} field '{field}' must be a non-empty string")
            
            # Validate severity
            if risk['severity'] not in valid_severities:
                raise ValidationError(
                    f"Risk alert {i} has invalid severity: {risk['severity']}. "
                    f"Must be one of: {', '.join(valid_severities)}"
                )
        
        return value
    
    def validate_token_usage(self, value):
        """
        Validate token usage structure.
        """
        if not isinstance(value, dict):
            raise ValidationError("Token usage must be a dictionary")
        
        required_fields = ['input_tokens', 'output_tokens']
        
        for field in required_fields:
            if field not in value:
                raise ValidationError(f"Token usage missing required field: {field}")
            
            if not isinstance(value[field], int) or value[field] < 0:
                raise ValidationError(f"Token usage field '{field}' must be a non-negative integer")
        
        return value
    
    def to_representation(self, instance):
        """
        Customize serialized output.
        """
        data = super().to_representation(instance)
        
        # Convert document_id to string for JSON serialization
        if 'document_id' in data:
            data['document_id'] = str(data['document_id'])
        
        # Add computed fields
        if 'token_usage' in data and isinstance(data['token_usage'], dict):
            data['total_tokens'] = sum(data['token_usage'].values())
        
        # Format completion_time
        if 'completion_time' in data:
            # DRF handles datetime serialization automatically
            pass
        
        return data


class DocumentAnalysisSerializer(serializers.Serializer):
    """
    Combined serializer for document with its latest analysis.
    Used for endpoints that return document metadata along with analysis results.
    """
    
    document = DocumentSerializer(read_only=True)
    analysis = AnalysisResultSerializer(read_only=True, allow_null=True)
    
    def to_representation(self, instance):
        """
        Handle representation for document with analysis.
        """
        if isinstance(instance, Document):
            # Get latest analysis for the document
            try:
                latest_analysis = Analysis.objects.filter(
                    document_id=instance.document_id
                ).order_by('-version').first()
            except Analysis.DoesNotExist:
                latest_analysis = None
            
            return {
                'document': DocumentSerializer(instance, context=self.context).data,
                'analysis': AnalysisResultSerializer(latest_analysis, context=self.context).data if latest_analysis else None
            }
        
        return super().to_representation(instance)