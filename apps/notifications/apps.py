"""
Notifications app configuration for H.E.L.P Backend.
"""
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Configuration for the notifications app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    
    def ready(self):
        """
        Import signal handlers when the app is ready.
        """
        import apps.notifications.signals  # noqa
