"""
YouTube Data API v3 Service for resumable video uploads.

Features:
- Resumable uploads (handles large files up to 128GB)
- Automatic token refresh
- Quota tracking
- Error handling with retries
"""
import io
import os
import logging
import tempfile
from datetime import datetime, timedelta
from typing import Optional, Callable
from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError, ResumableUploadError
import httplib2

logger = logging.getLogger(__name__)

# Scopes required for YouTube upload
YOUTUBE_SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
]

# Retry configuration
MAX_RETRIES = 10
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError)


@dataclass
class YouTubeUploadResult:
    """Result of a YouTube upload operation"""
    video_id: str
    video_url: str
    status: str
    title: str
    description: str
    privacy_status: str


class YouTubeService:
    """
    Service for YouTube Data API operations.
    
    Handles:
    - OAuth token management
    - Resumable video uploads
    - Video metadata updates
    - Quota tracking
    
    Configuration in settings:
    - YOUTUBE_CLIENT_ID
    - YOUTUBE_CLIENT_SECRET
    - YOUTUBE_API_KEY (optional, for read-only ops)
    """
    
    CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks for resumable upload
    
    def __init__(self, credential_name: str = 'main_channel'):
        """
        Initialize YouTube service with stored credentials.
        
        Args:
            credential_name: Name of the YouTubeCredential to use
        """
        self.credential_name = credential_name
        self._youtube = None
        self._credentials = None
    
    def _get_stored_credential(self):
        """Get stored OAuth credential from database"""
        from videos.models import YouTubeCredential
        
        try:
            return YouTubeCredential.objects.get(
                name=self.credential_name,
                is_active=True
            )
        except YouTubeCredential.DoesNotExist:
            logger.error(f"No active YouTube credential found: {self.credential_name}")
            raise ValueError(
                f"YouTube credential '{self.credential_name}' not found or inactive. "
                "Please set up OAuth credentials first."
            )
    
    def _refresh_token_if_needed(self, stored_cred) -> bool:
        """
        Refresh OAuth token if expired or about to expire.
        
        Returns:
            True if token was refreshed
        """
        # Check if token expires within 5 minutes
        if stored_cred.token_expiry and stored_cred.token_expiry > timezone.now() + timedelta(minutes=5):
            return False
        
        logger.info(f"Refreshing YouTube OAuth token for {self.credential_name}")
        
        credentials = Credentials(
            token=stored_cred.access_token,
            refresh_token=stored_cred.refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=getattr(settings, 'YOUTUBE_CLIENT_ID', None),
            client_secret=getattr(settings, 'YOUTUBE_CLIENT_SECRET', None),
        )
        
        try:
            credentials.refresh(Request())
            
            # Update stored credentials
            stored_cred.access_token = credentials.token
            stored_cred.token_expiry = timezone.now() + timedelta(seconds=3600)
            stored_cred.save(update_fields=['access_token', 'token_expiry', 'updated_at'])
            
            logger.info("YouTube OAuth token refreshed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh YouTube token: {e}")
            raise
    
    def _get_youtube_client(self):
        """Get authenticated YouTube API client"""
        if self._youtube:
            return self._youtube
        
        stored_cred = self._get_stored_credential()
        self._refresh_token_if_needed(stored_cred)
        
        credentials = Credentials(
            token=stored_cred.access_token,
            refresh_token=stored_cred.refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=getattr(settings, 'YOUTUBE_CLIENT_ID', None),
            client_secret=getattr(settings, 'YOUTUBE_CLIENT_SECRET', None),
        )
        
        self._youtube = build('youtube', 'v3', credentials=credentials)
        return self._youtube
    
    def upload_video_from_file(
        self,
        file_path: str,
        title: str,
        description: str = '',
        privacy_status: str = 'unlisted',
        tags: list = None,
        category_id: str = '27',  # Education category
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> YouTubeUploadResult:
        """
        Upload a video file to YouTube using resumable upload.
        
        This is the main upload method for production use.
        Uses chunked resumable uploads for reliability with large files.
        
        Args:
            file_path: Path to the video file
            title: Video title (max 100 chars)
            description: Video description (max 5000 chars)
            privacy_status: 'private', 'unlisted', or 'public'
            tags: List of tags
            category_id: YouTube category ID (27 = Education)
            progress_callback: Callback function receiving progress percentage
        
        Returns:
            YouTubeUploadResult with video details
        """
        youtube = self._get_youtube_client()
        
        # Prepare video metadata
        body = {
            'snippet': {
                'title': title[:100],  # YouTube limit
                'description': (description or '')[:5000],  # YouTube limit
                'tags': tags or [],
                'categoryId': category_id,
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False,
            },
        }
        
        # Create resumable upload
        media = MediaFileUpload(
            file_path,
            chunksize=self.CHUNK_SIZE,
            resumable=True,
            mimetype='video/*'
        )
        
        # Initialize upload request
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media,
        )
        
        # Execute resumable upload with retries
        response = self._execute_resumable_upload(
            request,
            progress_callback=progress_callback
        )
        
        video_id = response['id']
        logger.info(f"YouTube upload complete: {video_id}")
        
        return YouTubeUploadResult(
            video_id=video_id,
            video_url=f"https://www.youtube.com/watch?v={video_id}",
            status=response['status']['uploadStatus'],
            title=response['snippet']['title'],
            description=response['snippet'].get('description', ''),
            privacy_status=response['status']['privacyStatus'],
        )
    
    def upload_video_from_stream(
        self,
        file_stream: io.IOBase,
        file_size: int,
        title: str,
        description: str = '',
        privacy_status: str = 'unlisted',
        tags: list = None,
        category_id: str = '27',
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> YouTubeUploadResult:
        """
        Upload a video from a file-like stream.
        
        Useful when streaming directly from S3 without downloading to disk.
        
        Args:
            file_stream: File-like object
            file_size: Total size of the stream
            title: Video title
            description: Video description
            privacy_status: Privacy status
            tags: Video tags
            category_id: Category ID
            progress_callback: Progress callback
        
        Returns:
            YouTubeUploadResult
        """
        youtube = self._get_youtube_client()
        
        body = {
            'snippet': {
                'title': title[:100],
                'description': (description or '')[:5000],
                'tags': tags or [],
                'categoryId': category_id,
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False,
            },
        }
        
        media = MediaIoBaseUpload(
            file_stream,
            mimetype='video/*',
            chunksize=self.CHUNK_SIZE,
            resumable=True,
        )
        
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media,
        )
        
        response = self._execute_resumable_upload(
            request,
            progress_callback=progress_callback
        )
        
        video_id = response['id']
        
        return YouTubeUploadResult(
            video_id=video_id,
            video_url=f"https://www.youtube.com/watch?v={video_id}",
            status=response['status']['uploadStatus'],
            title=response['snippet']['title'],
            description=response['snippet'].get('description', ''),
            privacy_status=response['status']['privacyStatus'],
        )
    
    def _execute_resumable_upload(
        self,
        request,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> dict:
        """
        Execute a resumable upload with retry logic.
        
        Handles:
        - Network interruptions
        - Server errors
        - Resume from last successful chunk
        """
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                status, response = request.next_chunk()
                
                if status:
                    progress = int(status.progress() * 100)
                    logger.debug(f"Upload progress: {progress}%")
                    
                    if progress_callback:
                        progress_callback(progress)
                        
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = f"HTTP error {e.resp.status}: {e.content}"
                else:
                    raise
                    
            except RETRIABLE_EXCEPTIONS as e:
                error = str(e)
            
            if error:
                retry += 1
                if retry > MAX_RETRIES:
                    logger.error(f"Max retries exceeded: {error}")
                    raise Exception(f"Upload failed after {MAX_RETRIES} retries: {error}")
                
                # Exponential backoff
                sleep_seconds = min(2 ** retry, 60)
                logger.warning(f"Retry {retry}/{MAX_RETRIES} after {sleep_seconds}s: {error}")
                import time
                time.sleep(sleep_seconds)
                error = None
        
        # Final progress callback
        if progress_callback:
            progress_callback(100)
        
        return response
    
    def update_video_metadata(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        privacy_status: Optional[str] = None,
        tags: Optional[list] = None,
    ) -> dict:
        """Update video metadata on YouTube"""
        youtube = self._get_youtube_client()
        
        # Get current video details
        video_response = youtube.videos().list(
            part='snippet,status',
            id=video_id
        ).execute()
        
        if not video_response.get('items'):
            raise ValueError(f"Video not found: {video_id}")
        
        video = video_response['items'][0]
        
        # Update only specified fields
        if title:
            video['snippet']['title'] = title[:100]
        if description:
            video['snippet']['description'] = description[:5000]
        if tags:
            video['snippet']['tags'] = tags
        if privacy_status:
            video['status']['privacyStatus'] = privacy_status
        
        return youtube.videos().update(
            part='snippet,status',
            body=video
        ).execute()
    
    def get_video_status(self, video_id: str) -> dict:
        """Get video processing status from YouTube"""
        youtube = self._get_youtube_client()
        
        response = youtube.videos().list(
            part='status,processingDetails',
            id=video_id
        ).execute()
        
        if not response.get('items'):
            return {'status': 'not_found'}
        
        item = response['items'][0]
        return {
            'upload_status': item['status'].get('uploadStatus'),
            'privacy_status': item['status'].get('privacyStatus'),
            'processing_status': item.get('processingDetails', {}).get('processingStatus'),
        }
    
    def delete_video(self, video_id: str) -> bool:
        """Delete a video from YouTube"""
        try:
            youtube = self._get_youtube_client()
            youtube.videos().delete(id=video_id).execute()
            logger.info(f"Deleted YouTube video: {video_id}")
            return True
        except HttpError as e:
            logger.error(f"Failed to delete YouTube video {video_id}: {e}")
            return False


def get_oauth_authorization_url(redirect_uri: str) -> str:
    """
    Generate OAuth authorization URL for initial setup.
    
    This is used during initial credential setup to get user consent.
    
    Args:
        redirect_uri: URI to redirect after authorization
    
    Returns:
        Authorization URL to redirect user to
    """
    from google_auth_oauthlib.flow import Flow
    
    client_config = {
        'web': {
            'client_id': getattr(settings, 'YOUTUBE_CLIENT_ID', None),
            'client_secret': getattr(settings, 'YOUTUBE_CLIENT_SECRET', None),
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=YOUTUBE_SCOPES,
        redirect_uri=redirect_uri,
    )
    
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
    )
    
    return auth_url


def exchange_oauth_code(code: str, redirect_uri: str) -> dict:
    """
    Exchange authorization code for tokens.
    
    Args:
        code: Authorization code from OAuth callback
        redirect_uri: Same redirect URI used in authorization
    
    Returns:
        Dict with access_token, refresh_token, expires_at
    """
    from google_auth_oauthlib.flow import Flow
    
    client_config = {
        'web': {
            'client_id': getattr(settings, 'YOUTUBE_CLIENT_ID', None),
            'client_secret': getattr(settings, 'YOUTUBE_CLIENT_SECRET', None),
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=YOUTUBE_SCOPES,
        redirect_uri=redirect_uri,
    )
    
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    return {
        'access_token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'expires_at': credentials.expiry,
    }

