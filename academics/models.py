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


class CourseOffering(models.Model):
    MODE_CHOICES = (
        ("online", "Online"),
        ("offline", "Offline"),
        ("hybrid", "Hybrid"),
    )

    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="course_offerings"
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="offerings"
    )

    academic_term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.PROTECT,
        related_name="course_offerings"
    )

    section_code = models.CharField(max_length=50, blank=True, null=True)

    mode = models.CharField(
        max_length=20,
        choices=MODE_CHOICES
    )

    max_students = models.PositiveIntegerField(blank=True, null=True)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    coordinator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="coordinated_offerings"
    )

    primary_educator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="primary_teaching_offerings"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )

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
        db_table = "course_offerings"
        ordering = ["-created_at"]
        unique_together = (
            "institution",
            "course",
            "academic_term",
            "section_code",
        )

    def __str__(self):
        return f"{self.course.code} ({self.academic_term.name})"


class CourseInstructor(models.Model):
    ROLE_CHOICES = (
        ("primary", "Primary"),
        ("assistant", "Assistant"),
        ("guest", "Guest"),
    )

    course_offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name="instructors"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="teaching_assignments"
    )

    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default="assistant"
    )

    class Meta:
        db_table = "course_instructors"
        unique_together = ("course_offering", "user")

