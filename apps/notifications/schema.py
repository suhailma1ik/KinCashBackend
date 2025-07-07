"""
OpenAPI schema customizations for the notifications app.
"""
from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse

from apps.notifications.views import (
    NotificationListView,
    UnreadNotificationListView,
    CreateNotificationView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
)


class NotificationListViewSchema(OpenApiViewExtension):
    """Schema customization for NotificationListView."""
    target_class = NotificationListView
    
    def view_replacement(self):
        """Replace the view with customized schema."""
        class Extended(self.target_class):
            """Extended view with customized schema."""
            @extend_schema(
                summary="List notifications",
                description="Returns all notifications for the authenticated user.",
                parameters=[
                    OpenApiParameter(
                        name="page",
                        description="Page number",
                        required=False,
                        type=int
                    ),
                    OpenApiParameter(
                        name="page_size",
                        description="Number of items per page",
                        required=False,
                        type=int
                    )
                ],
                responses={
                    200: OpenApiResponse(
                        description="Notifications retrieved successfully",
                        examples=[
                            OpenApiExample(
                                name="Notification List",
                                value={
                                    "status": 200,
                                    "message": "Notifications retrieved successfully.",
                                    "data": [
                                        {
                                            "id": "notification_id",
                                            "loan": "loan_id",
                                            "sender": {
                                                "id": "sender_id",
                                                "email": "sender@example.com",
                                                "phone_number": "+1234567890",
                                                "first_name": "Sender",
                                                "last_name": "User"
                                            },
                                            "recipient": {
                                                "id": "recipient_id",
                                                "email": "recipient@example.com",
                                                "phone_number": "+0987654321",
                                                "first_name": "Recipient",
                                                "last_name": "User"
                                            },
                                            "title": "Payment Due",
                                            "body": "Your payment is due on 2023-02-01.",
                                            "is_read": False,
                                            "created_at": "2023-01-25T00:00:00Z"
                                        }
                                    ]
                                }
                            )
                        ]
                    )
                }
            )
            def get(self, request, *args, **kwargs):
                return super().get(request, *args, **kwargs)
        
        return Extended


class UnreadNotificationListViewSchema(OpenApiViewExtension):
    """Schema customization for UnreadNotificationListView."""
    target_class = UnreadNotificationListView
    
    def view_replacement(self):
        """Replace the view with customized schema."""
        class Extended(self.target_class):
            """Extended view with customized schema."""
            @extend_schema(
                summary="List unread notifications",
                description="Returns all unread notifications for the authenticated user.",
                parameters=[
                    OpenApiParameter(
                        name="page",
                        description="Page number",
                        required=False,
                        type=int
                    ),
                    OpenApiParameter(
                        name="page_size",
                        description="Number of items per page",
                        required=False,
                        type=int
                    )
                ],
                responses={
                    200: OpenApiResponse(
                        description="Unread notifications retrieved successfully",
                        examples=[
                            OpenApiExample(
                                name="Unread Notification List",
                                value={
                                    "status": 200,
                                    "message": "Notifications retrieved successfully.",
                                    "data": [
                                        {
                                            "id": "notification_id",
                                            "loan": "loan_id",
                                            "sender": {
                                                "id": "sender_id",
                                                "email": "sender@example.com",
                                                "phone_number": "+1234567890",
                                                "first_name": "Sender",
                                                "last_name": "User"
                                            },
                                            "recipient": {
                                                "id": "recipient_id",
                                                "email": "recipient@example.com",
                                                "phone_number": "+0987654321",
                                                "first_name": "Recipient",
                                                "last_name": "User"
                                            },
                                            "title": "Payment Due",
                                            "body": "Your payment is due on 2023-02-01.",
                                            "is_read": False,
                                            "created_at": "2023-01-25T00:00:00Z"
                                        }
                                    ]
                                }
                            )
                        ]
                    )
                }
            )
            def get(self, request, *args, **kwargs):
                return super().get(request, *args, **kwargs)
        
        return Extended


class CreateNotificationViewSchema(OpenApiViewExtension):
    """Schema customization for CreateNotificationView."""
    target_class = CreateNotificationView
    
    def view_replacement(self):
        """Replace the view with customized schema."""
        class Extended(self.target_class):
            """Extended view with customized schema."""
            @extend_schema(
                summary="Create notification",
                description="Creates a new notification for a recipient.",
                responses={
                    201: OpenApiResponse(
                        description="Notification created successfully",
                        examples=[
                            OpenApiExample(
                                name="Notification Creation",
                                value={
                                    "status": 201,
                                    "message": "Notification created successfully.",
                                    "data": {
                                        "id": "notification_id",
                                        "loan": "loan_id",
                                        "sender": {
                                            "id": "sender_id",
                                            "email": "sender@example.com",
                                            "phone_number": "+1234567890",
                                            "first_name": "Sender",
                                            "last_name": "User"
                                        },
                                        "recipient": {
                                            "id": "recipient_id",
                                            "email": "recipient@example.com",
                                            "phone_number": "+0987654321",
                                            "first_name": "Recipient",
                                            "last_name": "User"
                                        },
                                        "title": "Payment Reminder",
                                        "body": "Please remember to pay your EMI.",
                                        "is_read": False,
                                        "created_at": "2023-01-25T00:00:00Z"
                                    }
                                }
                            )
                        ]
                    ),
                    400: OpenApiResponse(
                        description="Validation error",
                        examples=[
                            OpenApiExample(
                                name="Validation Error",
                                value={
                                    "status": 400,
                                    "message": "Validation failed",
                                    "errors": {
                                        "recipient_id": ["This field is required."]
                                    }
                                }
                            )
                        ]
                    )
                }
            )
            def post(self, request, *args, **kwargs):
                return super().post(request, *args, **kwargs)
        
        return Extended


class MarkNotificationReadViewSchema(OpenApiViewExtension):
    """Schema customization for MarkNotificationReadView."""
    target_class = MarkNotificationReadView
    
    def view_replacement(self):
        """Replace the view with customized schema."""
        class Extended(self.target_class):
            """Extended view with customized schema."""
            @extend_schema(
                summary="Mark notification as read",
                description="Marks a specific notification as read.",
                responses={
                    200: OpenApiResponse(
                        description="Notification marked as read",
                        examples=[
                            OpenApiExample(
                                name="Mark as Read",
                                value={
                                    "status": 200,
                                    "message": "Notification marked as read.",
                                    "data": {
                                        "id": "notification_id",
                                        "loan": "loan_id",
                                        "sender": {
                                            "id": "sender_id",
                                            "email": "sender@example.com",
                                            "phone_number": "+1234567890",
                                            "first_name": "Sender",
                                            "last_name": "User"
                                        },
                                        "recipient": {
                                            "id": "recipient_id",
                                            "email": "recipient@example.com",
                                            "phone_number": "+0987654321",
                                            "first_name": "Recipient",
                                            "last_name": "User"
                                        },
                                        "title": "Payment Due",
                                        "body": "Your payment is due on 2023-02-01.",
                                        "is_read": True,
                                        "created_at": "2023-01-25T00:00:00Z"
                                    }
                                }
                            )
                        ]
                    ),
                    404: OpenApiResponse(
                        description="Notification not found",
                        examples=[
                            OpenApiExample(
                                name="Notification Not Found",
                                value={
                                    "status": 404,
                                    "message": "Notification not found."
                                }
                            )
                        ]
                    )
                }
            )
            def post(self, request, *args, **kwargs):
                return super().post(request, *args, **kwargs)
        
        return Extended


class MarkAllNotificationsReadViewSchema(OpenApiViewExtension):
    """Schema customization for MarkAllNotificationsReadView."""
    target_class = MarkAllNotificationsReadView
    
    def view_replacement(self):
        """Replace the view with customized schema."""
        class Extended(self.target_class):
            """Extended view with customized schema."""
            @extend_schema(
                summary="Mark all notifications as read",
                description="Marks all notifications for the authenticated user as read.",
                responses={
                    200: OpenApiResponse(
                        description="All notifications marked as read",
                        examples=[
                            OpenApiExample(
                                name="Mark All as Read",
                                value={
                                    "status": 200,
                                    "message": "All notifications marked as read.",
                                    "data": {
                                        "count": 5
                                    }
                                }
                            )
                        ]
                    )
                }
            )
            def post(self, request, *args, **kwargs):
                return super().post(request, *args, **kwargs)
        
        return Extended
