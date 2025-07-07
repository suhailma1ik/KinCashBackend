from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Loan, RepaymentSchedule, Payment, Transaction


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Admin configuration for the Loan model."""
    list_display = ('id', 'lender', 'borrower', 'principal_amount', 'status', 'created_at')
    list_filter = ('status', 'emi_cycle', 'is_deleted')
    search_fields = ('id', 'lender__email', 'borrower__email', 'lender__phone_number', 'borrower__phone_number')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'approved_at', 'closed_at', 'deleted_at')
    
    fieldsets = (
        (None, {'fields': ('lender', 'borrower', 'principal_amount', 'interest_rate_pct', 'term_months')}),
        (_('Status'), {'fields': ('status', 'emi_cycle', 'late_fee_pct')}),
        (_('Dates'), {'fields': ('created_at', 'approved_at', 'closed_at')}),
        (_('Deletion'), {'fields': ('is_deleted', 'deleted_at')}),
    )


@admin.register(RepaymentSchedule)
class RepaymentScheduleAdmin(admin.ModelAdmin):
    """Admin configuration for the RepaymentSchedule model."""
    list_display = ('id', 'loan', 'due_date', 'amount_due', 'amount_paid', 'status')
    list_filter = ('status',)
    search_fields = ('loan__id', 'loan__borrower__email', 'loan__lender__email')
    date_hierarchy = 'due_date'
    
    fieldsets = (
        (None, {'fields': ('loan', 'due_date', 'amount_due')}),
        (_('Payment'), {'fields': ('amount_paid', 'status', 'paid_at')}),
        (_('Late Fee'), {'fields': ('late_fee_accrued',)}),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for the Payment model."""
    list_display = ('id', 'loan', 'payer', 'amount', 'paid_at')
    search_fields = ('loan__id', 'payer__email', 'payer__phone_number')
    date_hierarchy = 'paid_at'
    
    fieldsets = (
        (None, {'fields': ('loan', 'payer', 'amount')}),
        (_('Details'), {'fields': ('remarks', 'paid_at')}),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for the Transaction model."""
    list_display = ('id', 'from_user', 'to_user', 'amount', 'type', 'created_at')
    list_filter = ('type',)
    search_fields = ('from_user__email', 'to_user__email', 'related_id')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {'fields': ('from_user', 'to_user', 'amount')}),
        (_('Details'), {'fields': ('type', 'related_id', 'created_at')}),
    )
