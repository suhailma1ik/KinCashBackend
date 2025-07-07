from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Notification, WebSocketNotification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for the Notification model."""
    list_display = ('id', 'sender', 'recipient', 'title', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('id', 'sender__email', 'recipient__email', 'title', 'body')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {'fields': ('loan', 'sender', 'recipient')}),
        (_('Content'), {'fields': ('title', 'body')}),
        (_('Status'), {'fields': ('is_read', 'created_at')}),
    )
    
    readonly_fields = ('created_at',)


@admin.register(WebSocketNotification)
class WebSocketNotificationAdmin(admin.ModelAdmin):
    """Admin configuration for the WebSocketNotification model."""
    list_display = ('id', 'notification', 'type', 'is_sent', 'sent_at')
    list_filter = ('type', 'is_sent')
    search_fields = ('id', 'notification__title', 'notification__body')
    
    fieldsets = (
        (None, {'fields': ('notification', 'type')}),
        (_('Data'), {'fields': ('data',)}),
        (_('Status'), {'fields': ('is_sent', 'sent_at')}),
    )
    
    readonly_fields = ('sent_at',)
