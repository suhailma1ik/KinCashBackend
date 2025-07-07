"""
Services for the notifications app.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.notifications.models import (
    Notification,
    WebSocketNotification,
    NotificationType,
)


class NotificationService:
    """Service for creating and sending notifications."""
    
    @staticmethod
    def create_notification(sender, recipient, title, body, loan=None, notification_type=None, data=None):
        """
        Create a notification and optionally send it via WebSocket.
        
        Args:
            sender: The user sending the notification.
            recipient: The user receiving the notification.
            title: The notification title.
            body: The notification body.
            loan: Optional loan related to the notification.
            notification_type: Optional notification type for WebSocket.
            data: Optional data for WebSocket notification.
        
        Returns:
            The created notification.
        """
        # Create the notification
        notification = Notification.objects.create(
            sender=sender,
            recipient=recipient,
            title=title,
            body=body,
            loan=loan
        )
        
        # Create WebSocket notification if type is provided
        if notification_type:
            ws_notification = WebSocketNotification.objects.create(
                notification=notification,
                type=notification_type,
                data=data or {}
            )
            
            # Send the notification via WebSocket
            NotificationService.send_websocket_notification(notification, ws_notification)
        
        return notification
    
    @staticmethod
    def send_websocket_notification(notification, ws_notification):
        """
        Send a notification via WebSocket.
        
        Args:
            notification: The notification to send.
            ws_notification: The WebSocket notification with type and data.
        
        Returns:
            Boolean indicating whether the notification was sent.
        """
        channel_layer = get_channel_layer()
        
        if not channel_layer:
            return False
        
        # Create the message to send
        message = {
            'type': 'notification_message',
            'message': {
                'type': ws_notification.type,
                'notification_id': str(notification.id),
                'title': notification.title,
                'body': notification.body,
                'created_at': notification.created_at.isoformat(),
                'is_read': notification.is_read,
                'data': ws_notification.data
            },
            'notification_id': str(notification.id)
        }
        
        # Send to the user's group
        try:
            async_to_sync(channel_layer.group_send)(
                f"user_{notification.recipient.id}",
                message
            )
            return True
        except Exception:
            return False
    
    @staticmethod
    def send_email_notification(notification):
        """
        Send a notification via email.
        
        Args:
            notification: The notification to send.
        
        Returns:
            Boolean indicating whether the email was sent.
        """
        if not notification.recipient.email:
            return False
        
        try:
            send_mail(
                subject=notification.title,
                message=notification.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.recipient.email],
                fail_silently=False,
            )
            return True
        except Exception:
            return False
    
    @staticmethod
    def send_sms_notification(notification):
        """
        Send a notification via SMS.
        
        Args:
            notification: The notification to send.
        
        Returns:
            Boolean indicating whether the SMS was sent.
        """
        if not notification.recipient.phone_number:
            return False
        
        # In a real implementation, you would integrate with an SMS gateway
        # For now, we'll just print the SMS to the console
        print(f"SMS to {notification.recipient.phone_number}: {notification.title} - {notification.body}")
        
        # Always return True for now since we're not actually sending SMS
        return True
    
    @staticmethod
    def create_loan_created_notification(loan):
        """
        Create a notification for when a loan is created.
        
        Args:
            loan: The loan that was created.
        
        Returns:
            The created notification.
        """
        # Notify the borrower
        title = _("New Loan Request")
        body = _(f"You have received a loan request from {loan.lender.get_full_name()} for {loan.principal_amount}.")
        
        return NotificationService.create_notification(
            sender=loan.lender,
            recipient=loan.borrower,
            title=title,
            body=body,
            loan=loan,
            notification_type=NotificationType.LOAN_CREATED,
            data={
                'loan_id': str(loan.id),
                'amount': str(loan.principal_amount),
                'lender_id': str(loan.lender.id),
                'lender_name': loan.lender.get_full_name()
            }
        )
    
    @staticmethod
    def create_loan_accepted_notification(loan):
        """
        Create a notification for when a loan is accepted.
        
        Args:
            loan: The loan that was accepted.
        
        Returns:
            The created notification.
        """
        # Notify the lender
        title = _("Loan Accepted")
        body = _(f"{loan.borrower.get_full_name()} has accepted your loan request for {loan.principal_amount}.")
        
        return NotificationService.create_notification(
            sender=loan.borrower,
            recipient=loan.lender,
            title=title,
            body=body,
            loan=loan,
            notification_type=NotificationType.LOAN_ACCEPTED,
            data={
                'loan_id': str(loan.id),
                'amount': str(loan.principal_amount),
                'borrower_id': str(loan.borrower.id),
                'borrower_name': loan.borrower.get_full_name()
            }
        )
    
    @staticmethod
    def create_payment_received_notification(payment):
        """
        Create a notification for when a payment is received.
        
        Args:
            payment: The payment that was received.
        
        Returns:
            The created notification.
        """
        loan = payment.loan
        
        # Notify the lender
        title = _("Payment Received")
        body = _(f"You have received a payment of {payment.amount} from {payment.payer.get_full_name()}.")
        
        return NotificationService.create_notification(
            sender=payment.payer,
            recipient=loan.lender,
            title=title,
            body=body,
            loan=loan,
            notification_type=NotificationType.PAYMENT_RECEIVED,
            data={
                'loan_id': str(loan.id),
                'payment_id': str(payment.id),
                'amount': str(payment.amount),
                'payer_id': str(payment.payer.id),
                'payer_name': payment.payer.get_full_name()
            }
        )
    
    @staticmethod
    def create_payment_due_notification(schedule):
        """
        Create a notification for when a payment is due.
        
        Args:
            schedule: The repayment schedule that is due.
        
        Returns:
            The created notification.
        """
        loan = schedule.loan
        
        # Notify the borrower
        title = _("Payment Due")
        body = _(f"Your payment of {schedule.amount_due} is due on {schedule.due_date}.")
        
        return NotificationService.create_notification(
            sender=loan.lender,
            recipient=loan.borrower,
            title=title,
            body=body,
            loan=loan,
            notification_type=NotificationType.PAYMENT_DUE,
            data={
                'loan_id': str(loan.id),
                'schedule_id': schedule.id,
                'amount': str(schedule.amount_due),
                'due_date': schedule.due_date.isoformat()
            }
        )
    
    @staticmethod
    def create_payment_overdue_notification(schedule):
        """
        Create a notification for when a payment is overdue.
        
        Args:
            schedule: The repayment schedule that is overdue.
        
        Returns:
            The created notification.
        """
        loan = schedule.loan
        
        # Notify the borrower
        title = _("Payment Overdue")
        body = _(f"Your payment of {schedule.amount_due} was due on {schedule.due_date} and is now overdue.")
        
        return NotificationService.create_notification(
            sender=loan.lender,
            recipient=loan.borrower,
            title=title,
            body=body,
            loan=loan,
            notification_type=NotificationType.PAYMENT_OVERDUE,
            data={
                'loan_id': str(loan.id),
                'schedule_id': schedule.id,
                'amount': str(schedule.amount_due),
                'due_date': schedule.due_date.isoformat()
            }
        )
    
    @staticmethod
    def create_loan_completed_notification(loan):
        """
        Create a notification for when a loan is completed.
        
        Args:
            loan: The loan that was completed.
        
        Returns:
            The created notification.
        """
        # Notify both lender and borrower
        title = _("Loan Completed")
        lender_body = _(f"Your loan to {loan.borrower.get_full_name()} for {loan.principal_amount} has been fully repaid.")
        borrower_body = _(f"You have fully repaid your loan from {loan.lender.get_full_name()} for {loan.principal_amount}.")
        
        # Create notifications
        lender_notification = NotificationService.create_notification(
            sender=loan.borrower,
            recipient=loan.lender,
            title=title,
            body=lender_body,
            loan=loan,
            notification_type=NotificationType.LOAN_COMPLETED,
            data={
                'loan_id': str(loan.id),
                'amount': str(loan.principal_amount),
                'borrower_id': str(loan.borrower.id),
                'borrower_name': loan.borrower.get_full_name()
            }
        )
        
        borrower_notification = NotificationService.create_notification(
            sender=loan.lender,
            recipient=loan.borrower,
            title=title,
            body=borrower_body,
            loan=loan,
            notification_type=NotificationType.LOAN_COMPLETED,
            data={
                'loan_id': str(loan.id),
                'amount': str(loan.principal_amount),
                'lender_id': str(loan.lender.id),
                'lender_name': loan.lender.get_full_name()
            }
        )
        
        return lender_notification, borrower_notification
