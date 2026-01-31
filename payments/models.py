from django.conf import settings
from django.db import models


class PaymentStatus(models.TextChoices):
    INITIATED = "INITIATED", "Initiated"
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"
    INVALID = "INVALID", "Invalid"
    REFUNDED = "REFUNDED", "Refunded"


class PaymentKind(models.TextChoices):
    ONE_TIME = "ONE_TIME", "One-time"
    SUBSCRIPTION = "SUBSCRIPTION", "Subscription"


class PaymentTransaction(models.Model):
    """
    Stores SSLCOMMERZ payment attempts and results.

    Enrollment is intentionally NOT handled here (will live in a separate app).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_transactions",
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_transactions",
        help_text="Course being purchased (optional for subscription payments)",
    )
    enrollment = models.ForeignKey(
        "enrollments.Enrollment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        help_text="Enrollment created after successful payment",
    )
    kind = models.CharField(max_length=20, choices=PaymentKind.choices)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="BDT")

    tran_id = models.CharField(max_length=64, unique=True)
    sessionkey = models.CharField(max_length=128, null=True, blank=True)
    gateway_page_url = models.URLField(max_length=500, null=True, blank=True)

    status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.INITIATED
    )

    # SSLCOMMERZ fields (from callback/IPN/validation API)
    val_id = models.CharField(max_length=128, null=True, blank=True)
    bank_tran_id = models.CharField(max_length=128, null=True, blank=True)
    card_type = models.CharField(max_length=64, null=True, blank=True)
    store_amount = models.CharField(max_length=32, null=True, blank=True)
    verify_sign = models.CharField(max_length=128, null=True, blank=True)
    verify_sign_sha2 = models.CharField(max_length=256, null=True, blank=True)
    risk_level = models.CharField(max_length=32, null=True, blank=True)
    risk_title = models.CharField(max_length=64, null=True, blank=True)

    # Store raw payloads/responses for debugging/audit
    init_response = models.JSONField(null=True, blank=True)
    callback_payload = models.JSONField(null=True, blank=True)
    validation_response = models.JSONField(null=True, blank=True)

    # Extra metadata (e.g., subscription period)
    meta = models.JSONField(default=dict, blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tran_id} ({self.status})"


