"""
Views for the payments app.
"""
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.payments.models import Payment
from apps.payments.serializers import PaymentSerializer, PaymentCreateSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payments.
    """
    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new payment."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set the user to the current authenticated user
        payment = serializer.save(user=request.user)
        
        # Return the created payment with the standard response format
        return Response(
            {
                "status": "success",
                "message": "Payment created successfully.",
                "data": PaymentSerializer(payment).data
            },
            status=status.HTTP_201_CREATED
        )
    
    def list(self, request, *args, **kwargs):
        """List all payments."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response(
            {
                "status": "success",
                "message": "Payments retrieved successfully.",
                "data": serializer.data
            }
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific payment."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response(
            {
                "status": "success",
                "message": "Payment retrieved successfully.",
                "data": serializer.data
            }
        )
