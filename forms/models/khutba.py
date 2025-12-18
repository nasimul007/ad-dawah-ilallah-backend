
from django.db import models

from forms.models.field_choices import DistrictChoices


class KhutbaRegistration(models.Model):
    """Model for Khutba registration form submissions"""
    
    mosque_name = models.CharField(
        max_length=255,
        verbose_name="Mosque Name"
    )
    village_locality_street = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Village/Locality/Street Name"
    )
    post_office = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Post Office"
    )
    upazila = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Upazila"
    )
    district = models.CharField(
        max_length=100,
        choices=DistrictChoices.choices,
        blank=True,
        null=True,
        verbose_name="District"
    )
    mosque_responsible_person_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Mosque Responsible Person's Name"
    )
    responsible_person_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Responsible Person's Number"
    )
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="WhatsApp Number"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email"
    )
    mosque_google_location_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Mosque Google Location URL",
        help_text="URL of the uploaded Google location file (PDF, PNG, JPEG)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Khutba Registration"
        verbose_name_plural = "Khutba Registrations"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.mosque_name} - {self.district or 'N/A'}"
