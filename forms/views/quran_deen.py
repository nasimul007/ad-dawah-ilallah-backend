from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from forms.models import QuranAndDeenCourse
from forms.serializers import QuranAndDeenCourseSerializer


class QuranAndDeenCourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Quran and Deen Course Registration.
    POST (create) is public, other operations require admin authentication.
    """
    queryset = QuranAndDeenCourse.objects.all().order_by("-created_at")
    serializer_class = QuranAndDeenCourseSerializer

    def get_permissions(self):
        """
        Allow public access for POST (create), require admin for other operations.
        """
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


