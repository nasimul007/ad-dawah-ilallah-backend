from django.db import models


class ProfessionChoices(models.TextChoices):
    TEACHER = "শিক্ষক", "শিক্ষক"
    DOCTOR = "ডাক্তার", "ডাক্তার"
    ENGINEER = "ইঞ্জিনিয়ার", "ইঞ্জিনিয়ার"
    LAWYER = "আইনজীবী", "আইনজীবী"
    FARMER = "কৃষক", "কৃষক"
    BUSINESSMAN = "ব্যবসায়ী", "ব্যবসায়ী"
    EMPLOYEE = "চাকরিজীবী", "চাকরিজীবী"
    FREELANCER = "ফ্রিল্যান্সার", "ফ্রিল্যান্সার"
    STUDENT = "ছাত্র", "ছাত্র"
    PHYSICIAN = "চিকিৎসক", "চিকিৎসক"
    OTHER = "অন্যান্য", "অন্যান্য"


class InterestedPersonChoices(models.TextChoices):
    SELF = "নিজে আসতে চায়", "নিজে আসতে চায়"
    SEND_OTHER = "অন্য কাউকে পাঠাতে চায়", "অন্য কাউকে পাঠাতে চায়"


class CourseSourceChoices(models.TextChoices):
    FACEBOOK_POST = "ফেসবুক পোস্টের মাধ্যমে", "ফেসবুক পোস্টের মাধ্যমে"
    SPEECH = "বক্তব্যের মাধ্যমে", "বক্তব্যের মাধ্যমে"
    ACQUAINTANCE = "পরিচিত ব্যক্তির মাধ্যমে", "পরিচিত ব্যক্তির মাধ্যমে"
    OTHER = "অন্যান্য", "অন্যান্য"


class MosqueCourseRegistration(models.Model):
    """Model for mosque course registration form submissions"""
    
    mosque_name = models.CharField(max_length=255, verbose_name="Mosque Name")
    full_name_bangla = models.CharField(max_length=255, verbose_name="Full Name (Bangla)")
    full_name_english = models.CharField(max_length=255, verbose_name="Full Name (English)")
    email = models.EmailField(verbose_name="Email")
    mobile_number = models.CharField(max_length=20, verbose_name="Mobile Number")
    mosque_address = models.TextField(verbose_name="Full Mosque Address")
    upazila = models.CharField(max_length=100, verbose_name="Upazila")
    district = models.CharField(max_length=100, verbose_name="District")
    profession = models.CharField(
        max_length=50,
        choices=ProfessionChoices.choices,
        verbose_name="Profession"
    )
    interested_person = models.CharField(
        max_length=50,
        choices=InterestedPersonChoices.choices,
        verbose_name="Interested Person"
    )
    course_source = models.CharField(
        max_length=50,
        choices=CourseSourceChoices.choices,
        verbose_name="How did you learn about this course?"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Mosque Course Registration"
        verbose_name_plural = "Mosque Course Registrations"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.full_name_english} - {self.mosque_name}"
