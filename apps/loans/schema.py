"""
OpenAPI schema customizations for the loans app.
"""
from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse

from apps.loans.views.loan_views import (
    CreateLoanView,
    GetLoansView,
    GetLoanScheduleByIdView,
)
from apps.loans.views.payments_views import (
    PayEMIView,
    AcceptLoanView,
    GetAllPaymentsRelatedToUserView,
)


class CreateLoanViewSchema(OpenApiViewExtension):
    """Schema customization for CreateLoanView."""
    target_class = CreateLoanView
    
    def view_replacement(self):
        """Replace the view with customized schema."""
        class Extended(self.target_class):
            """Extended view with customized schema."""
            @extend_schema(
                summary="Create a new loan",
                description="Creates a new loan between a lender and a borrower.",
                responses={
                    201: OpenApiResponse(
                        description="Loan created successfully",
                        examples=[
                            OpenApiExample(
                                name="Successful Loan Creation",
                                value={
                                    "status": 201,
                                    "message": "Loan created successfully.",
                                    "data": {
                                        "id": "loan_id",
                                        "lender": "lender_id",
                                        "borrower": "borrower_id",
                                        "principal_amount": "1000.00",
                                        "interest_rate_pct": "5.0",
                                        "term_months": 12,
                                        "emi_cycle": "MONTHLY",
                                        "status": "PENDING",
                                        "late_fee_pct": "1.0",
                                        "created_at": "2023-01-01T00:00:00Z",
                                        "approved_at": null,
                                        "closed_at": null,
                                        "start_date": "2023-01-01",
                                        "end_date": null
                                    }
                                }
                            )
                        ]
                    ),
                    400: OpenApiResponse(
                        description="Validation error",
                        examples=[
                            OpenApiExample(
                                name="Validation Error",
                                value={
                                    "status": 400,
                                    "message": "Validation failed",
                                    "errors": {
                                        "lender": ["This field is required."]
                                    }
                                }
                            )
                        ]
                    )
                }
            )
            def post(self, request, *args, **kwargs):
                return super().post(request, *args, **kwargs)
        
        return Extended


class GetLoansViewSchema(OpenApiViewExtension):
    """Schema customization for GetLoansView."""
    target_class = GetLoansView
    
    def view_replacement(self):
        """Replace the view with customized schema."""
        class Extended(self.target_class):
            """Extended view with customized schema."""
            @extend_schema(
                summary="Get user loans",
                description="Retrieves all loans associated with the authenticated user.",
                responses={
                    200: OpenApiResponse(
                        description="Loans retrieved successfully",
                        examples=[
                            OpenApiExample(
                                name="User Loans",
                                value={
                                    "status": 200,
                                    "message": "Loans retrieved successfully.",
                                    "data": {
                                        "loans": [
                                            {
                                                "id": "loan_id",
                                                "lender": "lender_id",
                                                "borrower": "borrower_id",
                                                "principal_amount": "1000.00",
                                                "interest_rate_pct": "5.0",
                                                "term_months": 12,
                                                "emi_cycle": "MONTHLY",
                                                "status": "ACTIVE",
                                                "late_fee_pct": "1.0",
                                                "created_at": "2023-01-01T00:00:00Z",
                                                "approved_at": "2023-01-02T00:00:00Z",
                                                "closed_at": null,
                                                "start_date": "2023-01-02",
                                                "end_date": "2024-01-02"
                                            }
                                        ],
                                        "payments_sent": "500.00",
                                        "payments_received": "300.00"
                                    }
                                }
                            )
                        ]
                    )
                }
            )
            def get(self, request, *args, **kwargs):
                return super().get(request, *args, **kwargs)
        
        return Extended


class GetLoanScheduleByIdViewSchema(OpenApiViewExtension):
    """Schema customization for GetLoanScheduleByIdView."""
    target_class = GetLoanScheduleByIdView
    
    def view_replacement(self):
        """Replace the view with customized schema."""
        class Extended(self.target_class):
            """Extended view with customized schema."""
            @extend_schema(
                summary="Get loan schedule",
                description="Retrieves the loan schedule for a specific loan.",
                parameters=[
                    OpenApiParameter(
                        name="id",
                        description="Loan ID",
                        required=True,
                        type=str
                    )
                ],
                responses={
                    200: OpenApiResponse(
                        description="Loan schedules retrieved successfully",
                        examples=[
                            OpenApiExample(
                                name="Loan Schedules",
                                value={
                                    "status": 200,
                                    "message": "Loan schedules retrieved successfully.",
                                    "data": [
                                        {
                                            "id": 1,
                                            "loan": "loan_id",
                                            "due_date": "2023-02-01",
                                            "amount_due": "100.00",
                                            "amount_paid": "0.00",
                                            "interest_component": "5.00",
                                            "late_fee_accrued": "0.00",
                                            "paid_at": null,
                                            "status": "DUE",
                                            "lender": "lender_id",
                                            "borrower": "borrower_id"
                                        }
                                    ]
                                }
                            )
                        ]
                    ),
                    404: OpenApiResponse(
                        description="No schedules found",
                        examples=[
                            OpenApiExample(
                                name="No Schedules",
                                value={
                                    "status": 404,
                                    "message": "No schedules found for this loan."
                                }
                            )
                        ]
                    )
                }
            )
            def get(self, request, *args, **kwargs):
                return super().get(request, *args, **kwargs)
        
        return Extended


class PayEMIViewSchema(OpenApiViewExtension):
    """Schema customization for PayEMIView."""
    target_class = PayEMIView
    
    def view_replacement(self):
        """Replace the view with customized schema."""
        class Extended(self.target_class):
            """Extended view with customized schema."""
            @extend_schema(
                summary="Pay EMI",
                description="Records a payment for a specific EMI and updates its status.",
                responses={
                    200: OpenApiResponse(
                        description="EMI paid successfully",
                        examples=[
                            OpenApiExample(
                                name="EMI Payment",
                                value={
                                    "status": 200,
                                    "message": "EMI paid successfully.",
                                    "data": {
                                        "payment": {
                                            "id": "payment_id",
                                            "loan": "loan_id",
                                            "amount": "100.00",
                                            "remarks": "First EMI payment",
                                            "paid_at": "2023-02-01T00:00:00Z"
                                        },
                                        "emi": {
                                            "id": 1,
                                            "loan": "loan_id",
                                            "due_date": "2023-02-01",
                                            "amount_due": "100.00",
                                            "amount_paid": "100.00",
                                            "interest_component": "5.00",
                                            "late_fee_accrued": "0.00",
                                            "paid_at": "2023-02-01T00:00:00Z",
                                            "status": "PAID",
                                            "lender": "lender_id",
                                            "borrower": "borrower_id"
                                        }
                                    }
                                }
                            )
                        ]
                    ),
                    400: OpenApiResponse(
                        description="Validation error",
                        examples=[
                            OpenApiExample(
                                name="EMI Already Paid",
                                value={
                                    "status": 400,
                                    "message": "EMI already paid."
                                }
                            )
                        ]
                    ),
                    404: OpenApiResponse(
                        description="Loan or EMI not found",
                        examples=[
                            OpenApiExample(
                                name="Loan Not Found",
                                value={
                                    "status": 404,
                                    "message": "Loan not found."
                                }
                            )
                        ]
                    )
                }
            )
            def post(self, request, *args, **kwargs):
                return super().post(request, *args, **kwargs)
        
        return Extended


class AcceptLoanViewSchema(OpenApiViewExtension):
    """Schema customization for AcceptLoanView."""
    target_class = AcceptLoanView
    
    def view_replacement(self):
        """Replace the view with customized schema."""
        class Extended(self.target_class):
            """Extended view with customized schema."""
            @extend_schema(
                summary="Accept loan",
                description="Changes the status of a loan to 'Active'.",
                responses={
                    200: OpenApiResponse(
                        description="Loan accepted successfully",
                        examples=[
                            OpenApiExample(
                                name="Loan Acceptance",
                                value={
                                    "status": 200,
                                    "message": "Loan accepted successfully.",
                                    "data": {}
                                }
                            )
                        ]
                    ),
                    400: OpenApiResponse(
                        description="Failed to accept loan",
                        examples=[
                            OpenApiExample(
                                name="Failed to Accept",
                                value={
                                    "status": 400,
                                    "message": "Failed to accept loan."
                                }
                            )
                        ]
                    ),
                    404: OpenApiResponse(
                        description="Loan not found",
                        examples=[
                            OpenApiExample(
                                name="Loan Not Found",
                                value={
                                    "status": 404,
                                    "message": "Loan not found."
                                }
                            )
                        ]
                    )
                }
            )
            def post(self, request, *args, **kwargs):
                return super().post(request, *args, **kwargs)
        
        return Extended
