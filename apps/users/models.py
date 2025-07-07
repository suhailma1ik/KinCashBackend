"""
User models for H.E.L.P Backend.
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.users.managers import UserManager


class KYCStatus(models.TextChoices):
    """KYC status choices for User model."""
    PENDING = 'PENDING', _('Pending')
    VERIFIED = 'VERIFIED', _('Verified')
    REJECTED = 'REJECTED', _('Rejected')


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for H.E.L.P Backend.
    
    Uses email and phone as unique identifiers and includes KYC status.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    email = models.EmailField(
        _('Email address'),
        unique=True,
        error_messages={
            'unique': _('A user with that email already exists.'),
        }
    )
    phone_number = models.CharField(
        _('Phone number'),
        max_length=20,
        unique=True,
        error_messages={
            'unique': _('A user with that phone number already exists.'),
        }
    )
    first_name = models.CharField(_('First name'), max_length=150, blank=True)
    last_name = models.CharField(_('Last name'), max_length=150, blank=True)
    
    kyc_status = models.CharField(
        _('KYC status'),
        max_length=20,
        choices=KYCStatus.choices,
        default=KYCStatus.PENDING
    )
    
    is_staff = models.BooleanField(
        _('Staff status'),
        default=False,
        help_text=_('Designates whether the user can log into the admin site.'),
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('Date joined'), default=timezone.now)
    
    # Fields for soft deletion
    is_deleted = models.BooleanField(_('Deleted'), default=False)
    deleted_at = models.DateTimeField(_('Deleted at'), null=True, blank=True)
    
    objects = UserManager()
    
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']
    
    class Meta:
        """Meta options for User model."""
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
    
    def __str__(self):
        """Return string representation of the user."""
        return self.get_full_name() or self.email or self.phone_number
    
    def get_full_name(self):
        """Return the full name of the user."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name
    
    def get_short_name(self):
        """Return the short name of the user."""
        return self.first_name
    
    def soft_delete(self):
        """Soft delete the user."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['is_deleted', 'deleted_at', 'is_active'])
