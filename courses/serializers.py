from rest_framework import serializers
from courses.models import Course, Module, CourseContent


class CourseContentSerializer(serializers.ModelSerializer):
    """Serializer for CourseContent"""
    
    class Meta:
        model = CourseContent
        fields = [
            "id",
            "title",
            "content_type",
            "content",
            "file_url",
            "duration_minutes",
            "order",
            "is_free",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for Module with nested contents"""
    contents = CourseContentSerializer(many=True, read_only=True)
    contents_count = serializers.IntegerField(source='contents.count', read_only=True)
    
    class Meta:
        model = Module
        fields = [
            "id",
            "course",
            "title",
            "description",
            "order",
            "contents",
            "contents_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course with nested modules"""
    modules = ModuleSerializer(many=True, read_only=True)
    modules_count = serializers.IntegerField(source='modules.count', read_only=True)
    instructor_name = serializers.CharField(source='instructor.full_name', read_only=True)
    
    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "instructor",
            "instructor_name",
            "thumbnail_url",
            "is_active",
            "is_published",
            "order",
            "modules",
            "modules_count",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "instructor_name", "modules_count"]


class CourseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for course lists (without nested modules)"""
    modules_count = serializers.IntegerField(source='modules.count', read_only=True)
    instructor_name = serializers.CharField(source='instructor.full_name', read_only=True)
    
    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "instructor",
            "instructor_name",
            "thumbnail_url",
            "is_active",
            "is_published",
            "order",
            "modules_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "instructor_name", "modules_count"]

