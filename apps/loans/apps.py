"""
Loans app configuration for H.E.L.P Backend.
"""
from django.apps import AppConfig


class LoansConfig(AppConfig):
    """Configuration for the loans app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.loans'
    
    def ready(self):
        """
        Import signal handlers when the app is ready.
        """
        import apps.loans.signals  # noqa
