"""
Loan models for H.E.L.P Backend.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.users.models import User


class LoanStatus(models.TextChoices):
    """Loan status choices."""
    PENDING = 'PENDING', _('Pending Approval')
    ACTIVE = 'ACTIVE', _('Active')
    PAID = 'PAID', _('Paid')
    DEFAULTED = 'DEFAULTED', _('Defaulted')
    CANCELLED = 'CANCELLED', _('Cancelled')


class EMICycle(models.TextChoices):
    """EMI cycle choices."""
    WEEKLY = 'WEEKLY', _('Weekly')
    MONTHLY = 'MONTHLY', _('Monthly')


class Loan(models.Model):
    """
    Loan model representing a loan between a lender and a borrower.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    lender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='loans_as_lender',
        verbose_name=_('Lender')
    )
    borrower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='loans_as_borrower',
        verbose_name=_('Borrower')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='loans_created',
        verbose_name=_('Created by'),
        null=True,
        blank=True
    )
    principal_amount = models.DecimalField(
        _('Principal amount'),
        max_digits=14,
        decimal_places=2
    )
    interest_rate_pct = models.DecimalField(
        _('Interest rate (%)'),
        max_digits=5,
        decimal_places=2,
        help_text=_('Annualized interest rate')
    )
    term_months = models.PositiveIntegerField(
        _('Term (months)'),
        help_text=_('Total tenure in months')
    )
    emi_cycle = models.CharField(
        _('EMI cycle'),
        max_length=10,
        choices=EMICycle.choices,
        default=EMICycle.MONTHLY
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=LoanStatus.choices,
        default=LoanStatus.PENDING
    )
    late_fee_pct = models.DecimalField(
        _('Late fee (%)'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Percentage of overdue amount per period')
    )
    created_at = models.DateTimeField(_('Created at'), default=timezone.now)
    approved_at = models.DateTimeField(_('Approved at'), null=True, blank=True)
    closed_at = models.DateTimeField(_('Closed at'), null=True, blank=True)
    
    # Fields for soft deletion
    is_deleted = models.BooleanField(_('Deleted'), default=False)
    deleted_at = models.DateTimeField(_('Deleted at'), null=True, blank=True)
    
    class Meta:
        """Meta options for Loan model."""
        verbose_name = _('loan')
        verbose_name_plural = _('loans')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['lender']),
            models.Index(fields=['borrower']),
        ]
    
    def __str__(self):
        """Return string representation of the loan."""
        return f"Loan {self.id} - {self.lender} to {self.borrower} - {self.principal_amount}"
    
    def activate(self):
        """Activate the loan and generate repayment schedules."""
        if self.status == LoanStatus.PENDING:
            try:
                self.status = LoanStatus.ACTIVE
                self.approved_at = timezone.now()
                self.save(update_fields=['status', 'approved_at'])
                
                # Generate repayment schedules
                from apps.loans.services import ScheduleGenerator
                ScheduleGenerator.generate_schedules(self)
                
                return True
            except Exception as e:
                # Rollback the status change if schedule generation fails
                self.status = LoanStatus.PENDING
                self.approved_at = None
                self.save(update_fields=['status', 'approved_at'])
                # Re-raise the exception for proper handling in the view
                raise e
        return False
    
    def mark_as_paid(self):
        """Mark the loan as paid."""
        if self.status == LoanStatus.ACTIVE:
            # Check if all schedules are paid
            unpaid_schedules = self.repayment_schedules.exclude(status=RepaymentScheduleStatus.PAID)
            if not unpaid_schedules.exists():
                self.status = LoanStatus.PAID
                self.closed_at = timezone.now()
                self.save(update_fields=['status', 'closed_at'])
                return True
        return False
    
    def mark_as_defaulted(self):
        """Mark the loan as defaulted."""
        if self.status == LoanStatus.ACTIVE:
            self.status = LoanStatus.DEFAULTED
            self.save(update_fields=['status'])
            return True
        return False
    
    def cancel(self):
        """Cancel the loan."""
        if self.status == LoanStatus.PENDING:
            self.status = LoanStatus.CANCELLED
            self.save(update_fields=['status'])
            return True
        return False
    
    def soft_delete(self):
        """Soft delete the loan."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])


class RepaymentScheduleStatus(models.TextChoices):
    """Repayment schedule status choices."""
    DUE = 'DUE', _('Due')
    PENDING_CONFIRMATION = 'PENDING_CONFIRMATION', _('Pending Confirmation')
    PAID = 'PAID', _('Paid')
    LATE = 'LATE', _('Late')


class RepaymentSchedule(models.Model):
    """
    Repayment schedule model representing an EMI installment.
    """
    id = models.AutoField(primary_key=True)
    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='repayment_schedules',
        verbose_name=_('Loan')
    )
    due_date = models.DateField(_('Due date'))
    amount_due = models.DecimalField(_('Amount due'), max_digits=14, decimal_places=2)
    amount_paid = models.DecimalField(_('Amount paid'), max_digits=14, decimal_places=2, default=0)
    interest_component = models.DecimalField(
        _('Interest component'),
        max_digits=14,
        decimal_places=2,
        help_text=_('Portion of amount_due that is interest')
    )
    late_fee_accrued = models.DecimalField(
        _('Late fee accrued'),
        max_digits=14,
        decimal_places=2,
        default=0
    )
    paid_at = models.DateTimeField(_('Paid at'), null=True, blank=True)
    status = models.CharField(
        _('Status'),
        max_length=30,  # Increased from 20 to 30 to accommodate 'PENDING_CONFIRMATION'
        choices=RepaymentScheduleStatus.choices,
        default=RepaymentScheduleStatus.DUE
    )
    
    class Meta:
        """Meta options for RepaymentSchedule model."""
        verbose_name = _('repayment schedule')
        verbose_name_plural = _('repayment schedules')
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['loan', 'due_date']),
        ]
    
    def __str__(self):
        """Return string representation of the repayment schedule."""
        return f"Schedule {self.id} - Loan {self.loan.id} - Due {self.due_date}"
    
    def mark_as_pending_confirmation(self, amount=None, paid_at=None):
        """Mark the schedule as pending confirmation from lender."""
        if self.status not in [RepaymentScheduleStatus.PAID, RepaymentScheduleStatus.PENDING_CONFIRMATION]:
            if amount is not None:
                self.amount_paid = amount
            
            self.status = RepaymentScheduleStatus.PENDING_CONFIRMATION
            self.paid_at = paid_at or timezone.now()
            self.save(update_fields=['status', 'amount_paid', 'paid_at'])
            return True
        return False
    
    def confirm_payment(self):
        """Confirm payment by lender."""
        if self.status == RepaymentScheduleStatus.PENDING_CONFIRMATION:
            self.status = RepaymentScheduleStatus.PAID
            self.save(update_fields=['status'])
            
            # Check if all schedules are paid
            all_schedules = self.loan.repayment_schedules.all()
            all_paid = all(schedule.status == RepaymentScheduleStatus.PAID for schedule in all_schedules)
            
            if all_paid:
                self.loan.mark_as_paid()
            
            return True
        return False
    
    def mark_as_paid(self, amount=None, paid_at=None):
        """Mark the schedule as paid. (Legacy method, use mark_as_pending_confirmation + confirm_payment instead)"""
        if self.status != RepaymentScheduleStatus.PAID:
            if amount is not None:
                self.amount_paid = amount
            
            self.status = RepaymentScheduleStatus.PAID
            self.paid_at = paid_at or timezone.now()
            self.save(update_fields=['status', 'amount_paid', 'paid_at'])
            
            # Check if all schedules are paid
            all_schedules = self.loan.repayment_schedules.all()
            all_paid = all(schedule.status == RepaymentScheduleStatus.PAID for schedule in all_schedules)
            
            if all_paid:
                self.loan.mark_as_paid()
            
            return True
        return False
    
    def mark_as_late(self):
        """Mark the schedule as late."""
        if self.status == RepaymentScheduleStatus.DUE and self.due_date < timezone.now().date():
            self.status = RepaymentScheduleStatus.LATE
            self.save(update_fields=['status'])
            return True
        return False
    
    def apply_late_fee(self):
        """Apply late fee to the schedule."""
        if self.status == RepaymentScheduleStatus.LATE and self.loan.late_fee_pct:
            outstanding = self.amount_due - self.amount_paid
            late_fee = outstanding * (self.loan.late_fee_pct / 100)
            self.late_fee_accrued += late_fee
            self.save(update_fields=['late_fee_accrued'])
            
            # Create a transaction for the late fee
            from apps.payments.models import Transaction, TransactionType
            Transaction.objects.create(
                from_user=self.loan.borrower,
                to_user=self.loan.lender,
                amount=late_fee,
                type=TransactionType.LATE_FEE,
                related_id=str(self.loan.id)
            )
            
            return True
        return False


class Payment(models.Model):
    """
    Payment model representing a payment made by a borrower.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='loan_payments',
        verbose_name=_('Loan')
    )
    payer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments_made',
        verbose_name=_('Payer')
    )
    amount = models.DecimalField(_('Amount'), max_digits=14, decimal_places=2)
    remarks = models.TextField(_('Remarks'), blank=True)
    paid_at = models.DateTimeField(_('Paid at'), default=timezone.now)
    
    class Meta:
        """Meta options for Payment model."""
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-paid_at']
        indexes = [
            models.Index(fields=['loan']),
        ]
    
    def __str__(self):
        """Return string representation of the payment."""
        return f"Payment {self.id} - Loan {self.loan.id} - {self.amount}"
    
    def save(self, *args, **kwargs):
        """Override save method to allocate payment to schedules."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Allocate payment to schedules
            from apps.loans.services import PaymentService
            PaymentService.allocate_payment(self)


class TransactionType(models.TextChoices):
    """Transaction type choices."""
    LOAN_DISBURSEMENT = 'LOAN_DISBURSEMENT', _('Loan Disbursement')
    REPAYMENT = 'REPAYMENT', _('Repayment')
    LATE_FEE = 'LATE_FEE', _('Late Fee')
    REFUND = 'REFUND', _('Refund')


class Transaction(models.Model):
    """
    Transaction model representing a financial transaction between users.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    from_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions_sent',
        verbose_name=_('From user')
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions_received',
        verbose_name=_('To user')
    )
    amount = models.DecimalField(_('Amount'), max_digits=14, decimal_places=2)
    type = models.CharField(
        _('Type'),
        max_length=20,
        choices=TransactionType.choices
    )
    related_id = models.CharField(_('Related ID'), max_length=36)
    created_at = models.DateTimeField(_('Created at'), default=timezone.now)
    
    class Meta:
        """Meta options for Transaction model."""
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['to_user', 'created_at']),
        ]
    
    def __str__(self):
        """Return string representation of the transaction."""
        from_user_str = self.from_user or 'System'
        return f"Transaction {self.id} - {from_user_str} to {self.to_user} - {self.amount}"
