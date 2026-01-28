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


class CourseEnrollment(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("dropped", "Dropped"),
        ("failed", "Failed"),
    )

    ENROLLMENT_SOURCE_CHOICES = (
        ("self", "Self"),
        ("admin", "Admin"),
        ("coordinator", "Coordinator"),
    )

    course_offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="course_enrollments"
    )

    enrollment_date = models.DateField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    enrollment_source = models.CharField(
        max_length=50,
        choices=ENROLLMENT_SOURCE_CHOICES,
        default="admin"
    )

    remarks = models.TextField(blank=True, null=True)

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
        db_table = "course_enrollments"
        unique_together = ("course_offering", "student")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.full_name} → {self.course_offering}"


class ClassRoutine(models.Model):
    WEEKDAY_CHOICES = (
        (0, "Sunday"),
        (1, "Monday"),
        (2, "Tuesday"),
        (3, "Wednesday"),
        (4, "Thursday"),
        (5, "Friday"),
        (6, "Saturday"),
    )

    CLASS_TYPE_CHOICES = (
        ("lecture", "Lecture"),
        ("tutorial", "Tutorial"),
        ("qa", "Q&A"),
    )

    course_offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name="class_routines"
    )

    weekday = models.PositiveSmallIntegerField(
        choices=WEEKDAY_CHOICES
    )

    start_time = models.TimeField()
    end_time = models.TimeField()

    class_type = models.CharField(
        max_length=50,
        choices=CLASS_TYPE_CHOICES,
        default="lecture"
    )

    location = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    zoom_link = models.URLField(blank=True, null=True)
    youtube_link = models.URLField(blank=True, null=True)

    class Meta:
        db_table = "class_routines"
        unique_together = (
            "course_offering",
            "weekday",
            "start_time",
        )
        ordering = ["weekday", "start_time"]

    def __str__(self):
        return f"{self.course_offering} | {self.get_weekday_display()}"


class ClassSession(models.Model):
    CLASS_TYPE_CHOICES = (
        ("lecture", "Lecture"),
        ("tutorial", "Tutorial"),
        ("qa", "Q&A"),
    )

    course_offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name="class_sessions"
    )

    session_date = models.DateField()

    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    topic = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    class_type = models.CharField(
        max_length=50,
        choices=CLASS_TYPE_CHOICES,
        default="lecture"
    )

    recording_url = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "class_sessions"
        unique_together = (
            "course_offering",
            "session_date",
        )
        ordering = ["-session_date"]

    def __str__(self):
        return f"{self.course_offering} | {self.session_date}"


class Attendance(models.Model):
    STATUS_CHOICES = (
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("excused", "Excused"),
    )

    class_session = models.ForeignKey(
        ClassSession,
        on_delete=models.CASCADE,
        related_name="attendances"
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="attendances"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )

    check_in_time = models.DateTimeField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    marked_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+"
    )

    class Meta:
        db_table = "attendance"
        unique_together = ("class_session", "student")
        ordering = ["student__full_name"]

    def __str__(self):
        return f"{self.student.full_name} | {self.class_session}"
