"""
OpenAPI schema customizations for the users app.
"""
from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse

from apps.users.views import (
    SignUpView,
    LoginView,
    LogoutView,
    CustomTokenRefreshView,
    UserDetailView,
    UpdateProfileView,
    PasswordResetRequestView,
    OTPVerificationView,
    PasswordResetConfirmView,
    GoogleAuthView,
)


class SignUpViewSchema(OpenApiViewExtension):
    """Schema customization for SignUpView."""
    target_class = SignUpView
    
    def view_replacement(self):
        """Replace the view with customized schema."""
        class Extended(self.target_class):
            """Extended view with customized schema."""
            @extend_schema(
                summary="Register a new user",
                description="Creates a new user account and returns JWT tokens.",
                responses={
                    201: OpenApiResponse(
                        description="User registered successfully",
                        examples=[
                            OpenApiExample(
                                name="Successful Registration",
                                value={
                                    "status": 201,
                                    "message": "Registration successful with your email address!",
                                    "data": {
                                        "token": {
                                            "refresh": "refresh_token_string",
                                            "access": "access_token_string"
                                        },
                                        "user": {
                                            "id": "user_id",
                                            "email": "user@example.com",
                                            "phone_number": "+1234567890",
                                            "first_name": "John",
                                            "last_name": "Doe"
                                        }
                                    }
                                }
                            )
                        ]
                    ),
                    400: OpenApiResponse(
                        description="Validation error or duplicate user",
                        examples=[
                            OpenApiExample(
                                name="Email Already Registered",
                                value={
                                    "status": 400,
                                    "message": "Email is already registered.",
                                }
                            ),
                            OpenApiExample(
                                name="Validation Error",
                                value={
                                    "status": 400,
                                    "message": "Validation failed",
                                    "errors": {
                                        "email": ["Enter a valid email address."]
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


class LoginViewSchema(OpenApiViewExtension):
    """Schema customization for LoginView."""
    target_class = LoginView
    
    def view_replacement(self):
        """Replace the view with customized schema."""
        class Extended(self.target_class):
            """Extended view with customized schema."""
            @extend_schema(
                summary="User login",
                description="Authenticates a user and returns JWT tokens.",
                responses={
                    200: OpenApiResponse(
                        description="Login successful",
                        examples=[
                            OpenApiExample(
                                name="Successful Login",
                                value={
                                    "status": 200,
                                    "message": "Login successful.",
                                    "data": {
                                        "token": {
                                            "refresh": "refresh_token_string",
                                            "access": "access_token_string"
                                        },
                                        "user": {
                                            "id": "user_id",
                                            "email": "user@example.com",
                                            "phone_number": "+1234567890",
                                            "first_name": "John",
                                            "last_name": "Doe"
                                        }
                                    }
                                }
                            )
                        ]
                    ),
                    400: OpenApiResponse(
                        description="Invalid credentials",
                        examples=[
                            OpenApiExample(
                                name="Invalid Credentials",
                                value={
                                    "status": 400,
                                    "message": "Unable to log in with provided credentials."
                                }
                            )
                        ]
                    )
                }
            )
            def post(self, request, *args, **kwargs):
                return super().post(request, *args, **kwargs)
        
        return Extended


class UserDetailViewSchema(OpenApiViewExtension):
    """Schema customization for UserDetailView."""
    target_class = UserDetailView
    
    def view_replacement(self):
        """Replace the view with customized schema."""
        class Extended(self.target_class):
            """Extended view with customized schema."""
            @extend_schema(
                summary="Get user details",
                description="Retrieves user details by phone number, email, or ID.",
                parameters=[
                    OpenApiParameter(
                        name="phone_number",
                        description="User's phone number",
                        required=False,
                        type=str
                    ),
                    OpenApiParameter(
                        name="email",
                        description="User's email address",
                        required=False,
                        type=str
                    ),
                    OpenApiParameter(
                        name="id",
                        description="User's ID",
                        required=False,
                        type=str
                    )
                ],
                responses={
                    200: OpenApiResponse(
                        description="User details retrieved successfully",
                        examples=[
                            OpenApiExample(
                                name="User Details",
                                value={
                                    "status": 200,
                                    "message": "User details retrieved successfully.",
                                    "data": {
                                        "id": "user_id",
                                        "email": "user@example.com",
                                        "phone_number": "+1234567890",
                                        "first_name": "John",
                                        "last_name": "Doe",
                                        "kyc_status": "PENDING",
                                        "date_joined": "2023-01-01T00:00:00Z"
                                    }
                                }
                            )
                        ]
                    ),
                    404: OpenApiResponse(
                        description="User not found",
                        examples=[
                            OpenApiExample(
                                name="User Not Found",
                                value={
                                    "status": 404,
                                    "message": "User not found."
                                }
                            )
                        ]
                    )
                }
            )
            def get(self, request, *args, **kwargs):
                return super().get(request, *args, **kwargs)
        
        return Extended
