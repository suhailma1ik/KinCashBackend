"""
URL patterns for the loans app.
"""
from django.urls import path

from apps.loans.views.loan_views import (
    CreateLoanView,
    GetLoansView,
    GetLoanScheduleByIdView,
)
from apps.loans.views.payments_views import (
    PayEMIView,
    AcceptLoanView,
    GetAllPaymentsRelatedToUserView,
    MarkEMIPaidView,
    ConfirmEMIPaymentView,
)
from apps.loans.views.loan_status_views import (
    GetLoanByIdView,
    RejectLoanView,
)

urlpatterns = [
    # Loan endpoints
    path('create_loan/', CreateLoanView.as_view(), name='create_loan'),
    path('get_loans/', GetLoansView.as_view(), name='get_loans'),
    path('get_loans_by_id/', GetLoanScheduleByIdView.as_view(), name='get_loan_schedule_by_id'),
    path('get_transactions_done/', GetLoansView.as_view(), name='get_transactions_done'),
    path('get_loan/', GetLoanByIdView.as_view(), name='get_loan'),
    
    # Payment endpoints
    path('pay_emi/', PayEMIView.as_view(), name='pay_emi'),  # Legacy endpoint
    path('mark_emi_paid/', MarkEMIPaidView.as_view(), name='mark_emi_paid'),  # Step 1: Borrower marks EMI as paid
    path('confirm_emi_payment/', ConfirmEMIPaymentView.as_view(), name='confirm_emi_payment'),  # Step 2: Lender confirms payment
    path('accept_loan/', AcceptLoanView.as_view(), name='accept_loan'),
    path('reject_loan/', RejectLoanView.as_view(), name='reject_loan'),
    path('get_user_payments/', GetAllPaymentsRelatedToUserView.as_view(), name='get_user_payments'),
]
