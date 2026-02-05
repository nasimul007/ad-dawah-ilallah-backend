from django.db import models

class Institution(models.Model):
    TYPE_CHOICES = (
        ("main", "Main"),
        ("branch", "Branch"),
        ("affiliate", "Affiliate"),
    )

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, null=True, blank=True)

    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=25, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)

    parent_institution = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="branches"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "institutions"

    def __str__(self):
        return self.name


class Department(models.Model):
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="departments"
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "departments"
        unique_together = ("institution", "code")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"