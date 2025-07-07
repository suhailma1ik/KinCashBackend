"""
Tests for the loans app.
"""
import uuid
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
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
from apps.loans.services import ScheduleGenerator, PaymentService


class LoanModelTests(TestCase):
    """Tests for the Loan model."""
    
    def setUp(self):
        """Set up test data."""
        self.lender = User.objects.create_user(
            email='lender@example.com',
            phone_number='+1234567890',
            password='testpassword',
            first_name='Lender',
            last_name='User'
        )
        
        self.borrower = User.objects.create_user(
            email='borrower@example.com',
            phone_number='+0987654321',
            password='testpassword',
            first_name='Borrower',
            last_name='User'
        )
        
        self.loan = Loan.objects.create(
            lender=self.lender,
            borrower=self.borrower,
            principal_amount=Decimal('1000.00'),
            interest_rate_pct=Decimal('5.0'),
            term_months=12,
            emi_cycle=EMICycle.MONTHLY,
            status=LoanStatus.PENDING,
            late_fee_pct=Decimal('1.0')
        )
    
    def test_loan_creation(self):
        """Test loan creation."""
        self.assertEqual(Loan.objects.count(), 1)
        self.assertEqual(self.loan.lender, self.lender)
        self.assertEqual(self.loan.borrower, self.borrower)
        self.assertEqual(self.loan.principal_amount, Decimal('1000.00'))
        self.assertEqual(self.loan.interest_rate_pct, Decimal('5.0'))
        self.assertEqual(self.loan.term_months, 12)
        self.assertEqual(self.loan.emi_cycle, EMICycle.MONTHLY)
        self.assertEqual(self.loan.status, LoanStatus.PENDING)
        self.assertEqual(self.loan.late_fee_pct, Decimal('1.0'))
    
    def test_loan_str(self):
        """Test loan string representation."""
        expected_str = f"Loan {self.loan.id} - {self.lender} to {self.borrower} - 1000.00"
        self.assertEqual(str(self.loan), expected_str)
    
    def test_loan_activate(self):
        """Test loan activation."""
        self.loan.activate()
        self.assertEqual(self.loan.status, LoanStatus.ACTIVE)
        self.assertIsNotNone(self.loan.approved_at)
        
        # Check if repayment schedules were generated
        schedules = self.loan.repayment_schedules.all()
        self.assertEqual(schedules.count(), 12)  # 12 months
    
    def test_loan_mark_as_paid(self):
        """Test marking a loan as paid."""
        self.loan.activate()
        
        # Mark all schedules as paid
        for schedule in self.loan.repayment_schedules.all():
            schedule.mark_as_paid()
        
        # Check if loan is marked as paid
        self.loan.mark_as_paid()
        self.assertEqual(self.loan.status, LoanStatus.PAID)
        self.assertIsNotNone(self.loan.closed_at)
    
    def test_loan_mark_as_defaulted(self):
        """Test marking a loan as defaulted."""
        self.loan.activate()
        self.loan.mark_as_defaulted()
        self.assertEqual(self.loan.status, LoanStatus.DEFAULTED)
    
    def test_loan_cancel(self):
        """Test canceling a loan."""
        self.loan.cancel()
        self.assertEqual(self.loan.status, LoanStatus.CANCELLED)


class RepaymentScheduleModelTests(TestCase):
    """Tests for the RepaymentSchedule model."""
    
    def setUp(self):
        """Set up test data."""
        self.lender = User.objects.create_user(
            email='lender@example.com',
            phone_number='+1234567890',
            password='testpassword',
            first_name='Lender',
            last_name='User'
        )
        
        self.borrower = User.objects.create_user(
            email='borrower@example.com',
            phone_number='+0987654321',
            password='testpassword',
            first_name='Borrower',
            last_name='User'
        )
        
        self.loan = Loan.objects.create(
            lender=self.lender,
            borrower=self.borrower,
            principal_amount=Decimal('1000.00'),
            interest_rate_pct=Decimal('5.0'),
            term_months=12,
            emi_cycle=EMICycle.MONTHLY,
            status=LoanStatus.ACTIVE,
            late_fee_pct=Decimal('1.0'),
            approved_at=timezone.now()
        )
        
        self.schedule = RepaymentSchedule.objects.create(
            loan=self.loan,
            due_date=timezone.now().date(),
            amount_due=Decimal('100.00'),
            interest_component=Decimal('5.00')
        )
    
    def test_schedule_creation(self):
        """Test repayment schedule creation."""
        self.assertEqual(RepaymentSchedule.objects.count(), 1)
        self.assertEqual(self.schedule.loan, self.loan)
        self.assertEqual(self.schedule.amount_due, Decimal('100.00'))
        self.assertEqual(self.schedule.interest_component, Decimal('5.00'))
        self.assertEqual(self.schedule.status, RepaymentScheduleStatus.DUE)
    
    def test_schedule_str(self):
        """Test repayment schedule string representation."""
        expected_str = f"Schedule {self.schedule.id} - Loan {self.loan.id} - Due {self.schedule.due_date}"
        self.assertEqual(str(self.schedule), expected_str)
    
    def test_schedule_mark_as_paid(self):
        """Test marking a schedule as paid."""
        self.schedule.mark_as_paid()
        self.assertEqual(self.schedule.status, RepaymentScheduleStatus.PAID)
        self.assertEqual(self.schedule.amount_paid, Decimal('100.00'))
        self.assertIsNotNone(self.schedule.paid_at)
    
    def test_schedule_mark_as_late(self):
        """Test marking a schedule as late."""
        # Set due date to yesterday
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        self.schedule.due_date = yesterday
        self.schedule.save()
        
        self.schedule.mark_as_late()
        self.assertEqual(self.schedule.status, RepaymentScheduleStatus.LATE)


class ScheduleGeneratorTests(TestCase):
    """Tests for the ScheduleGenerator service."""
    
    def setUp(self):
        """Set up test data."""
        self.lender = User.objects.create_user(
            email='lender@example.com',
            phone_number='+1234567890',
            password='testpassword',
            first_name='Lender',
            last_name='User'
        )
        
        self.borrower = User.objects.create_user(
            email='borrower@example.com',
            phone_number='+0987654321',
            password='testpassword',
            first_name='Borrower',
            last_name='User'
        )
        
        self.loan = Loan.objects.create(
            lender=self.lender,
            borrower=self.borrower,
            principal_amount=Decimal('1000.00'),
            interest_rate_pct=Decimal('12.0'),  # 12% annual interest
            term_months=12,
            emi_cycle=EMICycle.MONTHLY,
            status=LoanStatus.ACTIVE,
            approved_at=timezone.now()
        )
    
    def test_calculate_emi(self):
        """Test EMI calculation."""
        emi = ScheduleGenerator.calculate_emi(
            principal=Decimal('1000.00'),
            rate=Decimal('12.0'),
            term=12,
            cycle=EMICycle.MONTHLY
        )
        
        # Expected EMI for 1000 at 12% for 12 months is approximately 88.85
        self.assertAlmostEqual(float(emi), 88.85, places=2)
    
    def test_generate_schedules(self):
        """Test schedule generation."""
        schedules = ScheduleGenerator.generate_schedules(self.loan)
        
        # Check if correct number of schedules were generated
        self.assertEqual(len(schedules), 12)
        
        # Check if total amount due equals principal plus interest
        total_due = sum(schedule.amount_due for schedule in schedules)
        self.assertAlmostEqual(float(total_due), 1066.20, places=2)  # Principal + Interest
        
        # Check if schedules are properly spaced
        for i in range(1, len(schedules)):
            prev_date = schedules[i-1].due_date
            curr_date = schedules[i].due_date
            
            # Check if dates are approximately one month apart
            days_diff = (curr_date - prev_date).days
            self.assertTrue(28 <= days_diff <= 31)


class LoanAPITests(APITestCase):
    """Tests for the Loan API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.lender = User.objects.create_user(
            email='lender@example.com',
            phone_number='+1234567890',
            password='testpassword',
            first_name='Lender',
            last_name='User'
        )
        
        self.borrower = User.objects.create_user(
            email='borrower@example.com',
            phone_number='+0987654321',
            password='testpassword',
            first_name='Borrower',
            last_name='User'
        )
        
        self.loan = Loan.objects.create(
            lender=self.lender,
            borrower=self.borrower,
            principal_amount=Decimal('1000.00'),
            interest_rate_pct=Decimal('5.0'),
            term_months=12,
            emi_cycle=EMICycle.MONTHLY,
            status=LoanStatus.PENDING
        )
        
        self.create_loan_url = reverse('create_loan')
        self.get_loans_url = reverse('get_loans')
        self.accept_loan_url = reverse('accept_loan')
        
        # Get tokens for authentication
        self.lender_token = self._get_token(self.lender)
        self.borrower_token = self._get_token(self.borrower)
    
    def _get_token(self, user):
        """Helper method to get token for a user."""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_create_loan(self):
        """Test creating a loan."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.lender_token}')
        
        data = {
            'lender': str(self.lender.id),
            'borrower': str(self.borrower.id),
            'principal_amount': '2000.00',
            'interest_rate_pct': '6.0',
            'term_months': 24,
            'emi_cycle': EMICycle.MONTHLY,
            'due_date': 15,
            'is_lender': True
        }
        
        response = self.client.post(self.create_loan_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Loan.objects.count(), 2)
        
        new_loan = Loan.objects.get(principal_amount=Decimal('2000.00'))
        self.assertEqual(new_loan.lender, self.lender)
        self.assertEqual(new_loan.borrower, self.borrower)
        self.assertEqual(new_loan.interest_rate_pct, Decimal('6.0'))
        self.assertEqual(new_loan.term_months, 24)
    
    def test_get_loans(self):
        """Test getting loans."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.lender_token}')
        
        response = self.client.get(self.get_loans_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['loans']), 1)
        self.assertEqual(response.data['data']['loans'][0]['id'], str(self.loan.id))
    
    def test_accept_loan(self):
        """Test accepting a loan."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.borrower_token}')
        
        data = {
            'loan_id': str(self.loan.id)
        }
        
        response = self.client.post(self.accept_loan_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh loan from database
        self.loan.refresh_from_db()
        self.assertEqual(self.loan.status, LoanStatus.ACTIVE)
        self.assertIsNotNone(self.loan.approved_at)
        
        # Check if repayment schedules were generated
        schedules = self.loan.repayment_schedules.all()
        self.assertEqual(schedules.count(), 12)  # 12 months
