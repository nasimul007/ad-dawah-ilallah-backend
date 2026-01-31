import uuid

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course
from enrollments.models import Enrollment, EnrollmentKind, EnrollmentStatus
from payments.models import PaymentKind, PaymentStatus, PaymentTransaction
from payments.serializers import CheckoutSerializer, PaymentTransactionSerializer
from payments.sslcommerz import get_sslcommerz_client


def _new_tran_id() -> str:
    # SSLCOMMERZ accepts a string tran_id; keep it short & unique.
    return uuid.uuid4().hex.upper()


class CheckoutView(APIView):
    """
    Start an SSLCOMMERZ checkout session for a course purchase or subscription.
    Returns the GatewayPageURL to redirect the user.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        course = None
        if "course_id" in data:
            course = get_object_or_404(Course, id=data["course_id"])
        if course is None:
            return Response(
                {"detail": "course_id is required to create an enrollment after payment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tran_id = _new_tran_id()

        payment = PaymentTransaction.objects.create(
            user=request.user,
            course=course,
            kind=PaymentKind.ONE_TIME if data["kind"] == "ONE_TIME" else PaymentKind.SUBSCRIPTION,
            amount=data["amount"],
            currency=data.get("currency", "BDT"),
            tran_id=tran_id,
            status=PaymentStatus.INITIATED,
            meta={
                "subscription_plan": data.get("subscription_plan", ""),
                "subscription_months": data.get("subscription_months"),
            },
        )

        # Build callback URLs that SSLCOMMERZ will call
        success_url = request.build_absolute_uri(reverse("payments:ssl-success"))
        fail_url = request.build_absolute_uri(reverse("payments:ssl-fail"))
        cancel_url = request.build_absolute_uri(reverse("payments:ssl-cancel"))

        # Customer details (SSLCOMMERZ requires these fields)
        cus_name = getattr(request.user, "full_name", "") or getattr(request.user, "username", "customer")
        cus_email = getattr(request.user, "email", "") or "no-reply@example.com"
        cus_phone = getattr(request.user, "phone", "") or "01700000000"
        cus_add1 = getattr(request.user, "address", "") or "N/A"

        product_name = course.title if course else "Subscription"

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
            "product_category": "Course",
            "product_profile": "general",
        }

        try:
            sslcz = get_sslcommerz_client()
            init_resp = sslcz.createSession(post_body)
        except Exception as exc:
            payment.status = PaymentStatus.FAILED
            payment.init_response = {"error": str(exc)}
            payment.save(update_fields=["status", "init_response", "updated_at"])
            return Response(
                {"detail": "Failed to create SSLCOMMERZ session.", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        payment.init_response = init_resp
        payment.sessionkey = init_resp.get("sessionkey") or init_resp.get("Sessionkey") or init_resp.get("session_key")
        payment.gateway_page_url = init_resp.get("GatewayPageURL")
        payment.status = PaymentStatus.PENDING
        payment.save(
            update_fields=["init_response", "sessionkey", "gateway_page_url", "status", "updated_at"]
        )

        if not payment.gateway_page_url:
            payment.status = PaymentStatus.FAILED
            payment.save(update_fields=["status", "updated_at"])
            return Response(
                {"detail": "SSLCOMMERZ did not return GatewayPageURL.", "response": init_resp},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "payment_id": payment.id,
                "tran_id": payment.tran_id,
                "gateway_page_url": payment.gateway_page_url,
                "sessionkey": payment.sessionkey,
            },
            status=status.HTTP_200_OK,
        )


class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "tran_id"

    def get_queryset(self):
        return PaymentTransaction.objects.filter(user=self.request.user).order_by("-created_at")


def _update_from_payload(payment: PaymentTransaction, payload: dict):
    payment.callback_payload = payload
    payment.val_id = payload.get("val_id") or payment.val_id
    payment.bank_tran_id = payload.get("bank_tran_id") or payment.bank_tran_id
    payment.card_type = payload.get("card_type") or payment.card_type
    payment.store_amount = payload.get("store_amount") or payment.store_amount
    payment.verify_sign = payload.get("verify_sign") or payment.verify_sign
    payment.verify_sign_sha2 = payload.get("verify_sign_sha2") or payment.verify_sign_sha2
    payment.risk_level = payload.get("risk_level") or payment.risk_level
    payment.risk_title = payload.get("risk_title") or payment.risk_title


def _validate_and_finalize(payment: PaymentTransaction, payload: dict):
    """
    Validate the IPN/callback payload hash and then validate the transaction using val_id.
    """
    sslcz = get_sslcommerz_client()

    if not sslcz.hash_validate_ipn(payload):
        payment.status = PaymentStatus.INVALID
        _update_from_payload(payment, payload)
        payment.save(update_fields=["status", "callback_payload", "updated_at"])
        return False, {"detail": "Hash validation failed."}

    _update_from_payload(payment, payload)

    val_id = payload.get("val_id") or payload.get("valId") or payload.get("valID") or payment.val_id
    if not val_id:
        payment.status = PaymentStatus.INVALID
        payment.save(update_fields=["status", "callback_payload", "updated_at"])
        return False, {"detail": "Missing val_id."}

    validation_resp = sslcz.validationTransactionOrder(val_id)
    payment.validation_response = validation_resp

    ssl_status = (validation_resp or {}).get("status") or payload.get("status")

    with transaction.atomic():
        if str(ssl_status).upper() in {"VALID", "VALIDATED"}:
            payment.status = PaymentStatus.SUCCESS
            payment.paid_at = timezone.now()

            # Create enrollment once (idempotent)
            if payment.course_id and payment.enrollment_id is None:
                enrollment_kind = (
                    EnrollmentKind.SUBSCRIPTION
                    if payment.kind == PaymentKind.SUBSCRIPTION
                    else EnrollmentKind.ONE_TIME
                )

                enrollment, _created = Enrollment.objects.get_or_create(
                    user=payment.user,
                    course=payment.course,
                    defaults={
                        "kind": enrollment_kind,
                        "status": EnrollmentStatus.ACTIVE,
                    },
                )
                # If previously existed (maybe from earlier payment), ensure it is active and kind updated.
                if enrollment.status != EnrollmentStatus.ACTIVE:
                    enrollment.status = EnrollmentStatus.ACTIVE
                    enrollment.save(update_fields=["status", "updated_at"])

                payment.enrollment = enrollment
        else:
            payment.status = PaymentStatus.FAILED

        payment.save(
            update_fields=[
                "status",
                "paid_at",
                "enrollment",
                "val_id",
                "bank_tran_id",
                "card_type",
                "store_amount",
                "verify_sign",
                "verify_sign_sha2",
                "risk_level",
                "risk_title",
                "callback_payload",
                "validation_response",
                "updated_at",
            ]
        )

    return True, {"detail": "Payment validated.", "status": payment.status, "enrollment_id": payment.enrollment_id}


class SSLCommerzSuccessView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = dict(request.data)
        tran_id = payload.get("tran_id")
        payment = get_object_or_404(PaymentTransaction, tran_id=tran_id)
        ok, resp = _validate_and_finalize(payment, payload)
        return Response(resp, status=status.HTTP_200_OK if ok else status.HTTP_400_BAD_REQUEST)


class SSLCommerzFailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = dict(request.data)
        tran_id = payload.get("tran_id")
        payment = get_object_or_404(PaymentTransaction, tran_id=tran_id)
        _update_from_payload(payment, payload)
        payment.status = PaymentStatus.FAILED
        payment.save(update_fields=["status", "callback_payload", "updated_at"])
        return Response({"detail": "Payment failed."}, status=status.HTTP_200_OK)


class SSLCommerzCancelView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = dict(request.data)
        tran_id = payload.get("tran_id")
        payment = get_object_or_404(PaymentTransaction, tran_id=tran_id)
        _update_from_payload(payment, payload)
        payment.status = PaymentStatus.CANCELLED
        payment.save(update_fields=["status", "callback_payload", "updated_at"])
        return Response({"detail": "Payment cancelled."}, status=status.HTTP_200_OK)


class SSLCommerzIPNView(APIView):
    """
    IPN endpoint (server-to-server) from SSLCOMMERZ.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = dict(request.data)
        tran_id = payload.get("tran_id")
        payment = get_object_or_404(PaymentTransaction, tran_id=tran_id)
        ok, resp = _validate_and_finalize(payment, payload)
        return Response(resp, status=status.HTTP_200_OK if ok else status.HTTP_400_BAD_REQUEST)


