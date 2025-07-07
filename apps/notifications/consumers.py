"""
WebSocket consumers for the notifications app.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

from apps.notifications.models import Notification, WebSocketNotification


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time notifications.
    """
    
    async def connect(self):
        """
        Connect to the WebSocket and add the user to the notification group.
        """
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            # Reject the connection if the user is not authenticated
            await self.close()
            return
        
        # Create a unique group name for this user
        self.group_name = f"user_{self.user.id}"
        
        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send any unsent notifications
        await self.send_unsent_notifications()
    
    async def disconnect(self, close_code):
        """
        Disconnect from the WebSocket and remove the user from the notification group.
        """
        if hasattr(self, 'group_name'):
            # Leave the group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'mark_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    await self.mark_notification_read(notification_id)
            
            elif action == 'get_unread':
                await self.send_unread_notifications()
        
        except json.JSONDecodeError:
            # Ignore invalid JSON
            pass
    
    async def notification_message(self, event):
        """
        Receive notification message from group and send to WebSocket.
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event['message']))
        
        # Mark the notification as sent
        if 'notification_id' in event:
            await self.mark_notification_sent(event['notification_id'])
    
    @database_sync_to_async
    def get_unsent_notifications(self):
        """
        Get all unsent WebSocket notifications for the user.
        """
        return list(WebSocketNotification.objects.filter(
            notification__recipient=self.user,
            is_sent=False
        ).select_related('notification').values(
            'id',
            'notification_id',
            'type',
            'data',
            'notification__title',
            'notification__body',
            'notification__created_at',
            'notification__is_read'
        ))
    
    @database_sync_to_async
    def get_unread_notifications(self):
        """
        Get all unread notifications for the user.
        """
        return list(Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).values(
            'id',
            'title',
            'body',
            'created_at',
            'is_read',
            'loan_id',
            'sender_id'
        ))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """
        Mark a notification as read.
        """
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_notification_sent(self, notification_id):
        """
        Mark a WebSocket notification as sent.
        """
        try:
            ws_notification = WebSocketNotification.objects.get(
                notification_id=notification_id
            )
            ws_notification.mark_as_sent()
            return True
        except WebSocketNotification.DoesNotExist:
            return False
    
    async def send_unsent_notifications(self):
        """
        Send all unsent notifications to the user.
        """
        unsent_notifications = await self.get_unsent_notifications()
        
        for notification in unsent_notifications:
            message = {
                'type': notification['type'],
                'notification_id': str(notification['notification_id']),
                'title': notification['notification__title'],
                'body': notification['notification__body'],
                'created_at': notification['notification__created_at'].isoformat(),
                'is_read': notification['notification__is_read'],
                'data': notification['data']
            }
            
            await self.send(text_data=json.dumps(message))
            
            # Mark the notification as sent
            await self.mark_notification_sent(notification['notification_id'])
    
    async def send_unread_notifications(self):
        """
        Send all unread notifications to the user.
        """
        unread_notifications = await self.get_unread_notifications()
        
        message = {
            'type': 'unread_notifications',
            'notifications': [
                {
                    'id': str(notification['id']),
                    'title': notification['title'],
                    'body': notification['body'],
                    'created_at': notification['created_at'].isoformat(),
                    'is_read': notification['is_read'],
                    'loan_id': str(notification['loan_id']) if notification['loan_id'] else None,
                    'sender_id': str(notification['sender_id'])
                }
                for notification in unread_notifications
            ]
        }
        
        await self.send(text_data=json.dumps(message))
