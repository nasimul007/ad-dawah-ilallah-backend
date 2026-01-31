"""
Celery configuration for async video upload tasks.

This enables background processing for:
- YouTube uploads (long-running)
- Video processing status checks
- Cleanup tasks
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create Celery app
app = Celery('ad_dawah_ilallah')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all Django apps
app.autodiscover_tasks()

# Celery configuration
app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,  # Acknowledge after task completes (for reliability)
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Rate limiting for YouTube API
    task_annotations={
        'videos.tasks.upload_to_youtube_task': {
            'rate_limit': '10/m',  # Max 10 uploads per minute
        },
    },
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute default retry delay
    task_max_retries=5,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time (for large video uploads)
    worker_concurrency=2,  # Limit concurrent video uploads
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')

