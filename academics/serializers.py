from django.utils.timezone import now
from rest_framework import serializers
from academics.models import AcademicTerm, Course, CourseInstructor, CourseOffering, CourseEnrollment, ClassRoutine, \
    ClassSession, Attendance, Assignment, AssignmentSubmission


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


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollment
        fields = [
            "id",
            "course_offering",
            "student",
            "enrollment_date",
            "status",
            "enrollment_source",
            "remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "enrollment_date",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        course_offering = attrs.get("course_offering")
        student = attrs.get("student")

        if not course_offering:
            return attrs

        # Capacity check
        if course_offering.max_students:
            active_count = course_offering.enrollments.filter(
                status__in=["pending", "active"]
            ).count()

            if active_count >= course_offering.max_students:
                raise serializers.ValidationError(
                    "This course offering has reached maximum capacity."
                )

        return attrs


class ClassRoutineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassRoutine
        fields = [
            "id",
            "course_offering",
            "weekday",
            "start_time",
            "end_time",
            "class_type",
            "location",
            "zoom_link",
            "youtube_link",
        ]

    def validate(self, attrs):
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError(
                "End time must be after start time."
            )
        return attrs


class ClassSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSession
        fields = [
            "id",
            "course_offering",
            "session_date",
            "start_time",
            "end_time",
            "topic",
            "class_type",
            "recording_url",
            "notes",
        ]

    def validate(self, attrs):
        start = attrs.get("start_time")
        end = attrs.get("end_time")

        if start and end and start >= end:
            raise serializers.ValidationError(
                "End time must be after start time."
            )
        return attrs


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = [
            "id",
            "class_session",
            "student",
            "status",
            "check_in_time",
            "remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at")

    def validate(self, attrs):
        class_session = attrs.get("class_session")
        student = attrs.get("student")

        if not class_session or not student:
            return attrs

        # Ensure student is enrolled in this course offering
        is_enrolled = CourseEnrollment.objects.filter(
            course_offering=class_session.course_offering,
            student=student,
            status__in=["pending", "active", "completed"]
        ).exists()

        if not is_enrolled:
            raise serializers.ValidationError(
                "Student is not enrolled in this course offering."
            )

        return attrs


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            "id",
            "course_offering",
            "title",
            "description",
            "type",
            "max_marks",
            "due_at",
            "allow_late_submission",
            "late_penalty_percent",
            "instruction_file",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at")

    def validate(self, attrs):
        if (
            attrs.get("allow_late_submission") is False
            and attrs.get("late_penalty_percent")
        ):
            raise serializers.ValidationError(
                "Late penalty is not applicable if late submission is disabled."
            )
        return attrs


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = [
            "id",
            "assignment",
            "student",
            "submitted_at",
            "text_answer",
            "attachment",
            "marks_obtained",
            "feedback",
            "graded_by",
            "graded_at",
        ]
        read_only_fields = (
            "submitted_at",
            "marks_obtained",
            "feedback",
            "graded_by",
            "graded_at",
        )

    def validate(self, attrs):
        assignment = attrs.get("assignment")
        student = attrs.get("student")

        # Ensure student is enrolled
        is_enrolled = CourseEnrollment.objects.filter(
            course_offering=assignment.course_offering,
            student=student,
            status__in=["pending", "active", "completed"],
        ).exists()

        if not is_enrolled:
            raise serializers.ValidationError(
                "Student is not enrolled in this course offering."
            )

        # Due date check
        if assignment.due_at < now() and not assignment.allow_late_submission:
            raise serializers.ValidationError(
                "Assignment submission deadline has passed."
            )

        return attrs
