"""
Admin configuration for videos app.
"""
from django.contrib import admin
from videos.models import Video, YouTubeCredential


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'status',
        'youtube_video_id',
        'uploaded_by',
        'created_at',
    ]
    list_filter = [
        'status',
        'youtube_privacy',
        'created_at',
    ]
    search_fields = [
        'title',
        'description',
        'youtube_video_id',
        'uploaded_by__full_name',
        'uploaded_by__username',
    ]
    readonly_fields = [
        'id',
        's3_key',
        's3_bucket',
        'youtube_video_id',
        'youtube_url',
        'youtube_upload_progress',
        'celery_task_id',
        'created_at',
        'updated_at',
        's3_uploaded_at',
        'youtube_uploaded_at',
    ]
    raw_id_fields = ['uploaded_by', 'course_content']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'title', 'description', 'uploaded_by', 'course_content')
        }),
        ('Status', {
            'fields': ('status', 'error_message', 'retry_count', 'celery_task_id')
        }),
        ('S3 Storage', {
            'fields': ('s3_key', 's3_bucket', 'original_filename', 'file_size', 'content_type')
        }),
        ('YouTube', {
            'fields': (
                'youtube_video_id', 'youtube_url', 'youtube_privacy',
                'youtube_upload_progress', 'duration_seconds'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 's3_uploaded_at', 'youtube_uploaded_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(YouTubeCredential)
class YouTubeCredentialAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'channel_title',
        'is_active',
        'daily_quota_used',
        'updated_at',
    ]
    list_filter = ['is_active']
    search_fields = ['name', 'channel_title', 'channel_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'channel_id', 'channel_title', 'is_active')
        }),
        ('OAuth Tokens', {
            'fields': ('access_token', 'refresh_token', 'token_expiry'),
            'classes': ('collapse',),
            'description': 'These tokens should be encrypted in production.'
        }),
        ('Quota Tracking', {
            'fields': ('daily_quota_used', 'quota_reset_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
