from django.urls import path, include
from rest_framework.routers import DefaultRouter

from payments.views import (
    CheckoutView,
    PaymentTransactionViewSet,
    SSLCommerzCancelView,
    SSLCommerzFailView,
    SSLCommerzIPNView,
    SSLCommerzSuccessView,
)

app_name = "payments"

router = DefaultRouter()
router.register("transactions", PaymentTransactionViewSet, basename="payment-transactions")

urlpatterns = [
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("ssl/success/", SSLCommerzSuccessView.as_view(), name="ssl-success"),
    path("ssl/fail/", SSLCommerzFailView.as_view(), name="ssl-fail"),
    path("ssl/cancel/", SSLCommerzCancelView.as_view(), name="ssl-cancel"),
    path("ssl/ipn/", SSLCommerzIPNView.as_view(), name="ssl-ipn"),
    path("", include(router.urls)),
]





