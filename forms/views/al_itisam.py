from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from forms.models import AlItisamRegistration
from forms.serializers import AlItisamRegistrationSerializer


class AlItisamRegistrationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Al Itisam Registration.
    POST (create) is public, other operations require admin authentication.
    """
    queryset = AlItisamRegistration.objects.all().order_by("-created_at")
    serializer_class = AlItisamRegistrationSerializer

    def get_permissions(self):
        """
        Allow public access for POST (create), require admin for other operations.
        """
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

