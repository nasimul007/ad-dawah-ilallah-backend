from django.db import models
from forms.models.field_choices import CourseSourceChoices, DistrictChoices


class QuranAndDeenCourse(models.Model):
    """Model for Quran and Deen course registration form submissions"""
    
    full_name_bangla = models.CharField(max_length=255, verbose_name="Full Name (Bangla)")
    full_name_english = models.CharField(max_length=255, verbose_name="Full Name (English)")
    email = models.EmailField(verbose_name="Email")
    mobile_number = models.CharField(max_length=20, verbose_name="Mobile Number")
    village_locality = models.CharField(max_length=255, verbose_name="Village/Locality")
    post_office = models.CharField(max_length=255, verbose_name="Post Office")
    upazila = models.CharField(max_length=100, verbose_name="Upazila")
    district = models.CharField(
        max_length=100,
        choices=DistrictChoices.choices,
        verbose_name="District"
    )
    date_of_birth = models.DateField(verbose_name="Date of Birth")
    current_age = models.IntegerField(verbose_name="Current Age")
    course_source = models.CharField(
        max_length=50,
        choices=CourseSourceChoices.choices,
        verbose_name="How did you learn about this course?"
    )
    photo_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Photo URL",
        help_text="URL of the uploaded photo"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Quran and Deen Course Registration"
        verbose_name_plural = "Quran and Deen Course Registrations"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.full_name_english} - {self.district}"
