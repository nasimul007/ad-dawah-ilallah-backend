from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from forms.models import KhutbaRegistration
from forms.serializers import KhutbaRegistrationSerializer


class KhutbaRegistrationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Khutba Registration.
    POST (create) is public, other operations require admin authentication.
    """
    queryset = KhutbaRegistration.objects.all().order_by("-created_at")
    serializer_class = KhutbaRegistrationSerializer

    def get_permissions(self):
        """
        Allow public access for POST (create), require admin for other operations.
        """
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


