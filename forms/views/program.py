from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from forms.models import ProgramRegistration
from forms.serializers import ProgramRegistrationSerializer


class ProgramRegistrationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Program Registration.
    POST (create) is public, other operations require admin authentication.
    """
    queryset = ProgramRegistration.objects.all().order_by("-created_at")
    serializer_class = ProgramRegistrationSerializer

    def get_permissions(self):
        """
        Allow public access for POST (create), require admin for other operations.
        """
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

