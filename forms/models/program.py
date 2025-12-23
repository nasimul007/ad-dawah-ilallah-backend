
from django.db import models

from forms.models.field_choices import DistrictChoices, ProgramTimeChoices, ProgramTypeChoices, YesNoChoices


class ProgramRegistration(models.Model):
    """Model for program registration form submissions"""
    
    # Text fields
    responsible_person_name = models.CharField(
        max_length=255,
        verbose_name="Responsible Person's Name"
    )
    field_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Field/Ground Name"
    )
    village = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Village"
    )
    post_office = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Post Office"
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Postal Code"
    )
    upazila = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Upazila"
    )
    division = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Division"
    )
    reference_person_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Reference Person's Name"
    )
    
    # Number field
    responsible_person_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Responsible Person's Number"
    )
    
    # Select/Dropdown fields
    program_type = models.CharField(
        max_length=50,
        choices=ProgramTypeChoices.choices,
        blank=True,
        null=True,
        verbose_name="Program Type"
    )
    district = models.CharField(
        max_length=100,
        choices=DistrictChoices.choices,
        blank=True,
        null=True,
        verbose_name="District"
    )
    
    # Date field
    program_probable_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Program's Probable Date"
    )
    
    # File upload (URL)
    venue_google_location_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Venue's Google Location URL",
        help_text="URL of the uploaded Google location file (PDF, PNG, JPEG)"
    )
    
    # Checkbox groups (stored as JSON)
    program_fund_collection = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Program Fund Collection",
        help_text="List of selected fund collection sources"
    )
    speakers = models.JSONField(
        default=list,
        verbose_name="Speakers",
        help_text="List of selected speakers (at least one required)"
    )
    
    # Radio button groups
    program_time = models.CharField(
        max_length=50,
        choices=ProgramTimeChoices.choices,
        blank=True,
        null=True,
        verbose_name="Program Time"
    )
    participated_quran_deen_course = models.CharField(
        max_length=10,
        choices=YesNoChoices.choices,
        blank=True,
        null=True,
        verbose_name="Have you participated in Quran and Deen education course?"
    )
    mosque_has_maktab = models.CharField(
        max_length=10,
        choices=YesNoChoices.choices,
        blank=True,
        null=True,
        verbose_name="Does the mosque have a Maktab?"
    )
    attend_salafi_conferences = models.CharField(
        max_length=10,
        choices=YesNoChoices.choices,
        blank=True,
        null=True,
        verbose_name="Do you attend Salafi conferences?"
    )
    subscriber_al_itisam = models.CharField(
        max_length=10,
        choices=YesNoChoices.choices,
        blank=True,
        null=True,
        verbose_name="Are you a subscriber of monthly Al Itisam?"
    )
    affiliated_jamiah_salafiyyah = models.CharField(
        max_length=10,
        choices=YesNoChoices.choices,
        blank=True,
        null=True,
        verbose_name="Affiliated with Jami'ah Salafiyyah?"
    )
    participated_3day_madrasa = models.CharField(
        max_length=10,
        choices=YesNoChoices.choices,
        blank=True,
        null=True,
        verbose_name="Have you participated in 3-day Madrasa?"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Program Registration"
        verbose_name_plural = "Program Registrations"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.responsible_person_name} - {self.program_type or 'N/A'}"
