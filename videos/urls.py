"""
URL configuration for videos app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from videos.views import (
    InitiateUploadView,
    ConfirmUploadView,
    VideoViewSet,
)

router = DefaultRouter()
router.register(r'', VideoViewSet, basename='video')

urlpatterns = [
    # Upload flow endpoints
    path('initiate-upload/', InitiateUploadView.as_view(), name='initiate-upload'),
    path('confirm-upload/', ConfirmUploadView.as_view(), name='confirm-upload'),
    
    # Video CRUD (includes status and retry actions)
    path('', include(router.urls)),
]

