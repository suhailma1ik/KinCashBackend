"""
URL patterns for the users app.
"""
from django.urls import path

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
    GetUserByPhoneView,
)

urlpatterns = [
    # Authentication endpoints
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('google-auth/', GoogleAuthView.as_view(), name='google_auth'),
    
    # User profile endpoints
    path('get-user/', UserDetailView.as_view(), name='get_user'),
    path('update_profile/', UpdateProfileView.as_view(), name='update_profile'),
    
    # Password reset and OTP verification endpoints
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('verify-otp/', OTPVerificationView.as_view(), name='verify_otp'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # User lookup endpoint
    path('get-user-details/', GetUserByPhoneView.as_view(), name='get_user_by_phone'),
]
