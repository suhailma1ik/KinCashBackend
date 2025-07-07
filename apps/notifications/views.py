"""
Views for the notifications app.
"""
from django.utils.translation import gettext_lazy as _
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.notifications.models import Notification
from apps.notifications.serializers import (
    NotificationSerializer,
    NotificationCreateSerializer,
    MarkNotificationReadSerializer,
)


class NotificationListView(generics.ListAPIView):
    """
    API view for listing notifications.
    
    Returns all notifications for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        """Get notifications for the authenticated user."""
        return Notification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """List notifications for the authenticated user."""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                "status": status.HTTP_200_OK,
                "message": _("Notifications retrieved successfully."),
                "data": serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": _("Notifications retrieved successfully."),
            "data": serializer.data
        })


class UnreadNotificationListView(NotificationListView):
    """
    API view for listing unread notifications.
    
    Returns all unread notifications for the authenticated user.
    """
    
    def get_queryset(self):
        """Get unread notifications for the authenticated user."""
        return Notification.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).order_by('-created_at')


class CreateNotificationView(generics.CreateAPIView):
    """
    API view for creating a notification.
    
    Creates a new notification for a recipient.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationCreateSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new notification."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.save()
        
        return Response({
            "status": status.HTTP_201_CREATED,
            "message": _("Notification created successfully."),
            "data": NotificationSerializer(notification).data
        }, status=status.HTTP_201_CREATED)


class MarkNotificationReadView(APIView):
    """
    API view for marking a notification as read.
    
    Marks a specific notification as read.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Mark a notification as read."""
        serializer = MarkNotificationReadSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        notification = serializer.validated_data['notification']
        notification.mark_as_read()
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": _("Notification marked as read."),
            "data": NotificationSerializer(notification).data
        })


class MarkAllNotificationsReadView(APIView):
    """
    API view for marking all notifications as read.
    
    Marks all notifications for the authenticated user as read.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Mark all notifications as read."""
        notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        )
        
        count = notifications.count()
        notifications.update(is_read=True)
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": _("All notifications marked as read."),
            "data": {
                "count": count
            }
        })
