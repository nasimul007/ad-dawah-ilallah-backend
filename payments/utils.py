import uuid
from django.urls import reverse
from django.conf import settings
from .models import PaymentTransaction, PaymentKind, PaymentStatus
from .sslcommerz import get_sslcommerz_client

def generate_transaction_id():
    return uuid.uuid4().hex.upper()

def create_payment_session(request, print_order=None,  amount=None, kind="ONE_TIME", currency="BDT", meta=None):
    if not amount:
        if print_order:
            amount = print_order.total_cost
       
    
    tran_id = generate_transaction_id()
    
    # Handle anonymous user
    user = request.user if request.user.is_authenticated else None
    
    payment = PaymentTransaction.objects.create(
        user=user,
        print_order=print_order,
        kind=PaymentKind.ONE_TIME if kind == "ONE_TIME" else PaymentKind.SUBSCRIPTION,
        amount=amount,
        currency=currency,
        tran_id=tran_id,
        status=PaymentStatus.INITIATED,
        meta=meta or {},
    )

    success_url = request.build_absolute_uri(reverse("payments:ssl-success"))
    fail_url = request.build_absolute_uri(reverse("payments:ssl-fail"))
    cancel_url = request.build_absolute_uri(reverse("payments:ssl-cancel"))

    if user:
        cus_name = getattr(user, "full_name", "") or getattr(user, "username", "customer")
        cus_email = getattr(user, "email", "") or "no-reply@example.com"
        cus_phone = getattr(user, "phone", "") or "01700000000"
        cus_add1 = getattr(user, "address", "") or "N/A"
    else:
        cus_name = "Guest Customer"
        cus_email = "guest@example.com"
        cus_phone = "01700000000"
        cus_add1 = "N/A"

    product_name = "Subscription"
    if print_order:
        product_name = print_order.name

    post_body = {
        "total_amount": float(payment.amount),
        "currency": payment.currency,
        "tran_id": payment.tran_id,
        "success_url": success_url,
        "fail_url": fail_url,
        "cancel_url": cancel_url,
        "emi_option": 0,
        "cus_name": cus_name,
        "cus_email": cus_email,
        "cus_phone": cus_phone,
        "cus_add1": cus_add1,
        "cus_city": "Dhaka",
        "cus_country": "Bangladesh",
        "shipping_method": "NO",
        "multi_card_name": "",
        "num_of_item": 1,
        "product_name": product_name,
        "product_category": "PrintOrder",
        "product_profile": "general",
    }

    try:
        sslcz = get_sslcommerz_client()
        init_resp = sslcz.createSession(post_body)
    except Exception as exc:
        payment.status = PaymentStatus.FAILED
        payment.init_response = {"error": str(exc)}
        payment.save(update_fields=["status", "init_response", "updated_at"])
        raise exc

    payment.init_response = init_resp
    payment.sessionkey = init_resp.get("sessionkey") or init_resp.get("Sessionkey") or init_resp.get("session_key")
    payment.gateway_page_url = init_resp.get("GatewayPageURL")
    payment.status = PaymentStatus.PENDING
    payment.save(update_fields=["init_response", "sessionkey", "gateway_page_url", "status", "updated_at"])

    return payment
