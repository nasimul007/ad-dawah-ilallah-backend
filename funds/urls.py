"""
URL configuration for funds app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from funds.views import FundAccountViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'accounts', FundAccountViewSet, basename='fundaccount')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]

