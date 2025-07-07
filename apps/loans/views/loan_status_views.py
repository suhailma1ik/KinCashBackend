"""
Loan status views for the loans app.
"""
from django.utils.translation import gettext_lazy as _
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.loans.models import Loan, LoanStatus
from apps.loans.serializers import LoanSerializer


class GetLoanByIdView(APIView):
    """
    API view for retrieving a specific loan by ID.
    
    Returns detailed information about a loan.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Get a specific loan by ID."""
        loan_id = request.query_params.get('id')
        
        if not loan_id:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": _("Loan ID is required."),
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            loan = Loan.objects.get(id=loan_id)
            
            # Ensure the user is either the lender or borrower
            if request.user != loan.lender and request.user != loan.borrower:
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": _("You do not have permission to view this loan."),
                }, status=status.HTTP_403_FORBIDDEN)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": _("Loan retrieved successfully."),
                "data": LoanSerializer(loan).data
            })
        except Loan.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": _("Loan not found."),
            }, status=status.HTTP_404_NOT_FOUND)


class RejectLoanView(APIView):
    """
    API view for rejecting a loan.
    
    Changes the status of a loan to 'Cancelled'.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Reject a loan."""
        loan_id = request.data.get('loan_id')
        
        if not loan_id:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": _("Loan ID is required."),
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            loan = Loan.objects.get(id=loan_id)
            
            # Ensure the user is authorized to reject this loan
            current_user = request.user
            if loan.status == LoanStatus.PENDING and (current_user == loan.lender or current_user == loan.borrower):
                
                # Cancel the loan
                loan.status = LoanStatus.CANCELLED
                loan.save(update_fields=['status'])
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": _("Loan rejected successfully."),
                    "data": {}
                })
            else:
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": _("You do not have permission to reject this loan."),
                }, status=status.HTTP_403_FORBIDDEN)
            
        except Loan.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": _("Loan not found."),
            }, status=status.HTTP_404_NOT_FOUND)
