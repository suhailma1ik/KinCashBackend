"""
Integration tests for the H.E.L.P Backend.

These tests cover complete flows from user registration to loan creation, acceptance, and payment.
"""
import uuid
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
from apps.loans.models import (
    Loan,
    RepaymentSchedule,
    Payment,
    LoanStatus,
    EMICycle,
    RepaymentScheduleStatus,
)


class LoanFlowIntegrationTest(APITestCase):
    """
    Integration test for the complete loan flow.
    
    This test covers:
    1. User registration (lender and borrower)
    2. Loan creation
    3. Loan acceptance
    4. EMI payment
    """
    
    def setUp(self):
        """Set up test data."""
        self.signup_url = reverse('signup')
        self.create_loan_url = reverse('create_loan')
        self.accept_loan_url = reverse('accept_loan')
        self.pay_emi_url = reverse('pay_emi')
        
        # Register lender
        lender_data = {
            'email': 'lender@example.com',
            'phone_number': '+1234567890',
            'password': 'testpassword',
            'first_name': 'Lender',
            'last_name': 'User'
        }
        response = self.client.post(self.signup_url, lender_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.lender_id = response.data['data']['user']['id']
        self.lender_token = response.data['data']['token']['access']
        
        # Register borrower
        borrower_data = {
            'email': 'borrower@example.com',
            'phone_number': '+0987654321',
            'password': 'testpassword',
            'first_name': 'Borrower',
            'last_name': 'User'
        }
        response = self.client.post(self.signup_url, borrower_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.borrower_id = response.data['data']['user']['id']
        self.borrower_token = response.data['data']['token']['access']
    
    def test_complete_loan_flow(self):
        """Test the complete loan flow."""
        # Step 1: Lender creates a loan
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.lender_token}')
        
        loan_data = {
            'lender': self.lender_id,
            'borrower': self.borrower_id,
            'principal_amount': '1000.00',
            'interest_rate_pct': '5.0',
            'term_months': 12,
            'emi_cycle': EMICycle.MONTHLY,
            'due_date': 15,
            'is_lender': True
        }
        
        response = self.client.post(self.create_loan_url, loan_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        loan_id = response.data['data']['id']
        
        # Step 2: Borrower accepts the loan
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.borrower_token}')
        
        accept_data = {
            'loan_id': loan_id
        }
        
        response = self.client.post(self.accept_loan_url, accept_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify loan is active
        loan = Loan.objects.get(id=loan_id)
        self.assertEqual(loan.status, LoanStatus.ACTIVE)
        
        # Verify repayment schedules were created
        schedules = RepaymentSchedule.objects.filter(loan=loan)
        self.assertEqual(schedules.count(), 12)
        
        # Step 3: Borrower makes a payment for the first EMI
        first_schedule = schedules.order_by('due_date').first()
        
        pay_data = {
            'loan_id': loan_id,
            'emi_id': first_schedule.id,
            'amount': float(first_schedule.amount_due),
            'remarks': 'First EMI payment'
        }
        
        response = self.client.post(self.pay_emi_url, pay_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify payment was recorded
        first_schedule.refresh_from_db()
        self.assertEqual(first_schedule.status, RepaymentScheduleStatus.PAID)
        self.assertIsNotNone(first_schedule.paid_at)
        
        # Verify payment record was created
        payment = Payment.objects.filter(loan=loan).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount, Decimal(str(pay_data['amount'])))
        self.assertEqual(payment.payer.id, self.borrower_id)


class NotificationIntegrationTest(APITestCase):
    """
    Integration test for the notification flow.
    
    This test covers:
    1. User registration
    2. Creating a notification
    3. Marking a notification as read
    """
    
    def setUp(self):
        """Set up test data."""
        self.signup_url = reverse('signup')
        self.create_notification_url = reverse('create_notification')
        self.mark_notification_read_url = reverse('mark_notification_read')
        
        # Register sender
        sender_data = {
            'email': 'sender@example.com',
            'phone_number': '+1234567890',
            'password': 'testpassword',
            'first_name': 'Sender',
            'last_name': 'User'
        }
        response = self.client.post(self.signup_url, sender_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.sender_id = response.data['data']['user']['id']
        self.sender_token = response.data['data']['token']['access']
        
        # Register recipient
        recipient_data = {
            'email': 'recipient@example.com',
            'phone_number': '+0987654321',
            'password': 'testpassword',
            'first_name': 'Recipient',
            'last_name': 'User'
        }
        response = self.client.post(self.signup_url, recipient_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.recipient_id = response.data['data']['user']['id']
        self.recipient_token = response.data['data']['token']['access']
    
    def test_notification_flow(self):
        """Test the notification flow."""
        # Step 1: Sender creates a notification
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.sender_token}')
        
        notification_data = {
            'recipient_id': self.recipient_id,
            'title': 'Test Notification',
            'body': 'This is a test notification.'
        }
        
        response = self.client.post(self.create_notification_url, notification_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notification_id = response.data['data']['id']
        
        # Step 2: Recipient marks the notification as read
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.recipient_token}')
        
        mark_read_data = {
            'notification_id': notification_id
        }
        
        response = self.client.post(self.mark_notification_read_url, mark_read_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['is_read'])
