from rest_framework import serializers

from .models import Institution, Department


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = (
            "id",
            "name",
            "code",
            "type",
            "address",
            "phone",
            "email",
            "website_url",
            "parent_institution",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class DepartmentSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(
        source="institution.name", read_only=True
    )

    class Meta:
        model = Department
        fields = (
            "id",
            "institution",
            "institution_name",
            "name",
            "code",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")