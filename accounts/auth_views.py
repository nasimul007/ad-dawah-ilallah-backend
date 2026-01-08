from datetime import timedelta
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.settings import api_settings
from django.conf import settings
from .auth_serializers import AdDawahTokenObtainPairSerializer


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = AdDawahTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get tokens from validated data
        access_token = serializer.validated_data.get('access')
        refresh_token = serializer.validated_data.get('refresh')
        user_data = serializer.validated_data.get('user')
        
        # Create response with user data (without tokens in body)
        response = Response(
            {"user": user_data},
            status=status.HTTP_200_OK
        )
        
        # Set access token in cookie
        access_token_lifetime = api_settings.ACCESS_TOKEN_LIFETIME
        if isinstance(access_token_lifetime, timedelta):
            max_age = int(access_token_lifetime.total_seconds())
        else:
            max_age = int(access_token_lifetime)
        
        response.set_cookie(
            key='access_token',
            value=access_token,
            max_age=max_age,
            httponly=True,
            samesite='Lax',
            secure=not settings.DEBUG,  # Use secure cookies in production
        )
        
        # Set refresh token in cookie
        refresh_token_lifetime = api_settings.REFRESH_TOKEN_LIFETIME
        if isinstance(refresh_token_lifetime, timedelta):
            max_age = int(refresh_token_lifetime.total_seconds())
        else:
            max_age = int(refresh_token_lifetime)
        
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            max_age=max_age,
            httponly=True,
            samesite='Lax',
            secure=not settings.DEBUG,  # Use secure cookies in production
        )
        
        return response


class RefreshTokenView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Get refresh token from cookie instead of request body
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response(
                {"detail": "Refresh token not found in cookies."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Create serializer with refresh token from cookie
        serializer = self.get_serializer(data={'refresh': refresh_token})
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get new access token
        access_token = serializer.validated_data.get('access')
        
        # Create response
        response = Response(
            {"detail": "Token refreshed successfully."},
            status=status.HTTP_200_OK
        )
        
        # Set new access token in cookie
        access_token_lifetime = api_settings.ACCESS_TOKEN_LIFETIME
        if isinstance(access_token_lifetime, timedelta):
            max_age = int(access_token_lifetime.total_seconds())
        else:
            max_age = int(access_token_lifetime)
        
        response.set_cookie(
            key='access_token',
            value=access_token,
            max_age=max_age,
            httponly=True,
            samesite='Lax',
            secure=not settings.DEBUG,  # Use secure cookies in production
        )
        
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Create response
        response = Response(
            {"detail": "Successfully logged out."},
            status=status.HTTP_200_OK
        )
        
        # Clear access token cookie
        response.delete_cookie(
            key='access_token',
            samesite='Lax',
            secure=not settings.DEBUG,
        )
        
        # Clear refresh token cookie
        response.delete_cookie(
            key='refresh_token',
            samesite='Lax',
            secure=not settings.DEBUG,
        )
        
        return response
