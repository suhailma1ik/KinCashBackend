"""
Serializers for the notifications app.
"""
from rest_framework import serializers

from apps.users.serializers import UserSerializer
from apps.notifications.models import Notification, WebSocketNotification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)
    
    class Meta:
        """Meta options for NotificationSerializer."""
        model = Notification
        fields = [
            'id', 'loan', 'sender', 'recipient', 'title',
            'body', 'is_read', 'created_at'
        ]
        read_only_fields = fields


class WebSocketNotificationSerializer(serializers.ModelSerializer):
    """Serializer for WebSocketNotification model."""
    notification = NotificationSerializer(read_only=True)
    
    class Meta:
        """Meta options for WebSocketNotificationSerializer."""
        model = WebSocketNotification
        fields = [
            'id', 'notification', 'type', 'data', 'is_sent', 'sent_at'
        ]
        read_only_fields = fields


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a notification."""
    recipient_id = serializers.UUIDField(required=True)
    loan_id = serializers.UUIDField(required=False)
    
    class Meta:
        """Meta options for NotificationCreateSerializer."""
        model = Notification
        fields = ['recipient_id', 'loan_id', 'title', 'body']
    
    def create(self, validated_data):
        """Create a notification."""
        recipient_id = validated_data.pop('recipient_id')
        loan_id = validated_data.pop('loan_id', None)
        
        # Get the recipient and loan
        from apps.users.models import User
        from apps.loans.models import Loan
        
        recipient = User.objects.get(id=recipient_id)
        loan = Loan.objects.get(id=loan_id) if loan_id else None
        
        # Create the notification
        notification = Notification.objects.create(
            sender=self.context['request'].user,
            recipient=recipient,
            loan=loan,
            **validated_data
        )
        
        return notification


class MarkNotificationReadSerializer(serializers.Serializer):
    """Serializer for marking a notification as read."""
    notification_id = serializers.UUIDField(required=True)
    
    def validate(self, attrs):
        """Validate the notification ID."""
        notification_id = attrs.get('notification_id')
        user = self.context['request'].user
        
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
            attrs['notification'] = notification
            return attrs
        except Notification.DoesNotExist:
            raise serializers.ValidationError("Notification not found.")
