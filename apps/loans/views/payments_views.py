"""
Payment views for the loans app.
"""
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.loans.models import (
    Loan,
    RepaymentSchedule,
    Payment,
    LoanStatus,
    RepaymentScheduleStatus,
)
from apps.loans.serializers import (
    PaymentSerializer,
    PayEMISerializer,
    AcceptLoanSerializer,
    RepaymentScheduleSerializer,
    MarkEMIPaidSerializer,
    ConfirmEMIPaymentSerializer,
)
from apps.loans.services import PaymentService


class MarkEMIPaidView(APIView):
    """
    API view for borrowers to mark a specific EMI as paid.
    
    Records a payment and marks the EMI as pending confirmation from the lender.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Mark a specific EMI as paid by the borrower."""
        serializer = MarkEMIPaidSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        loan = serializer.validated_data['loan']
        emi = serializer.validated_data['emi']
        amount = serializer.validated_data['amount']
        payment_method = serializer.validated_data.get('payment_method', '')
        remarks = serializer.validated_data.get('remarks', '')
        
        # Create a payment record
        payment = Payment.objects.create(
            loan=loan,
            payer=request.user,
            amount=amount,
            remarks=f"Payment Method: {payment_method}. {remarks}".strip()
        )
        
        # Mark the EMI as pending confirmation
        emi.mark_as_pending_confirmation(amount=amount)
        
        # TODO: Send notification to lender about pending confirmation
        
        return Response({
            "status": "success",
            "message": _("EMI marked as paid and awaiting confirmation from lender."),
            "data": {
                "payment": PaymentSerializer(payment).data,
                "emi": RepaymentScheduleSerializer(emi).data
            }
        })


class ConfirmEMIPaymentView(APIView):
    """
    API view for lenders to confirm EMI payments.
    
    Confirms a payment that was previously marked as paid by the borrower.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Confirm an EMI payment as the lender."""
        serializer = ConfirmEMIPaymentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        loan = serializer.validated_data['loan']
        emi = serializer.validated_data['emi']
        
        # Confirm the payment
        if emi.confirm_payment():
            # TODO: Send notification to borrower about confirmed payment
            
            return Response({
                "status": "success",
                "message": _("EMI payment confirmed successfully."),
                "data": {
                    "emi": RepaymentScheduleSerializer(emi).data
                }
            })
        else:
            return Response({
                "status": "error",
                "message": _("Failed to confirm EMI payment."),
            }, status=status.HTTP_400_BAD_REQUEST)


class PayEMIView(APIView):
    """
    API view for paying a specific EMI.
    
    Records a payment for a specific EMI and marks it as pending confirmation.
    (Legacy endpoint, consider using MarkEMIPaidView + ConfirmEMIPaymentView instead)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Pay a specific EMI."""
        serializer = PayEMISerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        loan = serializer.validated_data['loan']
        emi = serializer.validated_data['emi']
        amount = serializer.validated_data['amount']
        remarks = serializer.validated_data.get('remarks', '')
        
        # Create a payment record
        payment = Payment.objects.create(
            loan=loan,
            payer=request.user,
            amount=amount,
            remarks=remarks
        )
        
        # Mark the EMI as pending confirmation
        emi.mark_as_pending_confirmation(amount=amount)
        
        return Response({
            "status": "success",
            "message": _("EMI marked as paid and awaiting confirmation from lender."),
            "data": {
                "payment": PaymentSerializer(payment).data,
                "emi": RepaymentScheduleSerializer(emi).data
            }
        })


class AcceptLoanView(APIView):
    """
    API view for accepting a loan.
    
    Changes the status of a loan based on who is accepting it (lender or borrower).
    If both parties have accepted, the loan becomes 'Active'.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Accept a loan."""
        serializer = AcceptLoanSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        loan = serializer.validated_data['loan']
        current_user = request.user
        
        # The serializer has already validated that:
        # 1. The loan is in PENDING status
        # 2. The current user is not the creator
        # 3. The current user is either the lender or borrower
        
        try:
            if loan.activate():
                return Response({
                    "status": "success",
                    "message": _("Loan accepted and activated successfully."),
                    "data": {}
                })
            else:
                return Response({
                    "status": "error",
                    "message": _("Failed to activate loan. It may already be active or in another state."),
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error activating loan {loan.id}: {str(e)}")
            
            return Response({
                "status": "error",
                "message": _("An error occurred while activating the loan."),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetAllPaymentsRelatedToUserView(APIView):
    """
    API view for retrieving all loan schedules related to the authenticated user.
    
    Returns all loan schedules where the user is either the lender or borrower,
    filtered by payment type (received or sent).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Get all payments related to the authenticated user."""
        user = request.user
        payment_type = request.query_params.get('paymentType', 'all')
        
        if payment_type == 'received':
            # User is lender
            schedules = RepaymentSchedule.objects.filter(loan__lender=user)
        elif payment_type == 'sent':
            # User is borrower
            schedules = RepaymentSchedule.objects.filter(loan__borrower=user)
        else:
            # Both
            schedules = RepaymentSchedule.objects.filter(
                loan__lender=user
            ) | RepaymentSchedule.objects.filter(
                loan__borrower=user
            )
        
        serializer = RepaymentScheduleSerializer(schedules, many=True)
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": _("Payments retrieved successfully."),
            "data": serializer.data
        })
