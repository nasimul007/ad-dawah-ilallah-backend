from django.db import models
from accounts.models import User


class Course(models.Model):
    """Main course model"""
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    instructors = models.ManyToManyField(
        User,
        blank=True,
        related_name="courses_taught",
        help_text="Users who teach this course",
    )
    thumbnail_url = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    
    # Ordering
    order = models.IntegerField(default=0, help_text="Order in which course appears")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses_created"
    )
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Course"
        verbose_name_plural = "Courses"
    
    def __str__(self):
        return self.title


class Module(models.Model):
    """Module belongs to a Course"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="modules"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    
    # Ordering within the course
    order = models.IntegerField(default=0, help_text="Order within the course")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        unique_together = [['course', 'order']]
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class CourseContent(models.Model):
    """Content items within a Module"""
    
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('text', 'Text'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('exam', 'Exam'),
    ]
    
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="contents"
    )
    title = models.CharField(max_length=255)
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='text'
    )
    content = models.TextField(
        null=True,
        blank=True,
        help_text="Text content or description"
    )
    file_url = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL to video, PDF, audio file, or external link"
    )
    duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duration in minutes (for video/audio)" 
    )
    
    # Ordering within the module
    order = models.IntegerField(default=0, help_text="Order within the module")
    
    is_free = models.BooleanField(
        default=False,
        help_text="Whether this content is free to access"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Course Content"
        verbose_name_plural = "Course Contents"
        unique_together = [['module', 'order']]
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"

