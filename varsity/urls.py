from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VarsityViewSet, PrintingPointViewSet, PrinterViewSet

router = DefaultRouter()
router.register(r'varsities', VarsityViewSet)
router.register(r'printing-points', PrintingPointViewSet)
router.register(r'printers', PrinterViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
