"""
Serializers for the payments app.
"""
from rest_framework import serializers

from apps.payments.models import Payment
from apps.users.serializers import UserSerializer


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for the Payment model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'loan', 'user', 'amount', 'status',
            'idempotency_key', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Payment."""
    
    class Meta:
        model = Payment
        fields = ['loan', 'amount', 'idempotency_key']
        
    def validate_idempotency_key(self, value):
        """
        Validate that the idempotency key is unique.
        """
        if Payment.objects.filter(idempotency_key=value).exists():
            raise serializers.ValidationError(
                "A payment with this idempotency key already exists."
            )
        return value
