from django.contrib import admin

from payments.models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "tran_id",
        "user",
        "course",
        "enrollment",
        "kind",
        "amount",
        "currency",
        "status",
        "paid_at",
        "created_at",
    )
    list_filter = ("status", "kind", "currency", "created_at")
    search_fields = ("tran_id", "user__username", "user__full_name", "val_id", "bank_tran_id")
    ordering = ("-created_at",)


