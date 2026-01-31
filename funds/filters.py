"""
Filters for fund management API.
"""
import django_filters
from funds.models import FundAccount, Transaction, TransactionStatus, TransactionType, TransactionCategory


class FundAccountFilter(django_filters.FilterSet):
    """Filter for fund accounts"""
    name = django_filters.CharFilter(lookup_expr='icontains')
    code = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    
    class Meta:
        model = FundAccount
        fields = ['name', 'code', 'is_active']


class TransactionFilter(django_filters.FilterSet):
    """Filter for transactions"""
    account = django_filters.ModelChoiceFilter(queryset=FundAccount.objects.all())
    transaction_type = django_filters.ChoiceFilter(choices=TransactionType.choices)
    category = django_filters.ChoiceFilter(choices=TransactionCategory.choices)
    status = django_filters.ChoiceFilter(choices=TransactionStatus.choices)
    
    # Date range filters
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    # Amount range filters
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    
    # Created by filter
    created_by = django_filters.NumberFilter(field_name='created_by__id')
    
    class Meta:
        model = Transaction
        fields = [
            'account',
            'transaction_type',
            'category',
            'status',
            'created_after',
            'created_before',
            'amount_min',
            'amount_max',
            'created_by',
        ]

