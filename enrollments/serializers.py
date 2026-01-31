from rest_framework import serializers

from enrollments.models import Enrollment


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = [
            "id",
            "user",
            "course",
            "kind",
            "status",
            "starts_at",
            "ends_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "starts_at", "created_at", "updated_at"]





