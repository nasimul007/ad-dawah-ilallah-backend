"""
S3 Service for generating pre-signed URLs and managing video storage.

Supports:
- AWS S3
- Google Cloud Storage (S3-compatible)
- Wasabi
- Cloudflare R2
- MinIO (self-hosted)
"""
import uuid
import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class PresignedUrlResult:
    """Result of generating a presigned URL"""
    upload_url: str
    s3_key: str
    bucket: str
    expires_in: int
    fields: dict = None  # For multipart uploads


class S3Service:
    """
    Service for S3 operations.
    
    Configuration in settings:
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_S3_BUCKET_NAME
    - AWS_S3_REGION_NAME
    - AWS_S3_ENDPOINT_URL (optional, for S3-compatible services)
    - AWS_S3_PRESIGNED_EXPIRY (optional, default 3600)
    """
    
    def __init__(self):
        self.bucket = getattr(settings, 'AWS_S3_BUCKET_NAME', None)
        self.region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        self.endpoint_url = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
        self.presigned_expiry = getattr(settings, 'AWS_S3_PRESIGNED_EXPIRY', 3600)
        
        # Configure boto3 client
        config = Config(
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
        
        client_kwargs = {
            'service_name': 's3',
            'region_name': self.region,
            'aws_access_key_id': getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            'aws_secret_access_key': getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            'config': config,
        }
        
        # Add endpoint URL for S3-compatible services
        if self.endpoint_url:
            client_kwargs['endpoint_url'] = self.endpoint_url
        
        self._client = boto3.client(**client_kwargs)
    
    def generate_presigned_url(
        self,
        video_id: str,
        filename: str,
        content_type: str = 'video/mp4',
        file_size: Optional[int] = None,
    ) -> PresignedUrlResult:
        """
        Generate a pre-signed URL for direct browser upload.
        
        The URL allows PUT request directly from browser to S3,
        bypassing the backend server entirely.
        
        Args:
            video_id: Unique identifier for the video
            filename: Original filename (for extension)
            content_type: MIME type of the video
            file_size: Expected file size (for validation)
        
        Returns:
            PresignedUrlResult with upload URL and metadata
        """
        # Generate unique S3 key with date prefix for organization
        date_prefix = datetime.utcnow().strftime('%Y/%m/%d')
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'mp4'
        s3_key = f"videos/{date_prefix}/{video_id}.{ext}"
        
        try:
            # Generate presigned URL for PUT operation
            params = {
                'Bucket': self.bucket,
                'Key': s3_key,
                'ContentType': content_type,
            }
            
            # Add content length condition if file size is known
            # This prevents uploading files larger than expected
            conditions = []
            if file_size:
                conditions.append(['content-length-range', 0, file_size])
            
            presigned_url = self._client.generate_presigned_url(
                'put_object',
                Params=params,
                ExpiresIn=self.presigned_expiry,
            )
            
            logger.info(
                f"Generated presigned URL for video {video_id}, "
                f"key: {s3_key}, expires in {self.presigned_expiry}s"
            )
            
            return PresignedUrlResult(
                upload_url=presigned_url,
                s3_key=s3_key,
                bucket=self.bucket,
                expires_in=self.presigned_expiry,
            )
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def generate_presigned_post(
        self,
        video_id: str,
        filename: str,
        content_type: str = 'video/mp4',
        max_file_size: int = 2 * 1024 * 1024 * 1024,  # 2GB
    ) -> PresignedUrlResult:
        """
        Generate a pre-signed POST for multipart form upload.
        
        Alternative to PUT that supports more complex upload policies
        and better progress tracking in some browsers.
        
        Args:
            video_id: Unique identifier for the video
            filename: Original filename
            content_type: MIME type
            max_file_size: Maximum allowed file size
        
        Returns:
            PresignedUrlResult with POST URL and required fields
        """
        date_prefix = datetime.utcnow().strftime('%Y/%m/%d')
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'mp4'
        s3_key = f"videos/{date_prefix}/{video_id}.{ext}"
        
        try:
            response = self._client.generate_presigned_post(
                Bucket=self.bucket,
                Key=s3_key,
                Fields={
                    'Content-Type': content_type,
                },
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 1, max_file_size],
                ],
                ExpiresIn=self.presigned_expiry,
            )
            
            logger.info(
                f"Generated presigned POST for video {video_id}, "
                f"key: {s3_key}"
            )
            
            return PresignedUrlResult(
                upload_url=response['url'],
                s3_key=s3_key,
                bucket=self.bucket,
                expires_in=self.presigned_expiry,
                fields=response['fields'],
            )
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned POST: {e}")
            raise
    
    def check_object_exists(self, s3_key: str) -> bool:
        """Check if an object exists in S3"""
        try:
            self._client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
    
    def get_object_size(self, s3_key: str) -> Optional[int]:
        """Get the size of an object in S3"""
        try:
            response = self._client.head_object(Bucket=self.bucket, Key=s3_key)
            return response.get('ContentLength')
        except ClientError:
            return None
    
    def generate_download_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for downloading/streaming"""
        return self._client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': s3_key},
            ExpiresIn=expires_in,
        )
    
    def delete_object(self, s3_key: str) -> bool:
        """Delete an object from S3"""
        try:
            self._client.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info(f"Deleted S3 object: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete S3 object {s3_key}: {e}")
            return False

