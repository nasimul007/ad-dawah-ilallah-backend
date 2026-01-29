from rest_framework.routers import DefaultRouter
from academics.views import AcademicTermViewSet, CourseViewSet, CourseOfferingViewSet, ClassRoutineViewSet, \
    ClassSessionViewSet, CourseEnrollmentViewSet, AttendanceViewSet, AssignmentSubmissionViewSet, AssignmentViewSet, \
    AssessmentViewSet, AssessmentResultViewSet, CourseResultViewSet

router = DefaultRouter()
router.register("academic-terms", AcademicTermViewSet, basename="academic-term")

router.register("courses", CourseViewSet, basename="course")
router.register("course-offerings", CourseOfferingViewSet, basename="course-offering")
router.register("course-enrollments", CourseEnrollmentViewSet, basename="course-enrollments")

router.register("class-routines", ClassRoutineViewSet, basename="class-routine")
router.register("class-sessions", ClassSessionViewSet, basename="class-session")

router.register("attendance", AttendanceViewSet, basename="attendance")

router.register("assignments", AssignmentViewSet, basename="assignment")
router.register("assignment-submissions", AssignmentSubmissionViewSet, basename="assignment-submission")

router.register("assessments", AssessmentViewSet, basename="assessment")
router.register("assessment-results", AssessmentResultViewSet, basename="assessment-result")
router.register("course-results", CourseResultViewSet, basename="course-result")


urlpatterns = router.urls
