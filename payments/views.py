import uuid

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from prints.models import PrintOrder
from payments.models import PaymentKind, PaymentStatus, PaymentTransaction
from payments.serializers import CheckoutSerializer, PaymentTransactionSerializer
from payments.sslcommerz import get_sslcommerz_client

FRONTEND_URL = getattr(settings, "FRONTEND_URL", "http://localhost:3000")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _flatten_payload(request_data) -> dict:
    """
    DRF QueryDict wraps each value in a list.
    SSLCommerz always sends single-value POST fields — flatten safely.
    """
    return {
        k: v[0] if isinstance(v, list) and len(v) == 1 else v
        for k, v in request_data.items()
    }


def _update_from_payload(payment: PaymentTransaction, payload: dict):
    """Persist raw SSLCommerz callback fields onto the payment record."""
    payment.callback_payload    = payload
    payment.val_id              = payload.get("val_id")          or payment.val_id
    payment.bank_tran_id        = payload.get("bank_tran_id")    or payment.bank_tran_id
    payment.card_type           = payload.get("card_type")       or payment.card_type
    payment.store_amount        = payload.get("store_amount")    or payment.store_amount
    payment.verify_sign         = payload.get("verify_sign")     or payment.verify_sign
    payment.verify_sign_sha2    = payload.get("verify_sign_sha2") or payment.verify_sign_sha2
    payment.risk_level          = payload.get("risk_level")      or payment.risk_level
    payment.risk_title          = payload.get("risk_title")      or payment.risk_title


def _validate_and_finalize(payment: PaymentTransaction, payload: dict):
    """
    Full validation pipeline per SSLCommerz docs:
      1. Hash / IPN signature check
      2. Call Order Validation API with val_id
      3. Cross-check amount against DB (tamper prevention)
      4. Cross-check tran_id (tamper prevention)
      5. Idempotency guard — skip if already SUCCESS
      6. Persist status atomically
    Returns (success: bool, message: str)
    """
    sslcz = get_sslcommerz_client()

    # ── 1. Hash validation ────────────────────────────────────────────────────
    if not sslcz.hash_validate_ipn(payload):
        payment.status = PaymentStatus.INVALID
        _update_from_payload(payment, payload)
        payment.save(update_fields=["status", "callback_payload", "updated_at"])
        return False, "Hash validation failed."

    _update_from_payload(payment, payload)

    # ── 2. Extract val_id ─────────────────────────────────────────────────────
    val_id = (
        payload.get("val_id")
        or payload.get("valId")
        or payload.get("valID")
        or payment.val_id
    )
    if not val_id:
        payment.status = PaymentStatus.INVALID
        payment.save(update_fields=["status", "callback_payload", "updated_at"])
        return False, "Missing val_id."

    # ── 3. Call Order Validation API ──────────────────────────────────────────
    validation_resp = sslcz.validationTransactionOrder(val_id)
    payment.validation_response = validation_resp
    ssl_status = str(
        (validation_resp or {}).get("status")
        or payload.get("status")
        or ""
    ).upper()

    # ── 4. Amount cross-check (required by SSLCommerz security docs) ──────────
    try:
        validated_amount = float(
            (validation_resp or {}).get("amount")
            or payload.get("amount")
            or 0
        )
        expected_amount = float(payment.amount)
        # Allow ±1 BDT tolerance for currency-conversion rounding
        if abs(validated_amount - expected_amount) > 1.0:
            payment.status = PaymentStatus.INVALID
            payment.save(update_fields=[
                "status", "validation_response", "callback_payload", "updated_at"
            ])
            return False, f"Amount mismatch: expected {expected_amount}, got {validated_amount}."
    except (TypeError, ValueError):
        pass  # unparseable amount — let status drive the outcome

    # ── 5. tran_id cross-check ────────────────────────────────────────────────
    returned_tran_id = (
        (validation_resp or {}).get("tran_id")
        or payload.get("tran_id")
    )
    if returned_tran_id and returned_tran_id != payment.tran_id:
        payment.status = PaymentStatus.INVALID
        payment.save(update_fields=[
            "status", "validation_response", "updated_at"
        ])
        return False, "Transaction ID mismatch."

    # ── 6. Persist outcome atomically ─────────────────────────────────────────
    with transaction.atomic():
        # Idempotency: IPN + success callback can both arrive; process only once
        if payment.status == PaymentStatus.SUCCESS:
            return True, "Already processed."

        if ssl_status in {"VALID", "VALIDATED"}:
            payment.status = PaymentStatus.SUCCESS
            payment.paid_at = timezone.now()

            # ── Fulfillment hooks (uncomment as needed) ──────────────────────
            # if payment.print_order:
            #     payment.print_order.status = "PAID"
            #     payment.print_order.save(update_fields=["status"])
            #
            # Enrollment example:
            # Enrollment.objects.get_or_create(
            #     user=payment.user,
            #     course=payment.course,
            #     defaults={"status": EnrollmentStatus.ACTIVE},
            # )

        elif ssl_status == "FAILED":
            payment.status = PaymentStatus.FAILED
        elif ssl_status == "CANCELLED":
            payment.status = PaymentStatus.CANCELLED
        else:
            payment.status = PaymentStatus.FAILED

        payment.save(update_fields=[
            "status", "paid_at",
            "val_id", "bank_tran_id", "card_type", "store_amount",
            "verify_sign", "verify_sign_sha2", "risk_level", "risk_title",
            "callback_payload", "validation_response", "updated_at",
        ])

    return payment.status == PaymentStatus.SUCCESS, payment.status


# ──────────────────────────────────────────────────────────────────────────────
# Checkout
# ──────────────────────────────────────────────────────────────────────────────

class CheckoutView(APIView):
    """
    Authenticated endpoint — frontend calls this to start a payment session.
    Returns GatewayPageURL; frontend redirects the user there.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        print_order = None
        if "print_order_id" in data:
            print_order = get_object_or_404(
                PrintOrder, id=data["print_order_id"]
            )

        if print_order is None:
            return Response(
                {"detail": "print_order_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .utils import create_payment_session
        try:
            payment = create_payment_session(
                request=request,
                print_order=print_order,
                amount=data["amount"],
                kind=data["kind"],
                currency=data.get("currency", "BDT"),
                meta={
                    "subscription_plan":   data.get("subscription_plan", ""),
                    "subscription_months": data.get("subscription_months"),
                },
            )
        except Exception as exc:
            return Response(
                {"detail": "Failed to create SSLCOMMERZ session.", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not payment.gateway_page_url:
            return Response(
                {
                    "detail": "SSLCOMMERZ did not return GatewayPageURL.",
                    "response": payment.init_response,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "payment_id":       payment.id,
            "tran_id":          payment.tran_id,
            "gateway_page_url": payment.gateway_page_url,
            "sessionkey":       payment.sessionkey,
        })


# ──────────────────────────────────────────────────────────────────────────────
# SSLCommerz browser callbacks — validate then redirect browser to frontend
# ──────────────────────────────────────────────────────────────────────────────

class SSLCommerzSuccessView(APIView):
    """SSLCommerz POSTs here after successful payment. Validate then redirect."""
    permission_classes  = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload  = _flatten_payload(request.data)
        tran_id  = payload.get("tran_id")

        if not tran_id:
            return redirect(f"{FRONTEND_URL}/your-prints?status=failed&reason=missing_tran_id")

        payment  = get_object_or_404(PaymentTransaction, tran_id=tran_id)
        ok, msg  = _validate_and_finalize(payment, payload)

        if ok:
            return redirect(f"{FRONTEND_URL}/your-prints?status=success&tran_id={tran_id}")
        return redirect(f"{FRONTEND_URL}/your-prints?status=failed&tran_id={tran_id}&reason={msg}")


class SSLCommerzFailView(APIView):
    """SSLCommerz POSTs here when payment fails at the bank."""
    permission_classes  = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = _flatten_payload(request.data)
        tran_id = payload.get("tran_id", "")

        payment = get_object_or_404(PaymentTransaction, tran_id=tran_id)
        _update_from_payload(payment, payload)
        payment.status = PaymentStatus.FAILED
        payment.save(update_fields=["status", "callback_payload", "updated_at"])

        return redirect(f"{FRONTEND_URL}/your-prints?status=failed&tran_id={tran_id}")


class SSLCommerzCancelView(APIView):
    """SSLCommerz POSTs here when the user cancels."""
    permission_classes  = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = _flatten_payload(request.data)
        tran_id = payload.get("tran_id", "")

        payment = get_object_or_404(PaymentTransaction, tran_id=tran_id)
        _update_from_payload(payment, payload)
        payment.status = PaymentStatus.CANCELLED
        payment.save(update_fields=["status", "callback_payload", "updated_at"])

        return redirect(f"{FRONTEND_URL}/your-prints?status=cancelled&tran_id={tran_id}")


# ──────────────────────────────────────────────────────────────────────────────
# IPN — server-to-server, no browser involved, returns JSON
# ──────────────────────────────────────────────────────────────────────────────

class SSLCommerzIPNView(APIView):
    """
    Instant Payment Notification from SSLCommerz server.
    This fires even if the user loses connection before the success redirect.
    Always returns JSON (no redirect) — SSLCommerz doesn't read the response body.
    """
    permission_classes  = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = _flatten_payload(request.data)
        tran_id = payload.get("tran_id")

        if not tran_id:
            return Response(
                {"detail": "Missing tran_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment    = get_object_or_404(PaymentTransaction, tran_id=tran_id)
        ok, msg    = _validate_and_finalize(payment, payload)

        return Response(
            {"detail": msg},
            status=status.HTTP_200_OK if ok else status.HTTP_400_BAD_REQUEST,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Frontend polling — called by frontend after redirect to verify real DB status
# ──────────────────────────────────────────────────────────────────────────────

class PaymentStatusView(APIView):
    """
    Frontend calls this after landing on /your-prints?status=success or /your-prints?status=failed
    to get the authoritative payment status from the DB.
    Never trust URL params alone.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, tran_id):
        payment = get_object_or_404(
            PaymentTransaction,
            tran_id=tran_id,
            user=request.user,   # users can only query their own
        )
        return Response({
            "tran_id":        payment.tran_id,
            "status":         payment.status,
            "amount":         payment.amount,
            "currency":       payment.currency,
            "paid_at":        payment.paid_at,
            "print_order_id": payment.print_order_id,
            "risk_level":     payment.risk_level,
            "risk_title":     payment.risk_title,
            "card_type":      payment.card_type,
        })


# ──────────────────────────────────────────────────────────────────────────────
# List / detail (read-only)
# ──────────────────────────────────────────────────────────────────────────────

class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field       = "tran_id"

    def get_queryset(self):
        return PaymentTransaction.objects.filter(
            user=self.request.user
        ).order_by("-created_at")