"""
Models for document storage, analysis results, and history tracking.
"""

from django.db import models
from django.core.validators import MinLengthValidator
from typing import Dict, Any, List

class Document(models.Model):
    """
    Model representing a legal document and its metadata.
    
    Attributes:
        title: Document title/name
        owner_uid: Firebase user ID of document owner
        file_type: MIME type of original document
        storage_path: GCS path for original document
        extracted_text: Plain text extracted from document
        language_code: Detected document language (ISO 639-1)
        created_at: Timestamp of document creation
        updated_at: Timestamp of last update
        status: Current processing status
    """
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Processing'
        PROCESSING = 'PROCESSING', 'Processing'
        ANALYZED = 'ANALYZED', 'Analysis Complete'
        ERROR = 'ERROR', 'Processing Error'
    
    title = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(1)]
    )
    owner_uid = models.CharField(
        max_length=128,
        db_index=True,
        help_text="Firebase user ID"
    )
    file_type = models.CharField(
        max_length=128,
        help_text="MIME type of original document"
    )
    storage_path = models.CharField(
        max_length=512,
        help_text="GCS path to original document"
    )
    extracted_text = models.TextField(
        null=True,
        blank=True,
        help_text="Plain text extracted from document"
    )
    language_code = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="ISO 639-1 language code"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['owner_uid', '-updated_at'])
        ]
    
    def __str__(self) -> str:
        return f"{self.title} ({self.status})"

class Analysis(models.Model):
    """
    Model storing AI analysis results for a document.
    
    Attributes:
        document: Related Document instance
        version: Analysis version number
        target_language: Target language for translations (ISO 639-1)
        summary: Plain language summary
        key_points: Extracted key points with citations
        risk_alerts: Detected risks and compliance issues
        token_usage: LLM token usage statistics
        completion_time: Analysis completion timestamp
    """
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='analyses'
    )
    version = models.PositiveIntegerField()
    target_language = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="ISO 639-1 target language code"
    )
    summary = models.JSONField(
        help_text="Summary in simple language",
        default=dict
    )
    key_points = models.JSONField(
        help_text="Key points with citations",
        default=list
    )
    risk_alerts = models.JSONField(
        help_text="Risk and compliance alerts",
        default=list
    )
    token_usage = models.JSONField(
        help_text="LLM token usage stats",
        default=dict
    )
    completion_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-version']
        unique_together = ['document', 'version']
        indexes = [
            models.Index(fields=['document', '-version'])
        ]
    
    def __str__(self) -> str:
        return f"Analysis v{self.version} for {self.document.title}"
    
    @property
    def summary_text(self) -> str:
        """Get the summary text in the target or original language."""
        if self.target_language and self.target_language in self.summary:
            return self.summary[self.target_language]
        return self.summary.get('en', '')  # Default to English
    
    @property
    def total_tokens(self) -> int:
        """Get total tokens used for this analysis."""
        return sum(self.token_usage.values())

class History(models.Model):
    """
    Model tracking document history and user actions.
    
    Attributes:
        document: Related Document instance
        action: Type of action performed
        actor_uid: Firebase user ID who performed action
        version: Analysis version (if applicable)
        payload: Additional action-specific data
        timestamp: When action occurred
    """
    
    class Action(models.TextChoices):
        CREATED = 'CREATED', 'Document Created'
        UPLOADED = 'UPLOADED', 'File Uploaded'
        ANALYZED = 'ANALYZED', 'Analysis Completed'
        REPORT_GENERATED = 'REPORT', 'Report Generated'
        DOWNLOADED = 'DOWNLOADED', 'Report Downloaded'
        ERROR = 'ERROR', 'Error Occurred'
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='history'
    )
    action = models.CharField(
        max_length=20,
        choices=Action.choices
    )
    actor_uid = models.CharField(
        max_length=128,
        help_text="Firebase user ID"
    )
    version = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    payload = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional action data"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['document', '-timestamp'])
        ]
    
    def __str__(self) -> str:
        return f"{self.action} on {self.document.title} by {self.actor_uid}"
    
    @classmethod
    def log_action(
        cls,
        document: Document,
        action: Action,
        actor_uid: str,
        version: int = None,
        payload: Dict[str, Any] = None
    ) -> 'History':
        """
        Create a new history entry.
        
        Args:
            document: The document the action was performed on
            action: Type of action from Action choices
            actor_uid: Firebase user ID who performed action
            version: Optional analysis version number
            payload: Optional additional data about the action
            
        Returns:
            New History instance
        """
        return cls.objects.create(
            document=document,
            action=action,
            actor_uid=actor_uid,
            version=version,
            payload=payload
        )
