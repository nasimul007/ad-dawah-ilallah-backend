from rest_framework.routers import DefaultRouter
from academics.views import AcademicTermViewSet

router = DefaultRouter()
router.register("academic-terms", AcademicTermViewSet, basename="academic-term")

urlpatterns = router.urls
