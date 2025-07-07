"""
Payments app configuration for H.E.L.P Backend.
"""
from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    """Configuration for the payments app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payments'
    
    def ready(self):
        """
        Import signal handlers when the app is ready.
        """
        import apps.payments.signals  # noqa
