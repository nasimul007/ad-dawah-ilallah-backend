from rest_framework import serializers

from payments.models import PaymentTransaction


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = [
            "id",
            "user",
            # "course",
            "print_order",
            # "enrollment",


            "kind",
            "amount",
            "currency",
            "tran_id",
            "sessionkey",
            "gateway_page_url",
            "status",
            "val_id",
            "bank_tran_id",
            "card_type",
            "store_amount",
            "risk_level",
            "risk_title",
            "meta",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "sessionkey",
            "gateway_page_url",
            "status",
            "val_id",
            "bank_tran_id",
            "card_type",
            "store_amount",
            "risk_level",
            "risk_title",
            # "enrollment",
            "paid_at",
            "created_at",
            "updated_at",
        ]



class CheckoutSerializer(serializers.Serializer):
    """
    Request body for starting a checkout session.
    """

    # course_id = serializers.IntegerField(required=False)
    print_order_id = serializers.IntegerField(required=False)

    kind = serializers.ChoiceField(choices=["ONE_TIME", "SUBSCRIPTION"])
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    currency = serializers.CharField(required=False, default="BDT")

    # subscription metadata (optional)
    subscription_plan = serializers.CharField(required=False, allow_blank=True)
    subscription_months = serializers.IntegerField(required=False, min_value=1)


