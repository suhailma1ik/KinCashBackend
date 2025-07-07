"""
Signal handlers for the loans app.

This module contains Django signal handlers for the loans app.
These are automatically imported when the app is ready via the AppConfig.ready() method.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.loans.models import Loan


@receiver(post_save, sender=Loan)
def loan_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Loan model post_save event.
    
    This is executed whenever a Loan instance is saved.
    
    Args:
        sender: The model class that sent the signal (Loan)
        instance: The actual Loan instance that was saved
        created: Boolean flag indicating if this is a new instance (True) or an update (False)
        **kwargs: Additional keyword arguments
    """
    # Add your signal handling logic here
    # For example, you might want to:
    # - Update loan statistics
    # - Send notifications about loan status changes
    # - Trigger payment processing
    pass  # Remove this pass statement when adding actual logic
