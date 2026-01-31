"""
Videos app - Production-grade video upload pipeline.

Architecture:
- Frontend → S3 (presigned URL) - Direct upload to object storage
- Backend → Celery task → YouTube (resumable upload)
- Track status throughout the pipeline
"""
default_app_config = 'videos.apps.VideosConfig'

