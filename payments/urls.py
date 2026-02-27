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
    # Checkout initiation
    path("checkout/",           CheckoutView.as_view(),         name="checkout"),

    # SSLCommerz browser callbacks
    path("ssl/success/",        SSLCommerzSuccessView.as_view(), name="ssl-success"),
    path("ssl/fail/",           SSLCommerzFailView.as_view(),    name="ssl-fail"),
    path("ssl/cancel/",         SSLCommerzCancelView.as_view(),  name="ssl-cancel"),

    # SSLCommerz server-to-server IPN
    path("ssl/ipn/",            SSLCommerzIPNView.as_view(),     name="ssl-ipn"),

    # Frontend polls this after redirect
    # path("<str:tran_id>/status/", PaymentStatusView.as_view(),  name="payment-status"),

    *router.urls,
]








