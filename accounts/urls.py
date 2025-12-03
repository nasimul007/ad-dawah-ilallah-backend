from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import UserViewSet, RoleViewSet, PermissionViewSet
from accounts.auth_views import LoginView, RefreshTokenView


router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("roles", RoleViewSet, basename="roles")
router.register("permissions", PermissionViewSet, basename="permissions")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    path("", include(router.urls)),
]
