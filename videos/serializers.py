"""
Serializers for video upload pipeline.
"""
from rest_framework import serializers
from videos.models import Video, VideoUploadStatus


class VideoCreateSerializer(serializers.Serializer):
    """
    Serializer for initiating a video upload.
    Returns a pre-signed URL for direct S3 upload.
    """
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    filename = serializers.CharField(max_length=255)
    file_size = serializers.IntegerField(min_value=1)
    content_type = serializers.ChoiceField(
        choices=[
            ('video/mp4', 'MP4'),
            ('video/webm', 'WebM'),
            ('video/quicktime', 'QuickTime'),
            ('video/x-msvideo', 'AVI'),
            ('video/x-matroska', 'MKV'),
        ],
        default='video/mp4'
    )
    youtube_privacy = serializers.ChoiceField(
        choices=[('private', 'Private'), ('unlisted', 'Unlisted'), ('public', 'Public')],
        default='unlisted'
    )
    course_content_id = serializers.IntegerField(required=False, allow_null=True)
    duration_seconds = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_file_size(self, value):
        """Validate file size (max 2GB by default)"""
        max_size = 2 * 1024 * 1024 * 1024  # 2GB
        if value > max_size:
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed ({max_size // (1024**3)}GB)"
            )
        return value
    
    def validate_filename(self, value):
        """Validate filename extension"""
        allowed_extensions = ['mp4', 'webm', 'mov', 'avi', 'mkv']
        ext = value.rsplit('.', 1)[-1].lower() if '.' in value else ''
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
            )
        return value


class PresignedUrlResponseSerializer(serializers.Serializer):
    """Response serializer for presigned URL generation"""
    video_id = serializers.UUIDField()
    upload_url = serializers.URLField()
    s3_key = serializers.CharField()
    expires_in = serializers.IntegerField(help_text="URL expiry in seconds")
    fields = serializers.DictField(
        required=False,
        help_text="Additional fields for multipart upload (if applicable)"
    )


class VideoConfirmUploadSerializer(serializers.Serializer):
    """Serializer for confirming S3 upload completion"""
    video_id = serializers.UUIDField()


class VideoSerializer(serializers.ModelSerializer):
    """Full video serializer for detail views"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)
    embed_url = serializers.CharField(read_only=True)
    is_ready = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Video
        fields = [
            'id',
            'title',
            'description',
            'status',
            'original_filename',
            'file_size',
            'content_type',
            'youtube_video_id',
            'youtube_url',
            'youtube_privacy',
            'youtube_upload_progress',
            'embed_url',
            'is_ready',
            'duration_seconds',
            'error_message',
            'uploaded_by',
            'uploaded_by_name',
            'course_content',
            'created_at',
            'updated_at',
            's3_uploaded_at',
            'youtube_uploaded_at',
        ]
        read_only_fields = [
            'id', 'status', 's3_key', 's3_bucket', 'youtube_video_id',
            'youtube_url', 'youtube_upload_progress', 'error_message',
            'uploaded_by', 'created_at', 'updated_at', 's3_uploaded_at',
            'youtube_uploaded_at', 'celery_task_id', 'retry_count'
        ]


class VideoListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)
    is_ready = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Video
        fields = [
            'id',
            'title',
            'status',
            'youtube_video_id',
            'youtube_upload_progress',
            'is_ready',
            'duration_seconds',
            'uploaded_by_name',
            'created_at',
        ]


class VideoStatusSerializer(serializers.ModelSerializer):
    """Minimal serializer for status polling"""
    is_ready = serializers.BooleanField(read_only=True)
    embed_url = serializers.CharField(read_only=True)
    
    class Meta:
        model = Video
        fields = [
            'id',
            'status',
            'youtube_video_id',
            'youtube_url',
            'youtube_upload_progress',
            'is_ready',
            'embed_url',
            'error_message',
        ]


class VideoUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating video metadata"""
    
    class Meta:
        model = Video
        fields = [
            'title',
            'description',
            'youtube_privacy',
            'course_content',
        ]


class RetryUploadSerializer(serializers.Serializer):
    """Serializer for retrying a failed upload"""
    video_id = serializers.UUIDField()

