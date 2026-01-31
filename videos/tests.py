"""
Tests for video upload pipeline.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from videos.models import Video, VideoUploadStatus, YouTubeCredential

User = get_user_model()


class VideoModelTests(TestCase):
    """Tests for Video model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            full_name='Test User',
            password='testpass123'
        )
    
    def test_video_creation(self):
        """Test creating a video record"""
        video = Video.objects.create(
            title='Test Video',
            description='Test description',
            uploaded_by=self.user,
        )
        
        self.assertEqual(video.status, VideoUploadStatus.PENDING)
        self.assertIsNotNone(video.id)
        self.assertEqual(str(video), 'Test Video (pending)')
    
    def test_video_status_transitions(self):
        """Test video status transitions"""
        video = Video.objects.create(
            title='Test Video',
            uploaded_by=self.user,
        )
        
        # Test status updates
        video.status = VideoUploadStatus.UPLOADING_S3
        video.save()
        self.assertEqual(video.status, VideoUploadStatus.UPLOADING_S3)
        
        video.status = VideoUploadStatus.READY
        video.save()
        self.assertTrue(video.is_ready)
    
    def test_video_embed_url(self):
        """Test embed URL generation"""
        video = Video.objects.create(
            title='Test Video',
            youtube_video_id='abc123',
            uploaded_by=self.user,
        )
        
        self.assertEqual(
            video.embed_url,
            'https://www.youtube.com/embed/abc123'
        )
    
    def test_video_mark_failed(self):
        """Test marking video as failed"""
        video = Video.objects.create(
            title='Test Video',
            uploaded_by=self.user,
        )
        
        video.mark_failed('Test error')
        
        self.assertEqual(video.status, VideoUploadStatus.FAILED)
        self.assertEqual(video.error_message, 'Test error')
        self.assertEqual(video.retry_count, 1)


class VideoAPITests(APITestCase):
    """Tests for video API endpoints"""
    
    def setUp(self):
        from accounts.models import Role, Permission
        
        self.user = User.objects.create_user(
            username='testuser',
            full_name='Test User',
            password='testpass123',
            is_superuser=True,  # Super admin for all permissions
        )
        
        # Create permission and role
        permission = Permission.objects.create(
            code='VIDEO_UPLOAD',
            module='videos',
            description='Can upload videos'
        )
        role = Role.objects.create(name='instructor')
        role.permissions.add(permission)
        self.user.roles.add(role)
        
        self.client.force_authenticate(user=self.user)
    
    @patch('videos.views.S3Service')
    def test_initiate_upload(self, mock_s3):
        """Test initiating a video upload"""
        # Mock S3 service
        mock_instance = MagicMock()
        mock_instance.generate_presigned_url.return_value = MagicMock(
            upload_url='https://s3.example.com/presigned-url',
            s3_key='videos/2024/01/01/test-uuid.mp4',
            bucket='test-bucket',
            expires_in=3600,
            fields=None,
        )
        mock_s3.return_value = mock_instance
        
        response = self.client.post('/api/videos/initiate-upload/', {
            'title': 'Test Video',
            'description': 'Test description',
            'filename': 'test.mp4',
            'file_size': 1024 * 1024 * 100,  # 100MB
            'content_type': 'video/mp4',
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('video_id', response.data)
        self.assertIn('upload_url', response.data)
        self.assertIn('s3_key', response.data)
    
    def test_initiate_upload_validation(self):
        """Test validation for video upload"""
        # Test file size limit
        response = self.client.post('/api/videos/initiate-upload/', {
            'title': 'Test Video',
            'filename': 'test.mp4',
            'file_size': 5 * 1024 * 1024 * 1024,  # 5GB - exceeds limit
            'content_type': 'video/mp4',
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid extension
        response = self.client.post('/api/videos/initiate-upload/', {
            'title': 'Test Video',
            'filename': 'test.exe',
            'file_size': 1024 * 1024,
            'content_type': 'video/mp4',
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_video_list(self):
        """Test listing videos"""
        Video.objects.create(
            title='Video 1',
            uploaded_by=self.user,
        )
        Video.objects.create(
            title='Video 2',
            uploaded_by=self.user,
        )
        
        response = self.client.get('/api/videos/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_video_status(self):
        """Test getting video status"""
        video = Video.objects.create(
            title='Test Video',
            uploaded_by=self.user,
            status=VideoUploadStatus.PROCESSING,
            youtube_video_id='abc123',
        )
        
        response = self.client.get(f'/api/videos/{video.id}/status/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'processing')
        self.assertEqual(response.data['youtube_video_id'], 'abc123')
    
    @patch('videos.views.upload_to_youtube_task')
    def test_retry_failed_upload(self, mock_task):
        """Test retrying a failed upload"""
        video = Video.objects.create(
            title='Test Video',
            uploaded_by=self.user,
            status=VideoUploadStatus.FAILED,
            s3_key='videos/test.mp4',
            error_message='Previous error',
        )
        
        mock_task.delay.return_value = MagicMock(id='task-123')
        
        response = self.client.post(f'/api/videos/{video.id}/retry/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        video.refresh_from_db()
        self.assertEqual(video.status, VideoUploadStatus.QUEUED)
        self.assertIsNone(video.error_message)
