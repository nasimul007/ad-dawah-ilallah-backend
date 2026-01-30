import uuid
from datetime import date

from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter

from academics.models import AcademicTerm, Course, CourseOffering, CourseEnrollment, ClassRoutine, ClassSession, \
    Attendance, Assignment, AssignmentSubmission, Assessment, AssessmentResult, CourseResult, CertificateTemplate, \
    Certificate
from accounts.permissions import HasPermissionCode
from .serializers import AcademicTermSerializer, CourseSerializer, CourseOfferingSerializer, \
    CourseEnrollmentSerializer, ClassRoutineSerializer, ClassSessionSerializer, \
    AttendanceSerializer, AssignmentSerializer, AssignmentSubmissionSerializer, AssessmentSerializer, \
    AssessmentResultSerializer, CourseResultSerializer, CertificateTemplateSerializer, CertificateSerializer
from .services import AcademicTermService


class AcademicTermViewSet(ModelViewSet):
    serializer_class = AcademicTermSerializer
    filter_backends = [SearchFilter, OrderingFilter]

    search_fields = ["name"]
    ordering_fields = ["start_date", "end_date", "created_at"]
    ordering = ["-start_date"]

    required_permissions = {
        "GET": "ACADEMIC_TERM_VIEW",
        "POST": "ACADEMIC_TERM_MANAGE",
        "PUT": "ACADEMIC_TERM_MANAGE",
        "PATCH": "ACADEMIC_TERM_MANAGE",
        "DELETE": "ACADEMIC_TERM_MANAGE",
    }
    permission_classes = [IsAuthenticated, HasPermissionCode]

    def get_queryset(self):
        user = self.request.user

        # superusers see all
        if user.is_superuser:
            return AcademicTerm.objects.all()

        # institution-scoped
        return AcademicTerm.objects.filter(
            institution=user.institution
        )

    def perform_create(self, serializer):
        term = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

        if term.is_current:
            AcademicTermService.set_current_term(term)

    def perform_update(self, serializer):
        term = serializer.save(updated_by=self.request.user)

        if term.is_current:
            AcademicTermService.set_current_term(term)


class CourseViewSet(ModelViewSet):
    serializer_class = CourseSerializer
    filter_backends = [SearchFilter, OrderingFilter]

    search_fields = ["code", "title"]
    ordering_fields = ["title", "created_at"]
    ordering = ["title"]

    required_permissions = {
        "GET": "COURSES_VIEW",
        "POST": "COURSES_MANAGE",
        "PUT": "COURSES_MANAGE",
        "PATCH": "COURSES_MANAGE",
        "DELETE": "COURSES_MANAGE",
    }
    permission_classes = [IsAuthenticated, HasPermissionCode]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Course.objects.all()

        return Course.objects.filter(
            institution=user.institution
        )

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class CourseOfferingViewSet(ModelViewSet):
    serializer_class = CourseOfferingSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    required_permission = "COURSES_OFFER"

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["course__title", "course__code", "section_code"]
    ordering_fields = ["created_at", "start_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return CourseOffering.objects.select_related(
                "course", "academic_term"
            )

        return CourseOffering.objects.filter(
            institution=user.institution
        ).select_related("course", "academic_term")

    def perform_create(self, serializer):
        serializer.save(
            institution=self.request.user.institution,
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class CourseEnrollmentViewSet(ModelViewSet):
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    required_permissions = {
        "GET": "COURSES_VIEW",
        "POST": "COURSES_MANAGE",
        "PUT": "COURSES_MANAGE",
        "PATCH": "COURSES_MANAGE",
        "DELETE": "COURSES_MANAGE",
    }

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "student__full_name",
        "student__username",
        "course_offering__course__title",
        "course_offering__course__code",
    ]
    ordering_fields = ["created_at", "enrollment_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user

         # Superuser → everything
        if user.is_superuser:
            return CourseEnrollment.objects.select_related(
                "student",
                "course_offering",
                "course_offering__course",
                "course_offering__academic_term",
            )

        # student → only own enrollments
        if user.has_role_code("student"):
            return CourseEnrollment.objects.filter(
                student=user
            ).select_related(
                "course_offering",
                "course_offering__course",
                "course_offering__academic_term",
            )

        # Admin / coordinator / others → institution scope
        return CourseEnrollment.objects.filter(
            course_offering__institution=user.institution
        ).select_related(
            "student",
            "course_offering",
            "course_offering__course",
            "course_offering__academic_term",
        )

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
            enrollment_source="admin"
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

class ClassRoutineViewSet(ModelViewSet):
    serializer_class = ClassRoutineSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    required_permissions = {
        "GET": "COURSES_VIEW",
        "POST": "COURSES_MANAGE",
        "PUT": "COURSES_MANAGE",
        "PATCH": "COURSES_MANAGE",
        "DELETE": "COURSES_MANAGE",
    }

    filter_backends = [OrderingFilter]
    ordering_fields = ["weekday", "start_time"]
    ordering = ["weekday", "start_time"]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return ClassRoutine.objects.select_related(
                "course_offering"
            )

        if user.has_role_code("student"):
            return ClassRoutine.objects.filter(
                course_offering__enrollments__student=user
            ).distinct()

        return ClassRoutine.objects.filter(
            course_offering__institution=user.institution
        ).select_related("course_offering")


class ClassSessionViewSet(ModelViewSet):
    serializer_class = ClassSessionSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    required_permissions = {
        "GET": "COURSES_VIEW",
        "POST": "COURSES_MANAGE",
        "PUT": "COURSES_MANAGE",
        "PATCH": "COURSES_MANAGE",
        "DELETE": "COURSES_MANAGE",
    }

    filter_backends = [OrderingFilter]
    ordering_fields = ["session_date"]
    ordering = ["-session_date"]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return ClassSession.objects.select_related(
                "course_offering"
            )

        # Students → only their sessions
        if user.has_role_code("student"):
            return ClassSession.objects.filter(
                course_offering__enrollments__student=user
            ).distinct()

        return ClassSession.objects.filter(
            course_offering__institution=user.institution
        ).select_related("course_offering")


class AttendanceViewSet(ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    required_permissions = {
        "GET": "COURSES_VIEW",
        "POST": "COURSES_MANAGE",
        "PUT": "COURSES_MANAGE",
        "PATCH": "COURSES_MANAGE",
        "DELETE": "COURSES_MANAGE",
    }

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["student__full_name", "student__username"]
    ordering_fields = ["created_at"]
    ordering = ["student__full_name"]

    def get_queryset(self):
        user = self.request.user

        # Superuser → everything
        if user.is_superuser:
            return Attendance.objects.select_related(
                "student",
                "class_session",
                "class_session__course_offering",
            )

        # Student → only own attendance
        if user.has_role_code("student"):
            return Attendance.objects.filter(
                student=user
            ).select_related(
                "class_session",
                "class_session__course_offering",
            )

        # Admin / teacher → institution scope
        return Attendance.objects.filter(
            class_session__course_offering__institution=user.institution
        ).select_related(
            "student",
            "class_session",
            "class_session__course_offering",
        )

    def perform_create(self, serializer):
        serializer.save(
            marked_by=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(
            marked_by=self.request.user
        )


class AssignmentViewSet(ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    required_permissions = {
        "GET": "COURSES_VIEW",
        "POST": "COURSES_MANAGE",
        "PUT": "COURSES_MANAGE",
        "PATCH": "COURSES_MANAGE",
        "DELETE": "COURSES_MANAGE",
    }

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title"]
    ordering_fields = ["due_at", "created_at"]
    ordering = ["-due_at"]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Assignment.objects.select_related("course_offering")

        if user.has_role_code("student"):
            return Assignment.objects.filter(
                course_offering__enrollments__student=user
            ).distinct()

        return Assignment.objects.filter(
            course_offering__institution=user.institution
        )

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class AssignmentSubmissionViewSet(ModelViewSet):
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    required_permissions = {
        "GET": "COURSES_VIEW",
        "POST": "COURSES_VIEW",     # students submit
        "PUT": "COURSES_MANAGE",    # grading
        "PATCH": "COURSES_MANAGE",
        "DELETE": "COURSES_MANAGE",
    }

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["student__full_name"]
    ordering_fields = ["submitted_at"]
    ordering = ["-submitted_at"]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return AssignmentSubmission.objects.select_related(
                "student", "assignment"
            )

        if user.has_role_code("student"):
            return AssignmentSubmission.objects.filter(
                student=user
            ).select_related("assignment")

        return AssignmentSubmission.objects.filter(
            assignment__course_offering__institution=user.institution
        )

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    def perform_update(self, serializer):
        serializer.save(
            graded_by=self.request.user,
            graded_at=now()
        )


class AssessmentViewSet(ModelViewSet):
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    required_permissions = {
        "GET": "COURSES_VIEW",
        "POST": "COURSES_MANAGE",
        "PUT": "COURSES_MANAGE",
        "PATCH": "COURSES_MANAGE",
        "DELETE": "COURSES_MANAGE",
    }

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Assessment.objects.all()

        if user.has_role_code("student"):
            return Assessment.objects.filter(
                course_offering__enrollments__student=user
            ).distinct()

        return Assessment.objects.filter(
            course_offering__institution=user.institution
        )


class AssessmentResultViewSet(ModelViewSet):
    serializer_class = AssessmentResultSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    required_permissions = {
        "GET": "COURSES_VIEW",
        "POST": "COURSES_MANAGE",
        "PUT": "COURSES_MANAGE",
        "PATCH": "COURSES_MANAGE",
        "DELETE": "COURSES_MANAGE",
    }

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return AssessmentResult.objects.select_related(
                "assessment", "enrollment"
            )

        if user.has_role_code("student"):
            return AssessmentResult.objects.filter(
                enrollment__student=user
            )

        return AssessmentResult.objects.filter(
            enrollment__course_offering__institution=user.institution
        )


class CourseResultViewSet(ModelViewSet):
    serializer_class = CourseResultSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    required_permissions = {
        "GET": "COURSES_VIEW",
        "POST": "COURSES_MANAGE",
        "PUT": "COURSES_MANAGE",
        "PATCH": "COURSES_MANAGE",
        "DELETE": "COURSES_MANAGE",
    }

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return CourseResult.objects.all()

        if user.has_role_code("student"):
            return CourseResult.objects.filter(
                enrollment__student=user
            )

        return CourseResult.objects.filter(
            enrollment__course_offering__institution=user.institution
        )


class CertificateTemplateViewSet(ModelViewSet):
    serializer_class = CertificateTemplateSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    required_permissions = {
        "GET": "COURSES_VIEW",
        "POST": "COURSES_MANAGE",
        "PUT": "COURSES_MANAGE",
        "PATCH": "COURSES_MANAGE",
        "DELETE": "COURSES_MANAGE",
    }

    queryset = CertificateTemplate.objects.all()


class CertificateViewSet(ModelViewSet):
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    required_permissions = {
        "GET": "COURSES_VIEW",
        "POST": "COURSES_MANAGE",
        "PUT": "COURSES_MANAGE",
        "PATCH": "COURSES_MANAGE",
        "DELETE": "COURSES_MANAGE",
    }

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Certificate.objects.all()

        if user.has_role_code("student"):
            return Certificate.objects.filter(student=user)

        return Certificate.objects.filter(
            course_offering__institution=user.institution
        )

    def perform_create(self, serializer):
        certificate_no = f"CERT-{uuid.uuid4().hex[:10].upper()}"

        serializer.save(
            certificate_no=certificate_no,
            issue_date=date.today()
        )
