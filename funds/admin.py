"""
Admin configuration for funds app.
"""
from django.contrib import admin
from funds.models import FundAccount, Transaction


@admin.register(FundAccount)
class FundAccountAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'code',
        'is_active',
        'current_balance',
        'created_by',
        'created_at',
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['current_balance', 'pending_balance_change', 'created_at', 'updated_at']
    raw_id_fields = ['created_by']
    ordering = ['name']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'account',
        'transaction_type',
        'category',
        'amount',
        'status',
        'created_by',
        'approved_by',
        'created_at',
    ]
    list_filter = [
        'status',
        'transaction_type',
        'category',
        'created_at',
    ]
    search_fields = [
        'description',
        'account__name',
        'account__code',
        'created_by__full_name',
    ]
    readonly_fields = [
        'approved_by',
        'approved_at',
        'created_at',
        'updated_at',
    ]
    raw_id_fields = ['account', 'created_by', 'approved_by']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('account', 'transaction_type', 'category', 'amount', 'description')
        }),
        ('Status', {
            'fields': ('status', 'rejection_reason')
        }),
        ('Users', {
            'fields': ('created_by', 'approved_by', 'approved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_selected', 'reject_selected']
    
    def approve_selected(self, request, queryset):
        """Admin action to approve selected transactions"""
        if not request.user.is_super_admin:
            self.message_user(request, "Only super admins can approve transactions", level='error')
            return
        
        count = 0
        for transaction in queryset.filter(status=TransactionStatus.PENDING):
            try:
                transaction.approve(request.user)
                count += 1
            except ValueError as e:
                self.message_user(request, f"Error approving {transaction.id}: {e}", level='error')
        
        self.message_user(request, f"Approved {count} transaction(s)")
    approve_selected.short_description = "Approve selected transactions"
    
    def reject_selected(self, request, queryset):
        """Admin action to reject selected transactions"""
        if not request.user.is_super_admin:
            self.message_user(request, "Only super admins can reject transactions", level='error')
            return
        
        count = 0
        for transaction in queryset.filter(status=TransactionStatus.PENDING):
            try:
                transaction.reject(request.user, "Bulk rejection from admin")
                count += 1
            except ValueError as e:
                self.message_user(request, f"Error rejecting {transaction.id}: {e}", level='error')
        
        self.message_user(request, f"Rejected {count} transaction(s)")
    reject_selected.short_description = "Reject selected transactions"
