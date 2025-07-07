"""
Serializers for the loans app.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.users.models import User
from apps.users.serializers import UserSerializer
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


class RepaymentScheduleSerializer(serializers.ModelSerializer):
    """Serializer for RepaymentSchedule model."""
    lender = serializers.SerializerMethodField()
    borrower = serializers.SerializerMethodField()
    
    class Meta:
        """Meta options for RepaymentScheduleSerializer."""
        model = RepaymentSchedule
        fields = [
            'id', 'loan', 'due_date', 'amount_due', 'amount_paid',
            'interest_component', 'late_fee_accrued', 'paid_at',
            'status', 'lender', 'borrower'
        ]
        read_only_fields = [
            'id', 'loan', 'due_date', 'amount_due', 'amount_paid',
            'interest_component', 'late_fee_accrued', 'paid_at',
            'status', 'lender', 'borrower'
        ]
    
    def get_lender(self, obj):
        """Get lender with ID and name information."""
        user = obj.loan.lender
        return {
            'id': str(user.id),
            'name': f"{user.first_name} {user.last_name}".strip() or user.username
        }
    
    def get_borrower(self, obj):
        """Get borrower with ID and name information."""
        user = obj.loan.borrower
        return {
            'id': str(user.id),
            'name': f"{user.first_name} {user.last_name}".strip() or user.username
        }


class LoanSerializer(serializers.ModelSerializer):
    """Serializer for Loan model."""
    lender = serializers.SerializerMethodField()
    borrower = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    
    class Meta:
        """Meta options for LoanSerializer."""
        model = Loan
        fields = [
            'id', 'lender', 'borrower', 'principal_amount',
            'interest_rate_pct', 'term_months', 'emi_cycle',
            'status', 'late_fee_pct', 'created_at', 'approved_at',
            'closed_at', 'start_date', 'end_date', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'approved_at', 'closed_at', 'status', 'created_by']
    
    def get_start_date(self, obj):
        """Get start date from approved_at or created_at."""
        return obj.approved_at.date() if obj.approved_at else obj.created_at.date()
    
    def get_end_date(self, obj):
        """Get end date from closed_at or calculate based on term_months."""
        if obj.closed_at:
            return obj.closed_at.date()
        
        if obj.approved_at:
            if obj.emi_cycle == EMICycle.MONTHLY:
                return obj.approved_at.date().replace(
                    month=((obj.approved_at.month - 1 + obj.term_months) % 12) + 1,
                    year=obj.approved_at.year + ((obj.approved_at.month - 1 + obj.term_months) // 12)
                )
            else:  # Weekly
                import datetime
                weeks = obj.term_months * 4  # Approximate weeks in months
                return obj.approved_at.date() + datetime.timedelta(weeks=weeks)
        
        return None
        
    def get_lender(self, obj):
        """Get lender with name information."""
        if obj.lender:
            return {
                'id': str(obj.lender.id),
                'name': f"{obj.lender.first_name} {obj.lender.last_name}".strip()
            }
        return None
    
    def get_borrower(self, obj):
        """Get borrower with name information."""
        if obj.borrower:
            return {
                'id': str(obj.borrower.id),
                'name': f"{obj.borrower.first_name} {obj.borrower.last_name}".strip()
            }
        return None
    
    def get_created_by(self, obj):
        """Get creator information (id & name)."""
        if obj.created_by:
            return {
                'id': str(obj.created_by.id),
                'name': f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
            }
        return None


class LoanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Loan."""
    lender = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=True
    )
    borrower = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=True
    )
    due_date = serializers.IntegerField(
        min_value=1,
        max_value=31,
        required=True,
        help_text=_("Day of the month for EMI due date (1-31)")
    )
    is_lender = serializers.BooleanField(
        required=True,
        help_text=_("True if the current user is the lender, false if borrower")
    )
    
    class Meta:
        """Meta options for LoanCreateSerializer."""
        model = Loan
        fields = [
            'lender', 'borrower', 'principal_amount', 'interest_rate_pct',
            'term_months', 'emi_cycle', 'late_fee_pct', 'due_date', 'is_lender'
        ]
    
    def validate(self, attrs):
        """Validate loan creation data."""
        lender = attrs.get('lender')
        borrower = attrs.get('borrower')
        is_lender = attrs.pop('is_lender')
        due_date = attrs.pop('due_date')
        
        # Ensure lender and borrower are different users
        if lender == borrower:
            raise serializers.ValidationError(_("Lender and borrower cannot be the same user."))
        
        # Ensure the current user is either the lender or borrower
        current_user = self.context['request'].user
        if is_lender and current_user != lender:
            raise serializers.ValidationError(_("You must be the lender to create this loan."))
        elif not is_lender and current_user != borrower:
            raise serializers.ValidationError(_("You must be the borrower to create this loan."))
        
        # Store due_date in context for later use in create method
        self.context['due_date'] = due_date
        
        return attrs
    
    def create(self, validated_data):
        """Create a new loan."""
        # Remove due_date and is_lender from validated_data
        due_date = validated_data.pop('due_date', None)
        is_lender = validated_data.pop('is_lender', False)
        
        # Set the initial status to PENDING
        current_user = self.context['request'].user
        validated_data['status'] = LoanStatus.PENDING
        
        # Store information about who created the loan
        validated_data['created_by'] = current_user
        
        # Create the loan
        loan = Loan.objects.create(**validated_data)
        
        # Store the due date for schedule generation
        self.context['due_date'] = due_date
        
        return loan


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    payer = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        """Meta options for PaymentSerializer."""
        model = Payment
        fields = ['id', 'loan', 'payer', 'amount', 'remarks', 'paid_at']
        read_only_fields = ['id', 'payer', 'paid_at']
    
    def validate_loan(self, value):
        """Validate that the loan exists and is active."""
        if value.status != LoanStatus.ACTIVE:
            raise serializers.ValidationError(_("Payments can only be made for active loans."))
        return value
    
    def validate(self, attrs):
        """Validate payment data."""
        loan = attrs.get('loan')
        current_user = self.context['request'].user
        
        # Ensure the current user is the borrower
        if current_user != loan.borrower:
            raise serializers.ValidationError(_("Only the borrower can make payments."))
        
        return attrs
    
    def create(self, validated_data):
        """Create a new payment."""
        # Set the payer to the current user
        validated_data['payer'] = self.context['request'].user
        
        return super().create(validated_data)


class MarkEMIPaidSerializer(serializers.Serializer):
    """Serializer for borrowers to mark a specific EMI as paid."""
    loan_id = serializers.UUIDField(required=True)
    emi_id = serializers.IntegerField(required=True)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, required=True)
    payment_method = serializers.CharField(required=False, allow_blank=True, max_length=50)
    remarks = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate EMI payment data."""
        loan_id = attrs.get('loan_id')
        emi_id = attrs.get('emi_id')
        amount = attrs.get('amount')
        
        try:
            loan = Loan.objects.get(id=loan_id)
        except Loan.DoesNotExist:
            raise serializers.ValidationError(_("Loan not found."))
        
        try:
            emi = RepaymentSchedule.objects.get(id=emi_id, loan=loan)
        except RepaymentSchedule.DoesNotExist:
            raise serializers.ValidationError(_("EMI not found."))
        
        # Ensure the current user is the borrower
        current_user = self.context['request'].user
        if current_user != loan.borrower:
            raise serializers.ValidationError(_("Only the borrower can mark EMIs as paid."))
        
        # Ensure the EMI is not already paid or pending confirmation
        if emi.status == RepaymentScheduleStatus.PAID:
            raise serializers.ValidationError(_("EMI already paid."))
        if emi.status == RepaymentScheduleStatus.PENDING_CONFIRMATION:
            raise serializers.ValidationError(_("EMI already marked as paid and awaiting confirmation."))
        
        # Ensure the amount is sufficient
        total_due = emi.amount_due + emi.late_fee_accrued - emi.amount_paid
        if amount < total_due:
            raise serializers.ValidationError(_(f"Amount must be at least {total_due}."))
        
        attrs['loan'] = loan
        attrs['emi'] = emi
        
        return attrs


class ConfirmEMIPaymentSerializer(serializers.Serializer):
    """Serializer for lenders to confirm EMI payments."""
    loan_id = serializers.UUIDField(required=True)
    emi_id = serializers.IntegerField(required=True)
    
    def validate(self, attrs):
        """Validate EMI confirmation data."""
        loan_id = attrs.get('loan_id')
        emi_id = attrs.get('emi_id')
        
        try:
            loan = Loan.objects.get(id=loan_id)
        except Loan.DoesNotExist:
            raise serializers.ValidationError(_("Loan not found."))
        
        try:
            emi = RepaymentSchedule.objects.get(id=emi_id, loan=loan)
        except RepaymentSchedule.DoesNotExist:
            raise serializers.ValidationError(_("EMI not found."))
        
        # Ensure the current user is the lender
        current_user = self.context['request'].user
        if current_user != loan.lender:
            raise serializers.ValidationError(_("Only the lender can confirm EMI payments."))
        
        # Ensure the EMI is in pending confirmation status
        if emi.status != RepaymentScheduleStatus.PENDING_CONFIRMATION:
            raise serializers.ValidationError(_("This EMI is not awaiting confirmation."))
        
        attrs['loan'] = loan
        attrs['emi'] = emi
        
        return attrs


class PayEMISerializer(serializers.Serializer):
    """Serializer for paying a specific EMI."""
    loan_id = serializers.UUIDField(required=True)
    emi_id = serializers.IntegerField(required=True)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, required=True)
    remarks = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate EMI payment data."""
        loan_id = attrs.get('loan_id')
        emi_id = attrs.get('emi_id')
        amount = attrs.get('amount')
        
        try:
            loan = Loan.objects.get(id=loan_id)
        except Loan.DoesNotExist:
            raise serializers.ValidationError(_("Loan not found."))
        
        try:
            emi = RepaymentSchedule.objects.get(id=emi_id, loan=loan)
        except RepaymentSchedule.DoesNotExist:
            raise serializers.ValidationError(_("EMI not found."))
        
        # Ensure the current user is the borrower
        current_user = self.context['request'].user
        if current_user != loan.borrower:
            raise serializers.ValidationError(_("Only the borrower can make payments."))
        
        # Ensure the EMI is not already paid
        if emi.status == RepaymentScheduleStatus.PAID:
            raise serializers.ValidationError(_("EMI already paid."))
        
        # Ensure the amount is sufficient
        total_due = emi.amount_due + emi.late_fee_accrued - emi.amount_paid
        if amount < total_due:
            raise serializers.ValidationError(_(f"Amount must be at least {total_due}."))
        
        attrs['loan'] = loan
        attrs['emi'] = emi
        
        return attrs


class AcceptLoanSerializer(serializers.Serializer):
    """Serializer for accepting a loan."""
    loan_id = serializers.UUIDField(required=True)
    
    def validate(self, attrs):
        """Validate loan acceptance data."""
        loan_id = attrs.get('loan_id')
        
        try:
            loan = Loan.objects.get(id=loan_id)
        except Loan.DoesNotExist:
            raise serializers.ValidationError(_("Loan not found."))
        
        # Get the current user
        current_user = self.context['request'].user
        
        # Check if the loan can be accepted
        if loan.status != LoanStatus.PENDING:
            raise serializers.ValidationError(_("This loan cannot be accepted in its current state."))
        
        # Check if the current user is eligible to accept this loan
        if current_user == loan.created_by:
            raise serializers.ValidationError(_("You cannot accept a loan you created."))
        
        if current_user != loan.lender and current_user != loan.borrower:
            raise serializers.ValidationError(_("Only the lender or borrower can accept this loan."))
        
        attrs['loan'] = loan
        
        return attrs


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model."""
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    
    class Meta:
        """Meta options for TransactionSerializer."""
        model = Transaction
        fields = ['id', 'from_user', 'to_user', 'amount', 'type', 'related_id', 'created_at']
        read_only_fields = fields
