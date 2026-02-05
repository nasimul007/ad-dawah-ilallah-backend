from django.db import models
from accounts.models import User


class FileUpload(models.Model):
    owner = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_files"
    )

    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to="uploads/%Y/%m/")
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    size_bytes = models.BigIntegerField(blank=True, null=True)

    used_for = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    entity_type = models.CharField(
        max_length=50
    )
    entity_id = models.BigIntegerField()

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "file_uploads"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.original_filename
