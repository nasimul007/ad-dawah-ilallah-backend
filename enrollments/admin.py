from django.contrib import admin

from enrollments.models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "kind", "status", "starts_at", "ends_at", "created_at")
    list_filter = ("kind", "status", "created_at")
    search_fields = ("user__username", "user__full_name", "course__title")
    ordering = ("-created_at",)





