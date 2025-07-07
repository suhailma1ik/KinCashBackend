"""
Authentication backends for the users app.
"""
import logging
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from apps.users.models import User

# Set up logger
logger = logging.getLogger('django')

class EmailPhoneBackend(ModelBackend):
    """
    Custom authentication backend that allows login with either email or phone number.
    
    This backend can handle authentication with a single identifier field that can be
    either an email address or a phone number, along with a password.
    """
    
    def authenticate(self, request, email=None, phone_number=None, password=None, **kwargs):
        """
        Authenticate a user based on email or phone number.
        
        Args:
            request: The request object
            email: Email address
            phone_number: Phone number
            password: Password
            **kwargs: Additional keyword arguments
            
        Returns:
            User instance if authentication is successful, None otherwise
        """
        try:
            # If no credentials provided, return None
            if password is None:
                logger.debug('No password provided for authentication')
                return None
                
            if email is None and phone_number is None:
                logger.debug('No email or phone number provided for authentication')
                return None
                
            # Try to find the user by either email or phone number
            user = None
            if email:
                logger.debug(f'Attempting to authenticate with email: {email}')
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    logger.debug(f'No user found with email: {email}')
                    return None
            elif phone_number:
                logger.debug(f'Attempting to authenticate with phone number: {phone_number}')
                try:
                    user = User.objects.get(phone_number=phone_number)
                except User.DoesNotExist:
                    logger.debug(f'No user found with phone number: {phone_number}')
                    return None
            
            # Check if user is active and not deleted
            if user and not user.is_active:
                logger.debug(f'User {user.id} is not active')
                return None
                
            if user and user.is_deleted:
                logger.debug(f'User {user.id} is deleted')
                return None
                
            # Check the password
            if user and user.check_password(password):
                logger.debug(f'Authentication successful for user: {user.id}')
                return user
            else:
                logger.debug('Password check failed')
                return None
                
        except Exception as e:
            logger.error(f'Authentication error: {str(e)}')
            return None
