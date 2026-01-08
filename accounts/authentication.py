from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads the access token from HTTP cookies
    instead of the Authorization header.
    """
    
    def authenticate(self, request):
        # Get the token from cookie instead of header
        raw_token = request.COOKIES.get('access_token')
        
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken:
            return None

