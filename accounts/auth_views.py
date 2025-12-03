from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .auth_serializers import AdDawahTokenObtainPairSerializer


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = AdDawahTokenObtainPairSerializer


class RefreshTokenView(TokenRefreshView):
    permission_classes = [AllowAny]
