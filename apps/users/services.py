"""
Services for the users app.
"""
import random
import string
from datetime import datetime, timedelta

from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class OTPService:
    """Service for generating and verifying OTPs."""
    
    @staticmethod
    def generate_otp(length=6):
        """Generate a random OTP of specified length."""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def store_otp(user, otp, expiry_minutes=10):
        """Store OTP in cache with expiry time."""
        cache_key = f"otp_{user.id}"
        expiry_time = datetime.now() + timedelta(minutes=expiry_minutes)
        cache.set(cache_key, {'otp': otp, 'expiry': expiry_time}, timeout=expiry_minutes * 60)
    
    @staticmethod
    def verify_otp(user, otp):
        """Verify OTP against stored value."""
        cache_key = f"otp_{user.id}"
        stored_data = cache.get(cache_key)
        
        if not stored_data:
            return False
        
        stored_otp = stored_data.get('otp')
        expiry_time = stored_data.get('expiry')
        
        if stored_otp == otp and datetime.now() < expiry_time:
            # OTP verified, delete it to prevent reuse
            cache.delete(cache_key)
            return True
        
        return False
    
    @staticmethod
    def send_otp_email(user):
        """Send OTP via email."""
        otp = OTPService.generate_otp()
        OTPService.store_otp(user, otp)
        
        subject = _("Your OTP for H.E.L.P")
        message = _(f"Your OTP is {otp}. It will expire in 10 minutes.")
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]
        
        try:
            send_mail(subject, message, from_email, recipient_list)
            return True
        except Exception:
            return False
    
    @staticmethod
    def send_otp_sms(user):
        """Send OTP via SMS."""
        otp = OTPService.generate_otp()
        OTPService.store_otp(user, otp)
        
        # In a real implementation, you would integrate with an SMS gateway
        # For now, we'll just print the OTP to the console
        print(f"SMS to {user.phone_number}: Your OTP is {otp}. It will expire in 10 minutes.")
        
        # Always return True for now since we're not actually sending SMS
        return True
