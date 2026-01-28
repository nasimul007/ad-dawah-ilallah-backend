from rest_framework.routers import DefaultRouter
from academics.views import AcademicTermViewSet, CourseViewSet, CourseOfferingViewSet, ClassRoutineViewSet, \
    ClassSessionViewSet, CourseEnrollmentViewSet, AttendanceViewSet

router = DefaultRouter()
router.register("academic-terms", AcademicTermViewSet, basename="academic-term")

router.register("courses", CourseViewSet, basename="course")
router.register("course-offerings", CourseOfferingViewSet, basename="course-offering")
router.register("course-enrollments", CourseEnrollmentViewSet, basename="course-enrollments")

router.register("class-routines", ClassRoutineViewSet, basename="class-routine")
router.register("class-sessions", ClassSessionViewSet, basename="class-session")

router.register("attendance", AttendanceViewSet, basename="attendance")



urlpatterns = router.urls
