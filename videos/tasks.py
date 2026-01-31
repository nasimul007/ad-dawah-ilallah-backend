"""
Celery tasks for video upload pipeline.

These tasks run asynchronously in background workers,
ensuring that video uploads don't block web requests.
"""
import logging
import tempfile
import os
from datetime import timedelta

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,  # Exponential backoff starting at 60s
    retry_backoff_max=3600,  # Max 1 hour between retries
    retry_jitter=True,  # Add randomness to prevent thundering herd
    max_retries=5,
    acks_late=True,  # Acknowledge after completion for reliability
)
def upload_to_youtube_task(
    self,
    video_id: str,
    title: str,
    description: str = '',
    privacy_status: str = 'unlisted',
    tags: list = None,
):
    """
    Upload video from S3 to YouTube.
    
    This task:
    1. Downloads video from S3 (streaming)
    2. Uploads to YouTube using resumable upload
    3. Updates video record with YouTube ID
    4. Cleans up temporary files
    
    Args:
        video_id: UUID of the Video record
        title: YouTube video title
        description: YouTube video description
        privacy_status: 'private', 'unlisted', or 'public'
        tags: List of video tags
    """
    from videos.models import Video, VideoUploadStatus
    from videos.services.s3_service import S3Service
    from videos.services.youtube_service import YouTubeService
    
    logger.info(f"Starting YouTube upload for video {video_id}")
    
    try:
        # Get video record
        video = Video.objects.get(id=video_id)
        
        # Check if already uploaded
        if video.youtube_video_id:
            logger.warning(f"Video {video_id} already has YouTube ID, skipping")
            return {'status': 'already_uploaded', 'youtube_id': video.youtube_video_id}
        
        # Update status to uploading
        video.status = VideoUploadStatus.UPLOADING_YOUTUBE
        video.celery_task_id = self.request.id
        video.save(update_fields=['status', 'celery_task_id', 'updated_at'])
        
        # Initialize services
        s3_service = S3Service()
        youtube_service = YouTubeService()
        
        # Download from S3 to temp file
        # (Streaming directly to YouTube is also possible but temp file is more reliable)
        temp_file = None
        try:
            # Create temp file with proper extension
            ext = video.s3_key.rsplit('.', 1)[-1] if '.' in video.s3_key else 'mp4'
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f'.{ext}',
                prefix='youtube_upload_'
            )
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Download from S3
            logger.info(f"Downloading video from S3: {video.s3_key}")
            download_url = s3_service.generate_download_url(video.s3_key, expires_in=3600)
            
            import requests
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(temp_file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            logger.info(f"Downloaded video to {temp_file_path}")
            
            # Progress callback to update video record
            def progress_callback(progress: int):
                Video.objects.filter(id=video_id).update(
                    youtube_upload_progress=progress,
                    updated_at=timezone.now()
                )
            
            # Upload to YouTube
            logger.info(f"Starting YouTube upload for {video_id}")
            result = youtube_service.upload_video_from_file(
                file_path=temp_file_path,
                title=title,
                description=description,
                privacy_status=privacy_status,
                tags=tags or [],
                progress_callback=progress_callback,
            )
            
            # Update video record with success
            with transaction.atomic():
                video.refresh_from_db()
                video.youtube_video_id = result.video_id
                video.youtube_url = result.video_url
                video.youtube_privacy = result.privacy_status
                video.youtube_upload_progress = 100
                video.status = VideoUploadStatus.PROCESSING
                video.youtube_uploaded_at = timezone.now()
                video.save()
            
            logger.info(f"YouTube upload complete: {result.video_id}")
            
            # Queue status check task
            check_youtube_processing_status.apply_async(
                args=[str(video_id)],
                countdown=60,  # Check after 1 minute
            )
            
            return {
                'status': 'success',
                'youtube_id': result.video_id,
                'youtube_url': result.video_url,
            }
            
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temp file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file: {e}")
        
    except Video.DoesNotExist:
        logger.error(f"Video not found: {video_id}")
        return {'status': 'error', 'message': 'Video not found'}
    
    except Exception as e:
        logger.error(f"YouTube upload failed for {video_id}: {e}")
        
        # Update video status to failed
        try:
            Video.objects.filter(id=video_id).update(
                status=VideoUploadStatus.FAILED,
                error_message=str(e)[:1000],
                retry_count=self.request.retries + 1,
                updated_at=timezone.now(),
            )
        except Exception:
            pass
        
        # Retry with exponential backoff
        try:
            raise self.retry(exc=e)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for video {video_id}")
            raise


@shared_task(
    bind=True,
    max_retries=10,
    default_retry_delay=120,
)
def check_youtube_processing_status(self, video_id: str):
    """
    Check if YouTube has finished processing the video.
    
    YouTube processing can take several minutes to hours depending on video length.
    This task polls YouTube API until processing is complete.
    """
    from videos.models import Video, VideoUploadStatus
    from videos.services.youtube_service import YouTubeService
    
    logger.info(f"Checking YouTube processing status for {video_id}")
    
    try:
        video = Video.objects.get(id=video_id)
        
        if not video.youtube_video_id:
            logger.warning(f"Video {video_id} has no YouTube ID")
            return {'status': 'error', 'message': 'No YouTube ID'}
        
        if video.status == VideoUploadStatus.READY:
            logger.info(f"Video {video_id} already ready")
            return {'status': 'already_ready'}
        
        youtube_service = YouTubeService()
        status = youtube_service.get_video_status(video.youtube_video_id)
        
        processing_status = status.get('processing_status')
        upload_status = status.get('upload_status')
        
        logger.info(
            f"Video {video_id} - upload: {upload_status}, processing: {processing_status}"
        )
        
        if processing_status == 'succeeded' or upload_status == 'processed':
            # Video is ready
            video.status = VideoUploadStatus.READY
            video.save(update_fields=['status', 'updated_at'])
            logger.info(f"Video {video_id} is now ready")
            return {'status': 'ready'}
        
        elif processing_status == 'failed':
            # Processing failed
            video.status = VideoUploadStatus.FAILED
            video.error_message = 'YouTube processing failed'
            video.save(update_fields=['status', 'error_message', 'updated_at'])
            logger.error(f"YouTube processing failed for {video_id}")
            return {'status': 'failed'}
        
        else:
            # Still processing, retry later
            retry_delay = min(120 * (2 ** self.request.retries), 3600)  # Max 1 hour
            logger.info(f"Video {video_id} still processing, retry in {retry_delay}s")
            raise self.retry(countdown=retry_delay)
        
    except Video.DoesNotExist:
        logger.error(f"Video not found: {video_id}")
        return {'status': 'error', 'message': 'Video not found'}
    
    except MaxRetriesExceededError:
        logger.error(f"Max retries exceeded checking status for {video_id}")
        # Mark as ready anyway - user can manually check
        Video.objects.filter(id=video_id).update(
            status=VideoUploadStatus.READY,
            updated_at=timezone.now(),
        )
        return {'status': 'timeout', 'message': 'Assumed ready after timeout'}


@shared_task
def cleanup_failed_uploads(days_old: int = 7):
    """
    Cleanup task to remove old failed uploads from S3.
    
    Run periodically (e.g., daily) to clean up storage.
    """
    from videos.models import Video, VideoUploadStatus
    from videos.services.s3_service import S3Service
    
    cutoff_date = timezone.now() - timedelta(days=days_old)
    
    failed_videos = Video.objects.filter(
        status=VideoUploadStatus.FAILED,
        created_at__lt=cutoff_date,
        s3_key__isnull=False,
    )
    
    s3_service = S3Service()
    deleted_count = 0
    
    for video in failed_videos:
        try:
            if s3_service.delete_object(video.s3_key):
                video.s3_key = None
                video.save(update_fields=['s3_key', 'updated_at'])
                deleted_count += 1
        except Exception as e:
            logger.error(f"Failed to cleanup video {video.id}: {e}")
    
    logger.info(f"Cleaned up {deleted_count} failed uploads older than {days_old} days")
    return {'deleted_count': deleted_count}


@shared_task
def retry_failed_uploads(max_retries: int = 3):
    """
    Retry failed uploads that haven't exceeded retry limit.
    
    Run periodically to automatically retry failed uploads.
    """
    from videos.models import Video, VideoUploadStatus
    
    failed_videos = Video.objects.filter(
        status=VideoUploadStatus.FAILED,
        retry_count__lt=max_retries,
        s3_key__isnull=False,
    )
    
    queued_count = 0
    
    for video in failed_videos:
        try:
            video.status = VideoUploadStatus.QUEUED
            video.error_message = None
            video.save(update_fields=['status', 'error_message', 'updated_at'])
            
            upload_to_youtube_task.delay(
                video_id=str(video.id),
                title=video.title,
                description=video.description or '',
                privacy_status=video.youtube_privacy,
            )
            
            queued_count += 1
            logger.info(f"Queued retry for video {video.id}")
            
        except Exception as e:
            logger.error(f"Failed to queue retry for video {video.id}: {e}")
    
    logger.info(f"Queued {queued_count} failed videos for retry")
    return {'queued_count': queued_count}

