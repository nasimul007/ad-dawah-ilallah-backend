from django.db import models
from institutions.models import Institution
from accounts.models import User


class AcademicTerm(models.Model):
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="academic_terms"
    )

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    is_current = models.BooleanField(default=False)

    # audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )

    class Meta:
        db_table = "academic_terms"
        ordering = ["-start_date"]
        unique_together = ("institution", "name")

    def __str__(self):
        return f"{self.name} ({self.institution.code})"


class Course(models.Model):
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="courses"
    )
    code = models.CharField(max_length=50)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    level = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    credit_hours = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    default_duration_weeks = models.PositiveIntegerField(
        blank=True, null=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )

    class Meta:
        db_table = "courses"
        unique_together = ("institution", "code")
        ordering = ["title"]

    def __str__(self):
        return f"{self.code} - {self.title}"







