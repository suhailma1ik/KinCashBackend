from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for the Payment model."""
    list_display = ('id', 'loan', 'user', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('id', 'loan__id', 'user__email', 'user__phone_number', 'idempotency_key')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {'fields': ('loan', 'user', 'amount')}),
        (_('Status'), {'fields': ('status',)}),
        (_('Details'), {'fields': ('idempotency_key', 'created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')
