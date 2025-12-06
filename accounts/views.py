from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.filters import UserFilter, PermissionFilter, RoleFilter
from accounts.models import User, Role, Permission
from accounts.serializers import UserSerializer, RoleSerializer, PermissionSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-id")
    serializer_class = UserSerializer

    filter_backends = [OrderingFilter]
    filterset_class = UserFilter
    ordering_fields = ["id", "username", "full_name", "created_at"]

    # Endpoint to get the current authenticated user
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    # ------------------------------------------
    # DELETE MULTIPLE USERS
    # ------------------------------------------
    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        ids = request.data.get("ids", [])

        if not ids or not isinstance(ids, list):
            return Response(
                {"detail": "Provide a list of user IDs."},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted_count, _ = User.objects.filter(id__in=ids).delete()

        return Response(
            {"deleted": deleted_count},
            status=status.HTTP_200_OK
        )


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().order_by("name")
    serializer_class = RoleSerializer

    filterset_class = RoleFilter
    filter_backends = [OrderingFilter]
    ordering_fields = ["id", "name"]

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        ids = request.data.get("ids", [])

        if not ids or not isinstance(ids, list):
            return Response(
                {"detail": "Provide a list of role IDs."},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted_count, _ = Role.objects.filter(id__in=ids).delete()

        return Response(
            {"deleted": deleted_count},
            status=status.HTTP_200_OK
        )


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API for permissions.
    Only supports: list (GET) and retrieve (GET /{id}/)
    """
    queryset = Permission.objects.all().order_by("module", "code")
    serializer_class = PermissionSerializer
    filterset_class = PermissionFilter