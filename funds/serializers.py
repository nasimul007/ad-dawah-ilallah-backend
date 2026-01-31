"""
Serializers for fund management API.
"""
from rest_framework import serializers
from funds.models import (
    FundAccount,
    Transaction,
    TransactionType,
    TransactionCategory,
    TransactionStatus,
)


class FundAccountSerializer(serializers.ModelSerializer):
    """Serializer for fund accounts"""
    current_balance = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True,
        help_text="Current balance from approved transactions"
    )
    pending_balance_change = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True,
        help_text="Pending balance change from pending transactions"
    )
    created_by_name = serializers.CharField(
        source='created_by.full_name',
        read_only=True
    )
    
    class Meta:
        model = FundAccount
        fields = [
            'id',
            'name',
            'code',
            'description',
            'is_active',
            'current_balance',
            'pending_balance_change',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FundAccountListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for account list"""
    current_balance = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = FundAccount
        fields = [
            'id',
            'name',
            'code',
            'is_active',
            'current_balance',
            'created_at',
        ]


class TransactionSerializer(serializers.ModelSerializer):
    """Full transaction serializer"""
    account_name = serializers.CharField(
        source='account.name',
        read_only=True
    )
    account_code = serializers.CharField(
        source='account.code',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.full_name',
        read_only=True
    )
    approved_by_name = serializers.CharField(
        source='approved_by.full_name',
        read_only=True
    )
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'account',
            'account_name',
            'account_code',
            'transaction_type',
            'transaction_type_display',
            'category',
            'category_display',
            'amount',
            'description',
            'status',
            'status_display',
            'created_by',
            'created_by_name',
            'approved_by',
            'approved_by_name',
            'rejection_reason',
            'created_at',
            'updated_at',
            'approved_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'approved_by',
            'approved_at',
            'rejection_reason',
            'created_at',
            'updated_at',
        ]


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transactions"""
    
    class Meta:
        model = Transaction
        fields = [
            'account',
            'transaction_type',
            'category',
            'amount',
            'description',
        ]
    
    def validate(self, attrs):
        """Validate transaction data"""
        account = attrs.get('account')
        
        # Check if account is active
        if account and not account.is_active:
            raise serializers.ValidationError({
                'account': 'Cannot create transaction for inactive account'
            })
        
        # For credits, check if account has sufficient balance (optional check)
        # You might want to allow negative balances, so this is commented out
        # if attrs.get('transaction_type') == TransactionType.CREDIT:
        #     if account.current_balance < attrs.get('amount'):
        #         raise serializers.ValidationError({
        #             'amount': 'Insufficient balance'
        #         })
        
        return attrs


class TransactionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for transaction list"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_code = serializers.CharField(source='account.code', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'account',
            'account_name',
            'account_code',
            'transaction_type',
            'category',
            'amount',
            'status',
            'created_by_name',
            'created_at',
        ]


class TransactionApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting transactions"""
    action = serializers.ChoiceField(
        choices=['approve', 'reject'],
        help_text="Action to take: 'approve' or 'reject'"
    )
    rejection_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Required if action is 'reject'"
    )
    
    def validate(self, attrs):
        action = attrs.get('action')
        rejection_reason = attrs.get('rejection_reason', '')
        
        if action == 'reject' and not rejection_reason:
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting a transaction'
            })
        
        return attrs


class TransactionSummarySerializer(serializers.Serializer):
    """Serializer for transaction summary statistics"""
    account_id = serializers.IntegerField()
    account_name = serializers.CharField()
    account_code = serializers.CharField()
    current_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_deposits = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_credits = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_deposits = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_credits = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_transactions = serializers.IntegerField()
    pending_transactions = serializers.IntegerField()

