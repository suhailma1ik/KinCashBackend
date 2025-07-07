"""
Signal handlers for the users app.

This module contains Django signal handlers for the users app.
These are automatically imported when the app is ready via the AppConfig.ready() method.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.users.models import User


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for User model post_save event.
    
    This is executed whenever a User instance is saved.
    
    Args:
        sender: The model class that sent the signal (User)
        instance: The actual User instance that was saved
        created: Boolean flag indicating if this is a new instance (True) or an update (False)
        **kwargs: Additional keyword arguments
    """
    # Add your signal handling logic here
    # For example, you might want to:
    # - Create a profile for new users
    # - Send welcome emails
    # - Set up default settings
    # - Trigger notifications
    pass  # Remove this pass statement when adding actual logic
