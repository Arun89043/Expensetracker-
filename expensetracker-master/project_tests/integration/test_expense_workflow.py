"""
Integration tests for the expense tracking workflow.
Tests the interaction between different components of the system.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from expenses.models import Expense, Category, ExpenseLimit
from userpreferences.models import UserPreference
from django.utils import timezone
from decimal import Decimal

class ExpenseWorkflowTest(TestCase):
    def setUp(self):
        """Set up test data for all test methods."""
        # Create test user
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')

        # Create user preferences
        self.user_pref = UserPreference.objects.create(
            user=self.user,
            currency='USD'
        )

        # Create expense limit
        self.expense_limit = ExpenseLimit.objects.create(
            owner=self.user,
            daily_expense_limit=1000
        )

        # Create categories
        self.category = Category.objects.create(name='Food')

    def test_complete_expense_workflow(self):
        """
        Test the complete workflow of expense management:
        1. Add an expense
        2. View expense list
        3. Edit expense
        4. Check expense limit
        5. View expense summary
        """
        # 1. Add new expense
        add_expense_data = {
            'amount': '50.00',
            'description': 'Lunch',
            'category': 'Food',
            'date': timezone.now().date().isoformat()
        }
        
        response = self.client.post(
            reverse('add-expenses'),
            add_expense_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify expense was created
        expense = Expense.objects.filter(description='Lunch').first()
        self.assertIsNotNone(expense)
        self.assertEqual(expense.amount, 50.00)

        # 2. View expense list
        response = self.client.get(reverse('expenses'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lunch')

        # 3. Edit expense
        edit_data = {
            'amount': '60.00',
            'description': 'Lunch updated',
            'category': 'Food',
            'date': timezone.now().date().isoformat()
        }
        
        response = self.client.post(
            reverse('expense-edit', args=[expense.id]),
            edit_data
        )
        self.assertEqual(response.status_code, 302)

        # Verify expense was updated
        expense.refresh_from_db()
        self.assertEqual(expense.amount, 60.00)
        self.assertEqual(expense.description, 'Lunch updated')

        # 4. Check expense limit
        # Add more expenses to test limit
        for _ in range(15):
            Expense.objects.create(
                owner=self.user,
                amount=100.00,
                date=timezone.now().date(),
                category='Food',
                description='Test expense'
            )

        response = self.client.get(reverse('expenses'))
        self.assertContains(response, 'daily expense limit')

        # 5. View expense summary
        response = self.client.get(reverse('expense_category_summary'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Food' in str(response.content))

    def test_expense_report_generation(self):
        """Test the expense report generation workflow."""
        # Create some test expenses
        dates = [
            timezone.now().date(),
            timezone.now().date() - timezone.timedelta(days=1),
            timezone.now().date() - timezone.timedelta(days=2)
        ]
        
        for date in dates:
            Expense.objects.create(
                owner=self.user,
                amount=100.00,
                date=date,
                category='Food',
                description=f'Test expense on {date}'
            )

        # Test CSV export
        response = self.client.get(
            reverse('export_csv'),
            {'start_date': dates[-1], 'end_date': dates[0]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

        # Test PDF export
        response = self.client.get(
            reverse('export_pdf'),
            {'start_date': dates[-1], 'end_date': dates[0]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
