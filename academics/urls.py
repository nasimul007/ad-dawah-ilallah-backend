from rest_framework.routers import DefaultRouter
from academics.views import AcademicTermViewSet, CourseViewSet

router = DefaultRouter()
router.register("academic-terms", AcademicTermViewSet, basename="academic-term")
router.register("courses", CourseViewSet, basename="course")


urlpatterns = router.urls
