"""
Tests for the API endpoints.
Ensures all API endpoints are working correctly and returning proper responses.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from expenses.models import Expense, Category
from userincome.models import UserIncome, Source
from goals.models import Goal
from django.utils import timezone
import json

class APIEndpointTests(TestCase):
    def setUp(self):
        """Set up test data for all test methods."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.category = Category.objects.create(name='Food')
        self.expense = Expense.objects.create(
            owner=self.user,
            amount=100.00,
            date=timezone.now().date(),
            category='Food',
            description='Test expense'
        )
        
        self.source = Source.objects.create(
            name='Salary',
            owner=self.user
        )
        self.income = UserIncome.objects.create(
            owner=self.user,
            amount=1000.00,
            date=timezone.now().date(),
            source='Salary',
            description='Monthly salary'
        )
        
        self.goal = Goal.objects.create(
            owner=self.user,
            name='Emergency Fund',
            amount_to_save=5000.00,
            current_saved_amount=1000.00,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=90)
        )

    def test_expense_list_endpoint(self):
        """Test the expense list endpoint."""
        response = self.client.get(reverse('expense-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        
        # Test expense creation
        new_expense = {
            'amount': 150.00,
            'date': timezone.now().date().isoformat(),
            'category': 'Food',
            'description': 'New test expense'
        }
        response = self.client.post(reverse('expense-list'), new_expense)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the expense was created
        self.assertTrue(
            Expense.objects.filter(description='New test expense').exists()
        )

    def test_income_list_endpoint(self):
        """Test the income list endpoint."""
        response = self.client.get(reverse('income-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        
        # Test income creation
        new_income = {
            'amount': 2000.00,
            'date': timezone.now().date().isoformat(),
            'source': 'Salary',
            'description': 'New test income'
        }
        response = self.client.post(reverse('income-list'), new_income)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_goals_endpoint(self):
        """Test the goals endpoint."""
        response = self.client.get(reverse('goal-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test goal creation
        new_goal = {
            'name': 'New Car',
            'amount_to_save': 20000.00,
            'start_date': timezone.now().date().isoformat(),
            'end_date': (timezone.now().date() + timezone.timedelta(days=365)).isoformat()
        }
        response = self.client.post(reverse('goal-list'), new_goal)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_expense_summary_endpoint(self):
        """Test the expense summary endpoint."""
        response = self.client.get(reverse('expense-summary'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('total_expenses' in response.data)
        self.assertTrue('expenses_by_category' in response.data)

    def test_unauthorized_access(self):
        """Test unauthorized access to endpoints."""
        client = APIClient()  # Unauthenticated client
        
        # Test expense list endpoint
        response = client.get(reverse('expense-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test income list endpoint
        response = client.get(reverse('income-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test goals endpoint
        response = client.get(reverse('goal-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expense_detail_endpoint(self):
        """Test the expense detail endpoint."""
        url = reverse('expense-detail', args=[self.expense.id])
        
        # Test GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '100.00')
        
        # Test PUT
        updated_data = {
            'amount': 200.00,
            'date': timezone.now().date().isoformat(),
            'category': 'Food',
            'description': 'Updated test expense'
        }
        response = self.client.put(url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test DELETE
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Expense.objects.filter(id=self.expense.id).exists()
        )
