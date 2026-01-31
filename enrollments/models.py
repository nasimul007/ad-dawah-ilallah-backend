from django.conf import settings
from django.db import models


class EnrollmentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    CANCELLED = "CANCELLED", "Cancelled"
    EXPIRED = "EXPIRED", "Expired"


class EnrollmentKind(models.TextChoices):
    ONE_TIME = "ONE_TIME", "One-time"
    SUBSCRIPTION = "SUBSCRIPTION", "Subscription"


class Enrollment(models.Model):
    """
    Tracks a user's enrollment in a course.
    Payment lives in the payments app; payments will link back to Enrollment via FK.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )

    kind = models.CharField(max_length=20, choices=EnrollmentKind.choices)
    status = models.CharField(max_length=20, choices=EnrollmentStatus.choices, default=EnrollmentStatus.ACTIVE)

    starts_at = models.DateTimeField(auto_now_add=True)
    ends_at = models.DateTimeField(null=True, blank=True, help_text="For subscriptions, when access expires")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["user", "course"]]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} -> {self.course_id} ({self.status})"





