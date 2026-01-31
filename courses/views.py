from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.models import Course, Module, CourseContent
from courses.serializers import (
    CourseSerializer,
    CourseListSerializer,
    ModuleSerializer,
    CourseContentSerializer
)


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet for Course model"""
    queryset = Course.objects.all().order_by('order', '-created_at')
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['order', 'created_at', 'title']
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use lightweight serializer for list, full serializer for detail"""
        if self.action == 'list':
            return CourseListSerializer
        return CourseSerializer

    def perform_create(self, serializer):
        # created_by should be set automatically from the authenticated user
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def modules(self, request, pk=None):
        """Get all modules for a specific course"""
        course = self.get_object()
        modules = course.modules.all().order_by('order')
        serializer = ModuleSerializer(modules, many=True)
        return Response(serializer.data)


class ModuleViewSet(viewsets.ModelViewSet):
    """ViewSet for Module model"""
    queryset = Module.objects.all().order_by('order', '-created_at')
    serializer_class = ModuleSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['order', 'created_at', 'title']
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Optionally filter by course"""
        queryset = super().get_queryset()
        course_id = self.request.query_params.get('course', None)
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset
    
    @action(detail=True, methods=['get'])
    def contents(self, request, pk=None):
        """Get all contents for a specific module"""
        module = self.get_object()
        contents = module.contents.all().order_by('order')
        serializer = CourseContentSerializer(contents, many=True)
        return Response(serializer.data)


class CourseContentViewSet(viewsets.ModelViewSet):
    """ViewSet for CourseContent model"""
    queryset = CourseContent.objects.all().order_by('order', '-created_at')
    serializer_class = CourseContentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['order', 'created_at', 'title']
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Optionally filter by module"""
        queryset = super().get_queryset()
        module_id = self.request.query_params.get('module', None)
        if module_id:
            queryset = queryset.filter(module_id=module_id)
        return queryset

