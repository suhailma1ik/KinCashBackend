"""
Serializers for the users app.
"""
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        """Meta options for RegistrationSerializer."""
        model = User
        fields = ['id', 'email', 'phone_number', 'password', 'first_name', 'last_name']
        extra_kwargs = {
            'id': {'read_only': True},
        }
    
    def create(self, validated_data):
        """Create and return a new user."""
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        """Meta options for UserSerializer."""
        model = User
        fields = ['id', 'email', 'phone_number', 'first_name', 'last_name', 'kyc_status', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'kyc_status']


class LoginSerializer(serializers.Serializer):
    """Serializer for user login.
    
    Accepts a single identifier field that can be either email or phone number,
    along with a required password field.
    """
    identifier = serializers.CharField(
        required=True,
        help_text=_('Email address or phone number')
    )
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate login credentials."""
        identifier = attrs.get('identifier')
        password = attrs.get('password')
        
        if not identifier:
            raise serializers.ValidationError(
                _('Email or phone number is required.')
            )
        
        # Determine if the identifier is an email or phone number
        import re
        email_pattern = re.compile(r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$')
        is_email = bool(email_pattern.match(identifier))
        
        email = identifier if is_email else None
        phone_number = None if is_email else identifier
        
        # For debugging purposes
        import logging
        logger = logging.getLogger('django')
        logger.debug(f"Login attempt with {'email' if is_email else 'phone number'}: {identifier}")
        
        try:
            # Try to authenticate with either email or phone number
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                phone_number=phone_number,
                password=password
            )
            
            if not user:
                # If authentication failed, check if user exists to provide better error message
                if is_email:
                    user_exists = User.objects.filter(email=email).exists()
                    if not user_exists:
                        raise serializers.ValidationError(_('No user found with this email.'))
                else:
                    user_exists = User.objects.filter(phone_number=phone_number).exists()
                    if not user_exists:
                        raise serializers.ValidationError(_('No user found with this phone number.'))
                    
                # User exists but password is wrong
                raise serializers.ValidationError(_('Invalid password.'))
                
        except Exception as e:
            if isinstance(e, serializers.ValidationError):
                raise
            logger.error(f"Authentication error: {str(e)}")
            raise serializers.ValidationError(_('Authentication error occurred.'))
        
        if not user.is_active:
            raise serializers.ValidationError(
                _('User account is disabled.')
            )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return {
            'user': user,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class TokenRefreshSerializer(serializers.Serializer):
    """Serializer for token refresh."""
    refresh = serializers.CharField()
    
    def validate(self, attrs):
        """Validate refresh token."""
        try:
            refresh = RefreshToken(attrs['refresh'])
            return {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        except Exception as e:
            raise serializers.ValidationError(
                _('Invalid or expired refresh token.')
            )


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        """Meta options for UpdateProfileSerializer."""
        model = User
        fields = ['email', 'phone_number', 'first_name', 'last_name']
        extra_kwargs = {
            'email': {'required': False},
            'phone_number': {'required': False},
        }
    
    def validate_email(self, value):
        """Validate email is unique."""
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError(_('This email is already in use.'))
        return value
    
    def validate_phone_number(self, value):
        """Validate phone number is unique."""
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(phone_number=value).exists():
            raise serializers.ValidationError(_('This phone number is already in use.'))
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    
    def validate(self, attrs):
        """Validate that either email or phone number is provided."""
        email = attrs.get('email')
        phone_number = attrs.get('phone_number')
        
        if not email and not phone_number:
            raise serializers.ValidationError(
                _('Either email or phone number is required.')
            )
        
        return attrs


class OTPVerificationSerializer(serializers.Serializer):
    """Serializer for OTP verification."""
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    otp = serializers.CharField(max_length=6, min_length=6)
    
    def validate(self, attrs):
        """Validate that either email or phone number is provided."""
        email = attrs.get('email')
        phone_number = attrs.get('phone_number')
        
        if not email and not phone_number:
            raise serializers.ValidationError(
                _('Either email or phone number is required.')
            )
        
        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    otp = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate that either email or phone number is provided."""
        email = attrs.get('email')
        phone_number = attrs.get('phone_number')
        
        if not email and not phone_number:
            raise serializers.ValidationError(
                _('Either email or phone number is required.')
            )
        
        return attrs
