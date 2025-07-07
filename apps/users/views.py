"""
Views for the users app.
"""
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.models import User
from apps.users.serializers import (
    RegistrationSerializer,
    UserSerializer,
    LoginSerializer,
    UpdateProfileSerializer,
    PasswordResetRequestSerializer,
    OTPVerificationSerializer,
    PasswordResetConfirmSerializer,
)
from apps.users.services import OTPService
from google.oauth2 import id_token
from google.auth.transport import requests


class SignUpView(generics.CreateAPIView):
    """
    API view for user registration.
    
    Creates a new user and returns JWT tokens.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new user and return JWT tokens."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Determine which identifier was used for registration
        if user.email:
            msg = _("Registration successful with your email address!")
        elif user.phone_number:
            msg = _("Registration successful with your phone number!")
        else:
            msg = _("Registration successful!")
        
        return Response({
            "status": status.HTTP_201_CREATED,
            "message": msg,
            "data": {
                "token": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "user": UserSerializer(user).data,
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """
    API view for user login.
    
    Authenticates a user and returns JWT tokens.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request, *args, **kwargs):
        """Authenticate a user and return JWT tokens."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            user = serializer.validated_data['user']
            
            return Response({
                "status": "success",
                "message": _("Login successful."),
                "data": {
                    "token": {
                        "refresh": serializer.validated_data['refresh'],
                        "access": serializer.validated_data['access'],
                    },
                    "user": UserSerializer(user).data,
                }
            })
        except Exception as e:
            import logging
            logger = logging.getLogger('django')
            logger.error(f"Login error: {str(e)}")
            
            return Response({
                "status": "error",
                "message": _("Login failed."),
                "errors": {"detail": str(e)}
            }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    API view for user logout.
    
    Blacklists the refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Blacklist the refresh token."""
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    "status": "error",
                    "message": _("Refresh token is required."),
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Log the token for debugging
            import logging
            logger = logging.getLogger('django')
            logger.debug(f"Attempting to blacklist token: {refresh_token[:10]}...")
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Clear any session data if using session authentication
            if hasattr(request, 'session'):
                request.session.flush()
                
            return Response({
                "status": "success",
                "message": _("Logout successful."),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logger = logging.getLogger('django')
            logger.error(f"Logout error: {str(e)}")
            
            return Response({
                "status": "error",
                "message": _("Invalid token or token already blacklisted."),
                "detail": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenRefreshView(TokenRefreshView):
    """
    API view for refreshing JWT tokens.
    
    Returns a new access token.
    """
    def post(self, request, *args, **kwargs):
        """Refresh the access token."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": _("Token refreshed."),
            "data": serializer.validated_data
        })


class UserDetailView(generics.RetrieveAPIView):
    """
    API view for retrieving user details.
    
    Returns the authenticated user's details or a specified user's details.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        """Get the user object."""
        phone_number = self.request.query_params.get('phone_number')
        email = self.request.query_params.get('email')
        user_id = self.request.query_params.get('id')
        
        if not phone_number and not email and not user_id:
            return self.request.user
        
        if phone_number:
            return get_object_or_404(User, phone_number=phone_number)
        elif email:
            return get_object_or_404(User, email=email)
        elif user_id:
            return get_object_or_404(User, id=user_id)


class UpdateProfileView(generics.UpdateAPIView):
    """
    API view for updating user profile.
    
    Updates the authenticated user's profile information.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UpdateProfileSerializer
    
    def get_object(self):
        """Get the authenticated user."""
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        """Update the user profile."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": _("Profile updated successfully."),
            "data": UserSerializer(instance).data
        })


class PasswordResetRequestView(generics.GenericAPIView):
    """
    API view for requesting a password reset.
    
    Sends an OTP to the user's email or phone number.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetRequestSerializer
    
    def post(self, request, *args, **kwargs):
        """Send an OTP to the user's email or phone number."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get('email')
        phone_number = serializer.validated_data.get('phone_number')
        
        try:
            if email:
                user = User.objects.get(email=email)
                OTPService.send_otp_email(user)
            elif phone_number:
                user = User.objects.get(phone_number=phone_number)
                OTPService.send_otp_sms(user)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": _("OTP sent successfully."),
            })
        except User.DoesNotExist:
            # For security reasons, don't reveal that the user doesn't exist
            return Response({
                "status": status.HTTP_200_OK,
                "message": _("If the account exists, an OTP has been sent."),
            })


class OTPVerificationView(generics.GenericAPIView):
    """
    API view for verifying an OTP.
    
    Verifies the OTP sent to the user's email or phone number.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = OTPVerificationSerializer
    
    def post(self, request, *args, **kwargs):
        """Verify the OTP."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get('email')
        phone_number = serializer.validated_data.get('phone_number')
        otp = serializer.validated_data.get('otp')
        
        try:
            if email:
                user = User.objects.get(email=email)
            elif phone_number:
                user = User.objects.get(phone_number=phone_number)
            
            if OTPService.verify_otp(user, otp):
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": _("OTP verified successfully."),
                })
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": _("Invalid or expired OTP."),
                }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": _("User not found."),
            }, status=status.HTTP_404_NOT_FOUND)


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    API view for confirming a password reset.
    
    Verifies the OTP and resets the user's password.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer
    
    def post(self, request, *args, **kwargs):
        """Verify the OTP and reset the user's password."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get('email')
        phone_number = serializer.validated_data.get('phone_number')
        otp = serializer.validated_data.get('otp')
        new_password = serializer.validated_data.get('new_password')
        
        try:
            if email:
                user = User.objects.get(email=email)
            elif phone_number:
                user = User.objects.get(phone_number=phone_number)
            
            if OTPService.verify_otp(user, otp):
                user.set_password(new_password)
                user.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": _("Password reset successfully."),
                })
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": _("Invalid or expired OTP."),
                }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": _("User not found."),
            }, status=status.HTTP_404_NOT_FOUND)


class GoogleAuthView(generics.GenericAPIView):
    """
    API view for Google authentication.
    
    Authenticates a user with Google OAuth and returns JWT tokens.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Authenticate a user with Google OAuth."""
        token = request.data.get('credential')
        if not token:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": _('Google credential is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request())
            if idinfo.get('iss') not in ("accounts.google.com", "https://accounts.google.com"):
                raise ValueError("Invalid token issuer.")
        except ValueError as exc:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": str(exc),
            }, status=status.HTTP_400_BAD_REQUEST)
        email = idinfo.get("email")
        first_name = idinfo.get("given_name", "")
        last_name = idinfo.get("family_name", "")
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"first_name": first_name, "last_name": last_name}
        )
        picture = idinfo.get("picture")
        if hasattr(user, "profile_picture") and picture and created:
            user.profile_picture = picture
            user.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "status": status.HTTP_200_OK,
            "message": _('Google authentication successful.'),
            "data": {
                "token": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "user": UserSerializer(user).data,
            }
        }, status=status.HTTP_200_OK)


class GetUserByPhoneView(APIView):
    """
    API view for retrieving user details by phone number.
    
    Returns user details if a user with the provided phone number exists.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Retrieve user details by phone number."""
        phone = request.query_params.get('phone')
        
        if not phone:
            return Response({
                "status": "error",
                "message": _("Phone number is required."),
                "errors": {"phone": [_("This field is required.")]}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(phone_number=phone)
            serializer = UserSerializer(user)
            return Response({
                "status": "success",
                "message": _("User details retrieved successfully."),
                "data": serializer.data
            })
        except User.DoesNotExist:
            return Response({
                "status": "error",
                "message": _("User not found."),
                "errors": {"phone": [_("No user found with this phone number.")]}
            }, status=status.HTTP_404_NOT_FOUND)
