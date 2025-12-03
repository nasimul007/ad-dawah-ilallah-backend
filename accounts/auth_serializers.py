from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class AdDawahTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Custom claims in JWT
        token["username"] = user.username
        token["full_name"] = user.full_name
        token["is_active"] = user.is_active
        token["roles"] = list(user.roles.values_list("name", flat=True))

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user

        # Add extra user info in response (besides tokens)
        data["user"] = {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "roles": list(user.roles.values_list("name", flat=True)),
            "is_active": user.is_active,
        }

        return data
