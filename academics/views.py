from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter

from academics.models import AcademicTerm, Course
from accounts.permissions import HasPermissionCode
from .serializers import AcademicTermSerializer, CourseSerializer
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
