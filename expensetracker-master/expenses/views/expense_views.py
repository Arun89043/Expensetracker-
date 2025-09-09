from django.shortcuts import redirect, render
from django.contrib import messages
from ..models import Expense, Category
from .base import BaseFinanceView
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from ..models import ExpenseLimit

class ExpenseListView(BaseFinanceView):
    """
    View for displaying a list of expenses.
    
    This view handles the display of all expenses for the logged-in user,
    including pagination, sorting, and filtering capabilities.
    
    Attributes:
        template_name (str): The template to render
        context_object_name (str): The name to use for the expense list in context
    """
    
    template_name = 'expenses/index.html'
    context_object_name = 'expenses'

    def get_queryset(self):
        """
        Get the list of expenses for the current user.
        
        Returns:
            QuerySet: A queryset of Expense objects filtered by the current user
        """
        return Expense.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

class ExpenseCreateView(BaseFinanceView):
    template_name = 'expenses/add_expense.html'

    def get_context_data(self, **kwargs):
        return {
            'categories': Category.objects.all(),
            'values': self.request.POST
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        amount = request.POST.get('amount')
        date_str = request.POST.get('date')
        category = request.POST.get('category')
        description = request.POST.get('description')

        try:
            date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            if date > timezone.now().date():
                messages.error(request, 'Date cannot be in the future')
                return render(request, self.template_name, self.get_context_data())

            # Check expense limit
            user = request.user
            expense_limits = ExpenseLimit.objects.filter(owner=user)
            daily_limit = expense_limits.first().daily_expense_limit if expense_limits.exists() else 5000

            total_expenses_today = sum(
                expense.amount for expense in Expense.objects.filter(
                    owner=user, 
                    date=timezone.now().date()
                )
            ) + float(amount)

            if total_expenses_today > daily_limit:
                self._send_limit_exceeded_email(user, daily_limit)
                messages.warning(request, 'Your expenses for today exceed your daily expense limit')

            Expense.objects.create(
                owner=user,
                amount=amount,
                date=date,
                category=category,
                description=description
            )
            messages.success(request, 'Expense saved successfully')
            return redirect('expenses')

        except ValueError:
            messages.error(request, 'Invalid date format')
            return render(request, self.template_name, self.get_context_data())

    def _send_limit_exceeded_email(self, user, limit):
        subject = 'Daily Expense Limit Exceeded'
        message = f'Hello {user.username},\n\nYour expenses for today have exceeded your daily expense limit of {limit}. Please review your expenses.'
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False
        )
