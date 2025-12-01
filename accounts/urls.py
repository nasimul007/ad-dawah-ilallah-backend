from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import UserViewSet, RoleViewSet, PermissionViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("roles", RoleViewSet, basename="roles")
router.register("permissions", PermissionViewSet, basename="permissions")

urlpatterns = [
    path("", include(router.urls)),
]
