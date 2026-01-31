from django.contrib import admin
from courses.models import Course, Module, CourseContent


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructors_list', 'is_active', 'is_published', 'order', 'created_at')
    list_filter = ('is_active', 'is_published', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('order', '-created_at')

    def instructors_list(self, obj):
        return ", ".join(obj.instructors.values_list("full_name", flat=True))

    instructors_list.short_description = "Instructors"


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('course', 'order', '-created_at')


@admin.register(CourseContent)
class CourseContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'content_type', 'order', 'is_free', 'created_at')
    list_filter = ('content_type', 'is_free', 'module__course', 'created_at')
    search_fields = ('title', 'content')
    ordering = ('module', 'order', '-created_at')

