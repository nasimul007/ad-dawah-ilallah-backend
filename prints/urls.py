from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrintOrderViewSet, PrintViewSet

router = DefaultRouter()
router.register(r'orders', PrintOrderViewSet)
router.register(r'items', PrintViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
