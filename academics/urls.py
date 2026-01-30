from rest_framework.routers import DefaultRouter
from academics.views import AcademicTermViewSet, CourseViewSet, CourseOfferingViewSet, ClassRoutineViewSet, \
    ClassSessionViewSet, CourseEnrollmentViewSet, AttendanceViewSet, AssignmentSubmissionViewSet, AssignmentViewSet, \
    AssessmentViewSet, AssessmentResultViewSet, CourseResultViewSet, CertificateTemplateViewSet, CertificateViewSet

router = DefaultRouter()
# academic-terms
router.register("academic-terms", AcademicTermViewSet, basename="academic-term")

# courses
router.register("courses", CourseViewSet, basename="course")
router.register("course-offerings", CourseOfferingViewSet, basename="course-offering")
router.register("course-enrollments", CourseEnrollmentViewSet, basename="course-enrollments")

# class
router.register("class-routines", ClassRoutineViewSet, basename="class-routine")
router.register("class-sessions", ClassSessionViewSet, basename="class-session")

# attendance
router.register("attendance", AttendanceViewSet, basename="attendance")

# assignments
router.register("assignments", AssignmentViewSet, basename="assignment")
router.register("assignment-submissions", AssignmentSubmissionViewSet, basename="assignment-submission")

# assessments
router.register("assessments", AssessmentViewSet, basename="assessment")
router.register("assessment-results", AssessmentResultViewSet, basename="assessment-result")
router.register("course-results", CourseResultViewSet, basename="course-result")

# certificates
router.register("certificate-templates", CertificateTemplateViewSet, basename="certificate-template")
router.register("certificates", CertificateViewSet, basename="certificate")


urlpatterns = router.urls
