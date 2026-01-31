"""
Views for video upload pipeline.

Endpoints:
1. POST /videos/initiate-upload/ - Get presigned URL for S3 upload
2. POST /videos/confirm-upload/ - Confirm S3 upload, queue YouTube upload
3. GET /videos/{id}/status/ - Poll video status
4. GET /videos/ - List videos
5. GET /videos/{id}/ - Video details
6. POST /videos/{id}/retry/ - Retry failed upload
"""
import logging
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from accounts.permissions import HasPermissionCode
from videos.models import Video, VideoUploadStatus
from videos.serializers import (
    VideoCreateSerializer,
    PresignedUrlResponseSerializer,
    VideoConfirmUploadSerializer,
    VideoSerializer,
    VideoListSerializer,
    VideoStatusSerializer,
    VideoUpdateSerializer,
    RetryUploadSerializer,
)

logger = logging.getLogger(__name__)


class InitiateUploadView(APIView):
    """
    Initiate video upload by generating a pre-signed URL for direct S3 upload.
    
    Flow:
    1. Client sends video metadata (title, filename, size, etc.)
    2. Server creates Video record with PENDING status
    3. Server generates pre-signed S3 URL
    4. Client uses URL to upload directly to S3
    """
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "VIDEO_UPLOAD"
    
    @extend_schema(
        request=VideoCreateSerializer,
        responses={
            201: PresignedUrlResponseSerializer,
            400: OpenApiResponse(description="Invalid input"),
            403: OpenApiResponse(description="Permission denied"),
        },
        summary="Initiate video upload",
        description="Generate a pre-signed URL for direct browser-to-S3 upload",
    )
    def post(self, request):
        serializer = VideoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Create video record
        video = Video.objects.create(
            title=data['title'],
            description=data.get('description', ''),
            original_filename=data['filename'],
            file_size=data['file_size'],
            content_type=data['content_type'],
            youtube_privacy=data.get('youtube_privacy', 'unlisted'),
            duration_seconds=data.get('duration_seconds'),
            status=VideoUploadStatus.PENDING,
            uploaded_by=request.user,
        )
        
        # Link to course content if provided
        if data.get('course_content_id'):
            from courses.models import CourseContent
            try:
                content = CourseContent.objects.get(id=data['course_content_id'])
                video.course_content = content
                video.save(update_fields=['course_content'])
            except CourseContent.DoesNotExist:
                pass
        
        # Generate presigned URL
        try:
            from videos.services.s3_service import S3Service
            s3_service = S3Service()
            result = s3_service.generate_presigned_url(
                video_id=str(video.id),
                filename=data['filename'],
                content_type=data['content_type'],
                file_size=data['file_size'],
            )
            
            # Update video with S3 info
            video.s3_key = result.s3_key
            video.s3_bucket = result.bucket
            video.status = VideoUploadStatus.UPLOADING_S3
            video.save(update_fields=['s3_key', 's3_bucket', 'status', 'updated_at'])
            
            logger.info(
                f"Initiated upload for video {video.id} by user {request.user.id}"
            )
            
            response_data = {
                'video_id': video.id,
                'upload_url': result.upload_url,
                's3_key': result.s3_key,
                'expires_in': result.expires_in,
            }
            
            if result.fields:
                response_data['fields'] = result.fields
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            video.delete()
            return Response(
                {'error': 'Failed to generate upload URL'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConfirmUploadView(APIView):
    """
    Confirm that S3 upload is complete and queue YouTube upload.
    
    Flow:
    1. Client finishes uploading to S3
    2. Client calls this endpoint
    3. Server verifies S3 upload
    4. Server queues Celery task for YouTube upload
    """
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "VIDEO_UPLOAD"
    
    @extend_schema(
        request=VideoConfirmUploadSerializer,
        responses={
            200: VideoStatusSerializer,
            400: OpenApiResponse(description="Invalid video ID or upload not complete"),
            404: OpenApiResponse(description="Video not found"),
        },
        summary="Confirm S3 upload complete",
        description="Confirm upload and queue YouTube processing",
    )
    def post(self, request):
        serializer = VideoConfirmUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        video_id = serializer.validated_data['video_id']
        
        try:
            video = Video.objects.get(
                id=video_id,
                uploaded_by=request.user,  # Ensure user owns the video
            )
        except Video.DoesNotExist:
            return Response(
                {'error': 'Video not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify video is in correct state
        if video.status not in [VideoUploadStatus.UPLOADING_S3, VideoUploadStatus.PENDING]:
            return Response(
                {'error': f'Invalid video status: {video.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Optionally verify S3 upload (can be disabled for performance)
        try:
            from videos.services.s3_service import S3Service
            s3_service = S3Service()
            if not s3_service.check_object_exists(video.s3_key):
                return Response(
                    {'error': 'S3 upload not found. Please complete upload first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update file size from S3 if not set
            if not video.file_size:
                video.file_size = s3_service.get_object_size(video.s3_key)
        except Exception as e:
            logger.warning(f"S3 verification failed for {video_id}: {e}")
            # Continue anyway - S3 may be temporarily unavailable
        
        # Update status and queue task
        video.status = VideoUploadStatus.QUEUED
        video.s3_uploaded_at = timezone.now()
        video.save(update_fields=['status', 's3_uploaded_at', 'file_size', 'updated_at'])
        
        # Queue YouTube upload task
        from videos.tasks import upload_to_youtube_task
        task = upload_to_youtube_task.delay(
            video_id=str(video.id),
            title=video.title,
            description=video.description or '',
            privacy_status=video.youtube_privacy,
        )
        
        # Store task ID
        video.celery_task_id = task.id
        video.save(update_fields=['celery_task_id'])
        
        logger.info(f"Queued YouTube upload for video {video.id}, task {task.id}")
        
        return Response(VideoStatusSerializer(video).data)


class VideoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Video CRUD operations.
    """
    queryset = Video.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'youtube_privacy', 'uploaded_by']
    ordering_fields = ['created_at', 'updated_at', 'title']
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return VideoListSerializer
        if self.action in ['update', 'partial_update']:
            return VideoUpdateSerializer
        if self.action == 'status':
            return VideoStatusSerializer
        return VideoSerializer
    
    def get_queryset(self):
        """Filter videos based on user permissions"""
        user = self.request.user
        
        # Super admin or users with VIDEO_MANAGE permission see all
        if user.is_super_admin or user.has_permission_code('VIDEO_MANAGE'):
            return Video.objects.all()
        
        # Others see only their own videos
        return Video.objects.filter(uploaded_by=user)
    
    @extend_schema(
        responses={200: VideoStatusSerializer},
        summary="Get video status",
        description="Poll video upload/processing status",
    )
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get video status for polling"""
        video = self.get_object()
        return Response(VideoStatusSerializer(video).data)
    
    @extend_schema(
        request=RetryUploadSerializer,
        responses={
            200: VideoStatusSerializer,
            400: OpenApiResponse(description="Cannot retry - video not failed"),
        },
        summary="Retry failed upload",
        description="Retry a failed YouTube upload",
    )
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed upload"""
        video = self.get_object()
        
        if video.status != VideoUploadStatus.FAILED:
            return Response(
                {'error': 'Can only retry failed uploads'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not video.s3_key:
            return Response(
                {'error': 'S3 file not found. Please upload again.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset status and queue task
        video.status = VideoUploadStatus.QUEUED
        video.error_message = None
        video.save(update_fields=['status', 'error_message', 'updated_at'])
        
        from videos.tasks import upload_to_youtube_task
        task = upload_to_youtube_task.delay(
            video_id=str(video.id),
            title=video.title,
            description=video.description or '',
            privacy_status=video.youtube_privacy,
        )
        
        video.celery_task_id = task.id
        video.save(update_fields=['celery_task_id'])
        
        logger.info(f"Retrying upload for video {video.id}")
        
        return Response(VideoStatusSerializer(video).data)
    
    def perform_destroy(self, instance):
        """Clean up S3 and YouTube when deleting video"""
        # Delete from S3
        if instance.s3_key:
            try:
                from videos.services.s3_service import S3Service
                s3_service = S3Service()
                s3_service.delete_object(instance.s3_key)
            except Exception as e:
                logger.warning(f"Failed to delete S3 object: {e}")
        
        # Optionally delete from YouTube
        if instance.youtube_video_id:
            try:
                from videos.services.youtube_service import YouTubeService
                youtube_service = YouTubeService()
                youtube_service.delete_video(instance.youtube_video_id)
            except Exception as e:
                logger.warning(f"Failed to delete YouTube video: {e}")
        
        instance.delete()
