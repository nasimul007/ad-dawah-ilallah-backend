from django.db import models

from forms.models.field_choices import DeliveryMediumChoices, DistrictChoices

class AlItisamRegistration(models.Model):
    """Model for Al Itisam magazine registration form submissions"""
    
    your_name = models.CharField(
        max_length=255,
        verbose_name="Your Name"
    )
    email = models.EmailField(
        verbose_name="Email"
    )
    mobile_number = models.CharField(
        max_length=20,
        verbose_name="Mobile Number"
    )
    village_locality_institution = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Village/Locality/Institution"
    )
    post = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Post"
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
    how_many_copies = models.IntegerField(
        verbose_name="How many copies will you take?",
        help_text="Number of copies"
    )
    delivery_medium = models.CharField(
        max_length=20,
        choices=DeliveryMediumChoices.choices,
        verbose_name="Through which medium will you take?",
        help_text="Post or Courier"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Al Itisam Registration"
        verbose_name_plural = "Al Itisam Registrations"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.your_name} - {self.how_many_copies} copies"
