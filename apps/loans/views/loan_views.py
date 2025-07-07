"""
Loan views for the loans app.
"""
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Q

from apps.loans.models import (
    Loan,
    RepaymentSchedule,
    Payment,
    LoanStatus,
)
from apps.loans.serializers import (
    LoanSerializer,
    LoanCreateSerializer,
    RepaymentScheduleSerializer,
)


class CreateLoanView(generics.CreateAPIView):
    """
    API view for creating a loan.
    
    Creates a new loan between a lender and a borrower.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoanCreateSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new loan."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan = serializer.save()
        
        return Response({
            "status": status.HTTP_201_CREATED,
            "message": _("Loan created successfully."),
            "data": LoanSerializer(loan).data
        }, status=status.HTTP_201_CREATED)


class GetLoansView(APIView):
    """
    API view for retrieving loans associated with the authenticated user.
    
    Returns all loans where the user is either the lender or borrower,
    along with sums of payments sent and received in the current month.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Get loans associated with the authenticated user."""
        user = request.user
        
        # Get loans where user is lender or borrower
        print(user)
        loans = Loan.objects.filter(
            Q(lender=user) | Q(borrower=user),
            is_deleted=False
        )
        
        # Calculate payments sent and received in the current month
        current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_end = (current_month_start + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(seconds=1)
        
        payments_sent = Payment.objects.filter(
            payer=user,
            paid_at__range=(current_month_start, current_month_end)
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        payments_received = Payment.objects.filter(
            loan__lender=user,
            paid_at__range=(current_month_start, current_month_end)
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": _("Loans retrieved successfully."),
            "data": {
                "loans": LoanSerializer(loans, many=True).data,
                "payments_sent": payments_sent,
                "payments_received": payments_received
            }
        })


class GetLoanScheduleByIdView(generics.RetrieveAPIView):
    """
    API view for retrieving the loan schedule for a specific loan.
    
    Returns all repayment schedules for the specified loan.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RepaymentScheduleSerializer
    
    def get_queryset(self):
        """Get repayment schedules for the specified loan."""
        loan_id = self.request.query_params.get('id')
        user = self.request.user
        
        # Ensure the user is either the lender or borrower
        try:
            loan = Loan.objects.get(id=loan_id)
            if user != loan.lender and user != loan.borrower:
                return RepaymentSchedule.objects.none()
            
            return RepaymentSchedule.objects.filter(loan=loan)
        except Loan.DoesNotExist:
            return RepaymentSchedule.objects.none()
    
    def list(self, request, *args, **kwargs):
        """List repayment schedules for the specified loan."""
        queryset = self.get_queryset()
        
        if not queryset.exists():
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": _("No schedules found for this loan."),
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": _("Loan schedules retrieved successfully."),
            "data": serializer.data
        })
    
    def get(self, request, *args, **kwargs):
        """Override get method to use list method."""
        return self.list(request, *args, **kwargs)
