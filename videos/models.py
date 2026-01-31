"""
Video models for production-grade YouTube upload pipeline.

Architecture:
1. Frontend → S3 (presigned URL) - Direct upload to object storage
2. Backend → Celery task → YouTube (resumable upload)
3. Track status throughout the pipeline
"""
import uuid
from django.db import models
from django.core.validators import FileExtensionValidator
from accounts.models import User
from courses.models import CourseContent


class VideoUploadStatus(models.TextChoices):
    """Status choices for video upload pipeline"""
    PENDING = 'pending', 'Pending Upload'
    UPLOADING_S3 = 'uploading_s3', 'Uploading to Storage'
    S3_COMPLETE = 's3_complete', 'Storage Upload Complete'
    QUEUED = 'queued', 'Queued for YouTube Upload'
    UPLOADING_YOUTUBE = 'uploading_youtube', 'Uploading to YouTube'
    PROCESSING = 'processing', 'YouTube Processing'
    READY = 'ready', 'Ready'
    FAILED = 'failed', 'Failed'


class Video(models.Model):
    """
    Video model tracking the entire upload pipeline.
    
    Flow:
    1. Created with PENDING status
    2. Frontend gets presigned URL, status → UPLOADING_S3
    3. Frontend confirms upload complete, status → S3_COMPLETE
    4. Celery task queued, status → QUEUED
    5. Task starts YouTube upload, status → UPLOADING_YOUTUBE
    6. YouTube processes, status → PROCESSING
    7. Video ready, status → READY
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Metadata
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # S3/Object Storage
    s3_key = models.CharField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text="Object storage key (path) for the video file"
    )
    s3_bucket = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="S3 bucket name"
    )
    original_filename = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Original filename from upload"
    )
    file_size = models.BigIntegerField(
        blank=True,
        null=True,
        help_text="File size in bytes"
    )
    content_type = models.CharField(
        max_length=100,
        default='video/mp4',
        help_text="MIME type of the video"
    )
    
    # YouTube
    youtube_video_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        help_text="YouTube video ID after successful upload"
    )
    youtube_url = models.URLField(
        blank=True,
        null=True,
        help_text="Full YouTube URL for embedding"
    )
    youtube_privacy = models.CharField(
        max_length=20,
        default='unlisted',
        choices=[
            ('private', 'Private'),
            ('unlisted', 'Unlisted'),
            ('public', 'Public'),
        ],
        help_text="YouTube video privacy status"
    )
    youtube_upload_progress = models.IntegerField(
        default=0,
        help_text="Upload progress percentage (0-100)"
    )
    
    # Status tracking
    status = models.CharField(
        max_length=30,
        choices=VideoUploadStatus.choices,
        default=VideoUploadStatus.PENDING,
        db_index=True
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error details if upload failed"
    )
    retry_count = models.IntegerField(
        default=0,
        help_text="Number of upload retry attempts"
    )
    
    # Celery task tracking
    celery_task_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Celery task ID for tracking"
    )
    
    # Duration (set after YouTube processing or from frontend metadata)
    duration_seconds = models.IntegerField(
        blank=True,
        null=True,
        help_text="Video duration in seconds"
    )
    
    # Relationships
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_videos'
    )
    course_content = models.OneToOneField(
        CourseContent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='video',
        help_text="Associated course content (if any)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    s3_uploaded_at = models.DateTimeField(blank=True, null=True)
    youtube_uploaded_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['uploaded_by', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.status})"
    
    @property
    def is_ready(self) -> bool:
        return self.status == VideoUploadStatus.READY
    
    @property
    def embed_url(self) -> str | None:
        """Return YouTube embed URL if available"""
        if self.youtube_video_id:
            return f"https://www.youtube.com/embed/{self.youtube_video_id}"
        return None
    
    def mark_failed(self, error_message: str):
        """Mark video upload as failed with error details"""
        self.status = VideoUploadStatus.FAILED
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count', 'updated_at'])


class YouTubeCredential(models.Model):
    """
    Store YouTube OAuth credentials (channel-level, not per-user).
    
    Security:
    - Tokens are encrypted at rest (handled by application layer)
    - Only backend has access to these credentials
    - Frontend never touches OAuth secrets
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Identifier for this credential set (e.g., 'main_channel')"
    )
    channel_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="YouTube channel ID"
    )
    channel_title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="YouTube channel name"
    )
    
    # OAuth tokens (encrypted in production)
    access_token = models.TextField(
        help_text="OAuth access token (encrypted)"
    )
    refresh_token = models.TextField(
        help_text="OAuth refresh token (encrypted)"
    )
    token_expiry = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the access token expires"
    )
    
    # Quota tracking
    daily_quota_used = models.IntegerField(
        default=0,
        help_text="API quota units used today"
    )
    quota_reset_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date when quota was last reset"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this credential is active for uploads"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "YouTube Credential"
        verbose_name_plural = "YouTube Credentials"
    
    def __str__(self):
        return f"{self.name} ({self.channel_title or 'Unknown Channel'})"
