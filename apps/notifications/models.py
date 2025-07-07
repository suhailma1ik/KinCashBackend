"""
Notification models for H.E.L.P Backend.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.users.models import User
from apps.loans.models import Loan


class Notification(models.Model):
    """
    Notification model representing a system or lender-initiated message.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        verbose_name=_('Loan')
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        verbose_name=_('Sender')
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_notifications',
        verbose_name=_('Recipient')
    )
    title = models.CharField(_('Title'), max_length=255)
    body = models.TextField(_('Body'))
    is_read = models.BooleanField(_('Is read'), default=False)
    created_at = models.DateTimeField(_('Created at'), default=timezone.now)
    
    class Meta:
        """Meta options for Notification model."""
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        """Return string representation of the notification."""
        return f"{self.title} - From {self.sender} to {self.recipient}"
    
    def mark_as_read(self):
        """Mark the notification as read."""
        self.is_read = True
        self.save(update_fields=['is_read'])
        return True


class NotificationType(models.TextChoices):
    """Notification type choices."""
    LOAN_CREATED = 'LOAN_CREATED', _('Loan Created')
    LOAN_ACCEPTED = 'LOAN_ACCEPTED', _('Loan Accepted')
    PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', _('Payment Received')
    PAYMENT_DUE = 'PAYMENT_DUE', _('Payment Due')
    PAYMENT_OVERDUE = 'PAYMENT_OVERDUE', _('Payment Overdue')
    LOAN_COMPLETED = 'LOAN_COMPLETED', _('Loan Completed')
    CUSTOM_MESSAGE = 'CUSTOM_MESSAGE', _('Custom Message')


class WebSocketNotification(models.Model):
    """
    WebSocket notification model for real-time notifications.
    
    This model is used to store notifications that will be sent via WebSocket.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        related_name='websocket_notification',
        verbose_name=_('Notification')
    )
    type = models.CharField(
        _('Type'),
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.CUSTOM_MESSAGE
    )
    data = models.JSONField(_('Data'), default=dict, blank=True)
    is_sent = models.BooleanField(_('Is sent'), default=False)
    sent_at = models.DateTimeField(_('Sent at'), null=True, blank=True)
    
    class Meta:
        """Meta options for WebSocketNotification model."""
        verbose_name = _('websocket notification')
        verbose_name_plural = _('websocket notifications')
        ordering = ['-notification__created_at']
    
    def __str__(self):
        """Return string representation of the websocket notification."""
        return f"{self.type} - {self.notification}"
    
    def mark_as_sent(self):
        """Mark the websocket notification as sent."""
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save(update_fields=['is_sent', 'sent_at'])
        return True
