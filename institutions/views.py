from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import HasPermissionCode
from utils.mixins import InstitutionScopedQuerySetMixin
from .models import Institution, Department
from .serializers import InstitutionSerializer, DepartmentSerializer


class InstitutionViewSet(InstitutionScopedQuerySetMixin, ModelViewSet):
    """
    Institution management (global for superuser)

    only superuser or user with "INSTITUTION_MANAGE" permission can CRUD Institution.
     when a user creates a course, that course will be automatically created under that user's
     Institution
    """

    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    required_permission = "INSTITUTION_MANAGE"
    permission_classes = [IsAuthenticated, HasPermissionCode]


class DepartmentViewSet(InstitutionScopedQuerySetMixin, ModelViewSet):
    """
    Department CRUD under institution

    only superuser or user with "INSTITUTION_MANAGE" permission can CRUD Department.
     when a user creates a course, that course will be automatically created under that user's
     Department
    """

    queryset = Department.objects.select_related("institution")
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    def perform_create(self, serializer):
        user = self.request.user

        # Force institution for non-superusers
        if not user.is_superuser:
            serializer.save(institution=user.institution)
        else:
            serializer.save()