from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from enrollments.models import Enrollment
from enrollments.serializers import EnrollmentSerializer


class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoints for users to view their enrollments.
    """

    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user).order_by("-created_at")





