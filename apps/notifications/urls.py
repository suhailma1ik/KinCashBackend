"""
URL patterns for the notifications app.
"""
from django.urls import path

from apps.notifications.views import (
    NotificationListView,
    UnreadNotificationListView,
    CreateNotificationView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
)

urlpatterns = [
    # Notification endpoints
    path('list/', NotificationListView.as_view(), name='notification_list'),
    path('unread/', UnreadNotificationListView.as_view(), name='unread_notification_list'),
    path('create/', CreateNotificationView.as_view(), name='create_notification'),
    path('mark_read/', MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('mark_all_read/', MarkAllNotificationsReadView.as_view(), name='mark_all_notifications_read'),
]
