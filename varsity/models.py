from django.db import models

class Varsity(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class PrintingPoint(models.Model):
    varsity = models.ForeignKey(Varsity, on_delete=models.CASCADE, related_name="printing_points")
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.varsity.name} - {self.name}"

class Printer(models.Model):
    printing_point = models.OneToOneField(PrintingPoint, on_delete=models.CASCADE, related_name="printer")
    name = models.CharField(max_length=255)
    connected_user = models.ForeignKey(
        "accounts.User", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="connected_printers"
    )

    def __str__(self):
        return self.name

