"""
Models for the payments app.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.models import User
from apps.loans.models import Loan


class PaymentStatus(models.TextChoices):
    """Payment status choices."""
    PENDING = "PENDING", _("Pending")
    COMPLETED = "COMPLETED", _("Completed")
    FAILED = "FAILED", _("Failed")


class Payment(models.Model):
    """
    Model representing a payment in the system.
    """
    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name="payments",
        help_text=_("The loan this payment is associated with")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments",
        help_text=_("The user who made the payment")
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Payment amount")
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        help_text=_("Current status of the payment")
    )
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("Unique key to ensure payment is processed only once")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """Meta options for the Payment model."""
        ordering = ['-created_at']
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
    
    def __str__(self):
        """Return a string representation of the payment."""
        return f"Payment {self.id} - {self.amount} - {self.status}"
