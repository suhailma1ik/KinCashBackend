"""
Tests for the users app.
"""
import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User, KYCStatus


class UserModelTests(TestCase):
    """Tests for the User model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='+1234567890',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_creation(self):
        """Test user creation."""
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.phone_number, '+1234567890')
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, 'User')
        self.assertEqual(self.user.kyc_status, KYCStatus.PENDING)
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
    
    def test_user_str(self):
        """Test user string representation."""
        self.assertEqual(str(self.user), 'Test User')
    
    def test_get_full_name(self):
        """Test get_full_name method."""
        self.assertEqual(self.user.get_full_name(), 'Test User')
    
    def test_get_short_name(self):
        """Test get_short_name method."""
        self.assertEqual(self.user.get_short_name(), 'Test')
    
    def test_soft_delete(self):
        """Test soft_delete method."""
        self.user.soft_delete()
        self.assertTrue(self.user.is_deleted)
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.deleted_at)


class UserAPITests(APITestCase):
    """Tests for the User API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        
        self.user_data = {
            'email': 'test@example.com',
            'phone_number': '+1234567890',
            'password': 'testpassword',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        self.user = User.objects.create_user(
            email='existing@example.com',
            phone_number='+0987654321',
            password='existingpassword',
            first_name='Existing',
            last_name='User'
        )
    
    def test_signup(self):
        """Test user signup."""
        response = self.client.post(self.signup_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(response.data['data']['user']['email'], self.user_data['email'])
        self.assertEqual(response.data['data']['user']['phone_number'], self.user_data['phone_number'])
        self.assertEqual(response.data['data']['user']['first_name'], self.user_data['first_name'])
        self.assertEqual(response.data['data']['user']['last_name'], self.user_data['last_name'])
        self.assertIn('token', response.data['data'])
    
    def test_signup_duplicate_email(self):
        """Test user signup with duplicate email."""
        self.user_data['email'] = 'existing@example.com'
        response = self.client.post(self.signup_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_signup_duplicate_phone(self):
        """Test user signup with duplicate phone."""
        self.user_data['phone_number'] = '+0987654321'
        response = self.client.post(self.signup_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_with_email(self):
        """Test user login with email."""
        login_data = {
            'identifier': 'existing@example.com',
            'password': 'existingpassword'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data['data'])
        self.assertEqual(response.data['data']['user']['email'], self.user.email)
    
    def test_login_with_phone(self):
        """Test user login with phone."""
        login_data = {
            'identifier': '+0987654321',
            'password': 'existingpassword'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data['data'])
        self.assertEqual(response.data['data']['user']['phone_number'], self.user.phone_number)
    
    def test_login_invalid_credentials(self):
        """Test user login with invalid credentials."""
        login_data = {
            'identifier': 'existing@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_login_missing_identifier(self):
        """Test user login with missing identifier."""
        login_data = {
            'password': 'existingpassword'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_login_missing_password(self):
        """Test user login with missing password."""
        login_data = {
            'identifier': 'existing@example.com'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
