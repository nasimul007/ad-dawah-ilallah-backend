from rest_framework import serializers
from academics.models import AcademicTerm, Course, CourseInstructor, CourseOffering


class AcademicTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicTerm
        fields = [
            "id",
            "institution",
            "name",
            "start_date",
            "end_date",
            "is_current",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at")

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")

        if start and end and start >= end:
            raise serializers.ValidationError(
                "End date must be after start date."
            )

        return attrs


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id",
            "institution",
            "code",
            "title",
            "description",
            "level",
            "category",
            "credit_hours",
            "default_duration_weeks",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at")

    def validate_code(self, value):
        return value.upper()


class CourseInstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseInstructor
        fields = ["id", "user", "role"]


class CourseOfferingSerializer(serializers.ModelSerializer):
    instructors = CourseInstructorSerializer(many=True, required=False)

    class Meta:
        model = CourseOffering
        fields = [
            "id",
            "institution",
            "course",
            "academic_term",
            "section_code",
            "mode",
            "max_students",
            "start_date",
            "end_date",
            "coordinator",
            "primary_educator",
            "status",
            "instructors",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at")

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")

        if start and end and start > end:
            raise serializers.ValidationError(
                "End date must be after start date."
            )
        return attrs

    def create(self, validated_data):
        instructors_data = validated_data.pop("instructors", [])
        offering = CourseOffering.objects.create(**validated_data)

        for instructor in instructors_data:
            CourseInstructor.objects.create(
                course_offering=offering,
                **instructor
            )

        return offering

    def update(self, instance, validated_data):
        instructors_data = validated_data.pop("instructors", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if instructors_data is not None:
            instance.instructors.all().delete()
            for instructor in instructors_data:
                CourseInstructor.objects.create(
                    course_offering=instance,
                    **instructor
                )

        return instance
