"""
Views for fund management API.

Features:
- Create and manage fund accounts
- Create transactions (deposit/credit)
- Super admin approval workflow
- Transaction filtering and reporting
"""
from decimal import Decimal
from django.db.models import Sum, Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from accounts.permissions import HasPermissionCode
from funds.models import FundAccount, Transaction, TransactionStatus
from funds.filters import FundAccountFilter, TransactionFilter
from funds.serializers import (
    FundAccountSerializer,
    FundAccountListSerializer,
    TransactionSerializer,
    TransactionCreateSerializer,
    TransactionListSerializer,
    TransactionApprovalSerializer,
    TransactionSummarySerializer,
)


class FundAccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing fund accounts.
    
    Permissions:
    - List/View: FUND_ACCOUNT_VIEW
    - Create/Update/Delete: FUND_ACCOUNT_MANAGE
    """
    queryset = FundAccount.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = FundAccountFilter
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    permission_classes = [IsAuthenticated, HasPermissionCode]
    
    # Set permissions per method
    required_permissions = {
        'GET': 'FUND_ACCOUNT_VIEW',
        'POST': 'FUND_ACCOUNT_MANAGE',
        'PUT': 'FUND_ACCOUNT_MANAGE',
        'PATCH': 'FUND_ACCOUNT_MANAGE',
        'DELETE': 'FUND_ACCOUNT_MANAGE',
    }
    
    def get_serializer_class(self):
        if self.action == 'list':
            return FundAccountListSerializer
        return FundAccountSerializer
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    @extend_schema(
        responses={200: TransactionSummarySerializer},
        summary="Get account summary",
        description="Get detailed summary including balances and transaction counts"
    )
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get detailed account summary"""
        account = self.get_object()
        
        # Calculate statistics
        all_transactions = account.transactions.filter(
            status=TransactionStatus.APPROVED
        )
        
        deposits = all_transactions.filter(
            transaction_type='deposit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        credits = all_transactions.filter(
            transaction_type='credit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        pending_transactions = account.transactions.filter(
            status=TransactionStatus.PENDING
        )
        
        pending_deposits = pending_transactions.filter(
            transaction_type='deposit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        pending_credits = pending_transactions.filter(
            transaction_type='credit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        summary = {
            'account_id': account.id,
            'account_name': account.name,
            'account_code': account.code,
            'current_balance': account.current_balance,
            'total_deposits': deposits,
            'total_credits': credits,
            'pending_deposits': pending_deposits,
            'pending_credits': pending_credits,
            'total_transactions': account.transactions.filter(
                status=TransactionStatus.APPROVED
            ).count(),
            'pending_transactions': pending_transactions.count(),
        }
        
        return Response(TransactionSummarySerializer(summary).data)
    
    @extend_schema(
        responses={200: TransactionListSerializer(many=True)},
        summary="Get account transactions",
        description="Get all transactions for this account"
    )
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get all transactions for this account"""
        account = self.get_object()
        transactions = account.transactions.all().order_by('-created_at')
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            transactions = transactions.filter(status=status_filter)
        
        serializer = TransactionListSerializer(transactions, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing transactions.
    
    Permissions:
    - List/View: TRANSACTION_VIEW
    - Create: TRANSACTION_CREATE
    - Approve/Reject: TRANSACTION_APPROVE (super admin only)
    """
    queryset = Transaction.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = TransactionFilter
    search_fields = ['description', 'account__name', 'account__code']
    ordering_fields = ['created_at', 'amount', 'status']
    permission_classes = [IsAuthenticated, HasPermissionCode]
    
    # Set permissions per method
    required_permissions = {
        'GET': 'TRANSACTION_VIEW',
        'POST': 'TRANSACTION_CREATE',
        'PUT': 'TRANSACTION_CREATE',
        'PATCH': 'TRANSACTION_CREATE',
        'DELETE': 'TRANSACTION_CREATE',
    }
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TransactionCreateSerializer
        if self.action == 'list':
            return TransactionListSerializer
        return TransactionSerializer
    
    def perform_create(self, serializer):
        """Set created_by and ensure status is PENDING"""
        serializer.save(
            created_by=self.request.user,
            status=TransactionStatus.PENDING
        )
    
    @extend_schema(
        request=TransactionApprovalSerializer,
        responses={
            200: TransactionSerializer,
            400: OpenApiResponse(description="Invalid action or transaction state"),
            403: OpenApiResponse(description="Only super admins can approve/reject"),
        },
        summary="Approve or reject transaction",
        description="Super admin action to approve or reject a pending transaction"
    )
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve or reject a transaction.
        Only super admins can perform this action.
        """
        transaction = self.get_object()
        
        # Check permission - super admin or TRANSACTION_APPROVE permission
        if not (request.user.is_super_admin or request.user.has_permission_code('TRANSACTION_APPROVE')):
            return Response(
                {'error': 'Only super admins or users with TRANSACTION_APPROVE permission can approve/reject transactions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate transaction state
        if transaction.status != TransactionStatus.PENDING:
            return Response(
                {'error': f'Cannot modify transaction with status: {transaction.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TransactionApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        rejection_reason = serializer.validated_data.get('rejection_reason', '')
        
        try:
            if action_type == 'approve':
                transaction.approve(request.user)
            elif action_type == 'reject':
                transaction.reject(request.user, rejection_reason)
            
            return Response(
                TransactionSerializer(transaction).data,
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        responses={200: TransactionSerializer},
        summary="Cancel transaction",
        description="Cancel a pending transaction (creator or super admin)"
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending transaction"""
        transaction = self.get_object()
        
        if transaction.status != TransactionStatus.PENDING:
            return Response(
                {'error': f'Cannot cancel transaction with status: {transaction.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check permissions
        if not (request.user.is_super_admin or request.user == transaction.created_by):
            return Response(
                {'error': 'Only creator or super admin can cancel transactions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            transaction.cancel(request.user)
            return Response(
                TransactionSerializer(transaction).data,
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        responses={200: TransactionListSerializer(many=True)},
        summary="Get pending transactions",
        description="Get all transactions pending approval"
    )
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending transactions (for super admin approval queue)"""
        if not request.user.is_super_admin:
            return Response(
                {'error': 'Only super admins can view pending transactions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pending_transactions = Transaction.objects.filter(
            status=TransactionStatus.PENDING
        ).order_by('-created_at')
        
        serializer = TransactionListSerializer(pending_transactions, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        responses={200: TransactionListSerializer(many=True)},
        summary="Get my transactions",
        description="Get all transactions created by current user"
    )
    @action(detail=False, methods=['get'])
    def my_transactions(self, request):
        """Get all transactions created by current user"""
        my_transactions = Transaction.objects.filter(
            created_by=request.user
        ).order_by('-created_at')
        
        serializer = TransactionListSerializer(my_transactions, many=True)
        return Response(serializer.data)
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        user = self.request.user
        
        # Super admins see all
        if user.is_super_admin:
            return Transaction.objects.all()
        
        # Others see only their own transactions
        # (unless they have TRANSACTION_VIEW_ALL permission)
        if user.has_permission_code('TRANSACTION_VIEW_ALL'):
            return Transaction.objects.all()
        
        return Transaction.objects.filter(created_by=user)
