from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from accounts.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-id")
    serializer_class = UserSerializer

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
