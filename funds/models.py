"""
Fund Management Models

Handles fund accounts (branches) and transactions with approval workflow.
"""
from decimal import Decimal
from django.db import models
from django.db.models import Sum, Q
from django.core.validators import MinValueValidator
from accounts.models import User


class FundAccount(models.Model):
    """
    Fund account representing a branch or department.
    Example: "Dhaka Branch", "Chittagong Branch", "Main Office"
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Account name (e.g., 'Dhaka Branch')"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Short code for the account (e.g., 'DHAKA-001')"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Account description"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this account is active"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_fund_accounts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Fund Account"
        verbose_name_plural = "Fund Accounts"
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def current_balance(self) -> Decimal:
        """
        Calculate current balance from all approved transactions.
        Deposits increase balance, credits decrease balance.
        """
        approved_transactions = self.transactions.filter(
            status=TransactionStatus.APPROVED
        )
        
        deposits = approved_transactions.filter(
            transaction_type=TransactionType.DEPOSIT
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        credits = approved_transactions.filter(
            transaction_type=TransactionType.CREDIT
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return deposits - credits
    
    @property
    def pending_balance_change(self) -> Decimal:
        """
        Calculate pending balance change from pending transactions.
        """
        pending_transactions = self.transactions.filter(
            status=TransactionStatus.PENDING
        )
        
        pending_deposits = pending_transactions.filter(
            transaction_type=TransactionType.DEPOSIT
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        pending_credits = pending_transactions.filter(
            transaction_type=TransactionType.CREDIT
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return pending_deposits - pending_credits


class TransactionType(models.TextChoices):
    """Transaction type choices"""
    DEPOSIT = 'deposit', 'Deposit'
    CREDIT = 'credit', 'Credit'


class TransactionCategory(models.TextChoices):
    """Transaction category choices"""
    DONATION = 'donation', 'Donation'
    CHARITY = 'charity', 'Charity'
    SALARY = 'salary', 'Salary'
    EXPENSE = 'expense', 'Expense'
    INCOME = 'income', 'Income'
    OTHER = 'other', 'Other'


class TransactionStatus(models.TextChoices):
    """Transaction approval status"""
    PENDING = 'pending', 'Pending Approval'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    CANCELLED = 'cancelled', 'Cancelled'


class Transaction(models.Model):
    """
    Financial transaction in a fund account.
    
    All transactions require super admin approval before being applied
    to the account balance.
    """
    account = models.ForeignKey(
        FundAccount,
        on_delete=models.PROTECT,
        related_name='transactions',
        help_text="Fund account this transaction belongs to"
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        help_text="Deposit (money in) or Credit (money out)"
    )
    
    category = models.CharField(
        max_length=20,
        choices=TransactionCategory.choices,
        default=TransactionCategory.OTHER,
        help_text="Transaction category"
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Transaction amount (must be positive)"
    )
    
    description = models.TextField(
        help_text="Description of the transaction"
    )
    
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        db_index=True,
        help_text="Approval status"
    )
    
    # User tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_transactions',
        help_text="User who created this transaction"
    )
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_transactions',
        help_text="Super admin who approved/rejected this transaction"
    )
    
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for rejection (if rejected)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        indexes = [
            models.Index(fields=['account', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['category', 'status']),
        ]
    
    def __str__(self):
        return f"{self.account.name} - {self.get_transaction_type_display()} {self.amount} ({self.status})"
    
    def approve(self, approved_by: User, rejection_reason: str = None):
        """
        Approve this transaction.
        Only super admins can approve.
        """
        if not approved_by.is_super_admin:
            raise ValueError("Only super admins can approve transactions")
        
        if self.status != TransactionStatus.PENDING:
            raise ValueError(f"Cannot approve transaction with status: {self.status}")
        
        from django.utils import timezone
        
        self.status = TransactionStatus.APPROVED
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.rejection_reason = None
        self.save(update_fields=['status', 'approved_by', 'approved_at', 'rejection_reason', 'updated_at'])
    
    def reject(self, rejected_by: User, reason: str):
        """
        Reject this transaction.
        Only super admins can reject.
        """
        if not rejected_by.is_super_admin:
            raise ValueError("Only super admins can reject transactions")
        
        if self.status != TransactionStatus.PENDING:
            raise ValueError(f"Cannot reject transaction with status: {self.status}")
        
        from django.utils import timezone
        
        self.status = TransactionStatus.REJECTED
        self.approved_by = rejected_by
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save(update_fields=['status', 'approved_by', 'approved_at', 'rejection_reason', 'updated_at'])
    
    def cancel(self, cancelled_by: User):
        """
        Cancel a pending transaction.
        Can be done by creator or super admin.
        """
        if self.status != TransactionStatus.PENDING:
            raise ValueError(f"Cannot cancel transaction with status: {self.status}")
        
        if not (cancelled_by.is_super_admin or cancelled_by == self.created_by):
            raise ValueError("Only creator or super admin can cancel transactions")
        
        self.status = TransactionStatus.CANCELLED
        self.save(update_fields=['status', 'updated_at'])
    
    @property
    def is_pending(self) -> bool:
        return self.status == TransactionStatus.PENDING
    
    @property
    def is_approved(self) -> bool:
        return self.status == TransactionStatus.APPROVED
