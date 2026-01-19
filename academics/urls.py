from rest_framework.routers import DefaultRouter
from academics.views import AcademicTermViewSet, CourseViewSet, CourseOfferingViewSet

router = DefaultRouter()
router.register("academic-terms", AcademicTermViewSet, basename="academic-term")
router.register("courses", CourseViewSet, basename="course")
router.register("course-offerings", CourseOfferingViewSet, basename="course-offering")


urlpatterns = router.urls
