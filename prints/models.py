from django.db import models
from django.conf import settings

class PrintOrder(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", "Received"
        PRINTED = "PRINTED", "Printed"
        SENT = "SENT", "Sent"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="print_orders", null=True, blank=True)
    anon_id = models.UUIDField(null=True, blank=True)
    printer = models.ForeignKey("varsity.Printer", on_delete=models.CASCADE, related_name="print_orders")
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED
    )
    created_at = models.DateTimeField(auto_now_add=True)


    def __get_total_cost(self):
        return sum(p.cost for p in self.prints.all())
    total_cost = property(__get_total_cost)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

class Print(models.Model):
    class Sides(models.TextChoices):
        SINGLE_SIDED = "SINGLE_SIDED", "Single Sided"
        DOUBLE_SIDED = "DOUBLE_SIDED", "Double Sided"

    class Color(models.TextChoices):
        B_W = "B_W", "B&W"
        COLOR = "COLOR", "Color"

    class Pages(models.TextChoices):
        ALL = "ALL", "All"
        CUSTOM = "CUSTOM", "Custom"

    class Slides(models.IntegerChoices):
        ONE = 1, "1"
        TWO = 2, "2"
        FOUR = 4, "4"
        EIGHT = 8, "8"
        SIXTEEN = 16, "16"

    print_order = models.ForeignKey(PrintOrder, on_delete=models.CASCADE, related_name="prints")
    name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=500, null=True, blank=True)
    copies = models.IntegerField(default=1)
    
    sides = models.CharField(max_length=20, choices=Sides.choices, default=Sides.SINGLE_SIDED)
    print_color = models.CharField(max_length=10, choices=Color.choices, default=Color.B_W)
    print_pages = models.CharField(max_length=10, choices=Pages.choices, default=Pages.ALL)
    page_range = models.CharField(max_length=255, null=True, blank=True)
    pages_per_slide = models.IntegerField(choices=Slides.choices, default=Slides.ONE)
    total_pages = models.IntegerField(default=0)

    remaining_printing_options = models.IntegerField(null=True, blank=True)
    cost = models.IntegerField(default=0)

    def __str__(self):
        return self.name

