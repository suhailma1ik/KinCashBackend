"""
Services for the loans app.
"""
import datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from django.db import transaction
from django.utils import timezone

from apps.loans.models import (
    Loan,
    RepaymentSchedule,
    Payment,
    Transaction,
    LoanStatus,
    EMICycle,
    RepaymentScheduleStatus,
    TransactionType,
)


class ScheduleGenerator:
    """Service for generating repayment schedules."""
    
    @staticmethod
    def generate_schedules(loan):
        """
        Generate repayment schedules for a loan.
        
        Args:
            loan: The loan to generate schedules for.
        
        Returns:
            List of created RepaymentSchedule objects.
        """
        if loan.status != LoanStatus.ACTIVE:
            return []
        
        # Clear existing schedules if any
        loan.repayment_schedules.all().delete()
        
        # Get the due date from the loan or use a default
        due_day = getattr(loan, 'due_date', 15)
        
        # Calculate EMI amount
        emi_amount = ScheduleGenerator.calculate_emi(
            principal=loan.principal_amount,
            rate=loan.interest_rate_pct,
            term=loan.term_months,
            cycle=loan.emi_cycle
        )
        
        # Generate schedules
        schedules = []
        start_date = loan.approved_at.date()
        
        # Adjust start date to the due day
        if loan.emi_cycle == EMICycle.MONTHLY:
            # Set the due day, handling month end cases
            try:
                start_date = start_date.replace(day=due_day)
            except ValueError:
                # Handle case where due_day is greater than days in month
                # Use the last day of the month
                if due_day >= 28:
                    next_month = start_date.replace(day=1) + relativedelta(months=1)
                    start_date = next_month - relativedelta(days=1)
            
            # If start date is in the past, move to next month
            if start_date < timezone.now().date():
                start_date = start_date + relativedelta(months=1)
        else:  # Weekly
            # Move to the next occurrence of the due day
            days_ahead = due_day - start_date.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            start_date = start_date + datetime.timedelta(days=days_ahead)
        
        remaining_principal = loan.principal_amount
        
        # Determine number of installments based on cycle
        if loan.emi_cycle == EMICycle.MONTHLY:
            num_installments = loan.term_months
        else:  # Weekly
            num_installments = loan.term_months * 4  # Approximate weeks in months
        
        with transaction.atomic():
            for i in range(num_installments):
                # Calculate due date for this installment
                if loan.emi_cycle == EMICycle.MONTHLY:
                    due_date = start_date + relativedelta(months=i)
                else:  # Weekly
                    due_date = start_date + datetime.timedelta(weeks=i)
                
                # Calculate interest for this period
                if loan.emi_cycle == EMICycle.MONTHLY:
                    period_rate = loan.interest_rate_pct / 12 / 100
                else:  # Weekly
                    period_rate = loan.interest_rate_pct / 52 / 100
                
                interest = remaining_principal * period_rate
                
                # For the last installment, adjust to ensure total equals principal
                if i == num_installments - 1:
                    principal_component = remaining_principal
                    amount_due = principal_component + interest
                else:
                    principal_component = min(emi_amount - interest, remaining_principal)
                    amount_due = emi_amount
                
                # Create schedule
                schedule = RepaymentSchedule.objects.create(
                    loan=loan,
                    due_date=due_date,
                    amount_due=amount_due,
                    interest_component=interest,
                )
                schedules.append(schedule)
                
                # Update remaining principal
                remaining_principal -= principal_component
                if remaining_principal <= 0:
                    break
        
        return schedules
    
    @staticmethod
    def calculate_emi(principal, rate, term, cycle):
        """
        Calculate EMI amount using the formula:
        EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
        
        Args:
            principal: Loan principal amount.
            rate: Annual interest rate in percentage.
            term: Loan term in months.
            cycle: EMI cycle (MONTHLY or WEEKLY).
        
        Returns:
            Decimal: EMI amount.
        """
        principal = Decimal(str(principal))
        rate = Decimal(str(rate))
        
        # Convert annual rate to period rate
        if cycle == EMICycle.MONTHLY:
            period_rate = rate / 12 / 100
            num_periods = term
        else:  # Weekly
            period_rate = rate / 52 / 100
            num_periods = term * 4  # Approximate weeks in months
        
        # Handle edge case of zero interest
        if rate == 0:
            return principal / num_periods
        
        # Calculate EMI
        emi = principal * period_rate * (1 + period_rate) ** num_periods
        emi = emi / ((1 + period_rate) ** num_periods - 1)
        
        return emi.quantize(Decimal('0.01'))


class PaymentService:
    """Service for handling payments."""
    
    @staticmethod
    def allocate_payment(payment):
        """
        Allocate a payment to repayment schedules.
        
        Args:
            payment: The payment to allocate.
        
        Returns:
            List of updated RepaymentSchedule objects.
        """
        loan = payment.loan
        amount = payment.amount
        remaining = amount
        updated_schedules = []
        
        # Get unpaid schedules ordered by due date
        unpaid_schedules = loan.repayment_schedules.exclude(
            status=RepaymentScheduleStatus.PAID
        ).order_by('due_date')
        
        with transaction.atomic():
            # Create transaction record
            transaction_obj = Transaction.objects.create(
                from_user=payment.payer,
                to_user=loan.lender,
                amount=amount,
                type=TransactionType.REPAYMENT,
                related_id=str(loan.id)
            )
            
            # Allocate payment to schedules
            for schedule in unpaid_schedules:
                if remaining <= 0:
                    break
                
                # Calculate amount due including late fee
                total_due = schedule.amount_due + schedule.late_fee_accrued - schedule.amount_paid
                
                if remaining >= total_due:
                    # Full payment for this schedule
                    schedule.amount_paid += total_due
                    schedule.paid_at = payment.paid_at
                    schedule.status = RepaymentScheduleStatus.PAID
                    schedule.save()
                    remaining -= total_due
                else:
                    # Partial payment for this schedule
                    schedule.amount_paid += remaining
                    schedule.save()
                    remaining = 0
                
                updated_schedules.append(schedule)
            
            # Check if loan is fully paid
            loan.mark_as_paid()
        
        return updated_schedules
    
    @staticmethod
    def mark_overdue_loans():
        """
        Mark overdue loans and schedules.
        
        Returns:
            Tuple of (marked_schedules, applied_late_fees).
        """
        today = timezone.now().date()
        
        # Get active loans with due schedules
        active_loans = Loan.objects.filter(status=LoanStatus.ACTIVE)
        
        marked_schedules = []
        applied_late_fees = []
        
        for loan in active_loans:
            # Find overdue schedules
            overdue_schedules = loan.repayment_schedules.filter(
                status=RepaymentScheduleStatus.DUE,
                due_date__lt=today
            )
            
            for schedule in overdue_schedules:
                # Mark as late
                if schedule.mark_as_late():
                    marked_schedules.append(schedule)
                
                # Apply late fee if configured
                if loan.late_fee_pct and schedule.apply_late_fee():
                    applied_late_fees.append(schedule)
        
        return marked_schedules, applied_late_fees
