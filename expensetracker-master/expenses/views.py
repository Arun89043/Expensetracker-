from django.shortcuts import render, redirect, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from .models import Category, Expense, ExpenseLimit
from django.contrib import messages
from django.core.paginator import Paginator
import json
from django.http import JsonResponse
from userpreferences.models import UserPreference
import datetime
from datetime import date
from django.core.mail import send_mail
from django.conf import settings
import requests

@login_required(login_url='/authentication/login')
def search_expenses(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        expenses = Expense.objects.filter(
            amount__istartswith=search_str, owner=request.user) | Expense.objects.filter(
            date__istartswith=search_str, owner=request.user) | Expense.objects.filter(
            description__icontains=search_str, owner=request.user) | Expense.objects.filter(
            category__icontains=search_str, owner=request.user)
        data = expenses.values()
        return JsonResponse(list(data), safe=False)


@login_required(login_url='/authentication/login')
def index(request):
    categories = Category.objects.all()
    expenses = Expense.objects.filter(owner=request.user)

    sort_order = request.GET.get('sort')

    if sort_order == 'amount_asc':
        expenses = expenses.order_by('amount')
    elif sort_order == 'amount_desc':
        expenses = expenses.order_by('-amount')
    elif sort_order == 'date_asc':
        expenses = expenses.order_by('date')
    elif sort_order == 'date_desc':
        expenses = expenses.order_by('-date')

    paginator = Paginator(expenses, 5)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    try:
        currency = UserPreference.objects.get(user=request.user).currency
    except:
        currency=None

    total = page_obj.paginator.num_pages
    context = {
        'expenses': expenses,
        'page_obj': page_obj,
        'currency': currency,
        'total': total,
        'sort_order': sort_order,

    }
    return render(request, 'expenses/index.html', context)

daily_expense_amounts = {}

@login_required(login_url='/authentication/login')
def add_expense(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
        'values': request.POST
    }
    if request.method == 'GET':
        return render(request, 'expenses/add_expense.html', context)

    if request.method == 'POST':
        amount = request.POST.get('amount', '').strip()
        description = request.POST.get('description', '').strip()
        date_str = request.POST.get('expense_date', '').strip()
        predicted_category = request.POST.get('category', '')
        custom_category = request.POST.get('custom_category', '').strip()

        # Validate required fields
        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/add_expense.html', context)

        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'expenses/add_expense.html', context)
            
        if not date_str:
            messages.error(request, 'Date is required')
            return render(request, 'expenses/add_expense.html', context)
            
        # PARSE AND VALIDATE DATE FIRST - BEFORE ANYTHING ELSE
        try:
            expense_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            today = datetime.date.today()
            if expense_date > today:
                messages.error(request, 'Date cannot be in the future')
                return render(request, 'expenses/add_expense.html', context)
        except ValueError:
            messages.error(request, 'Please select a valid date')
            return render(request, 'expenses/add_expense.html', context)

        if not predicted_category:
            messages.error(request, 'Category is required')
            return render(request, 'expenses/add_expense.html', context)

        # Handle custom category creation
        if predicted_category == 'Other' and custom_category:
            # Create new category if it doesn't exist
            category_obj, created = Category.objects.get_or_create(name=custom_category)
            if created:
                messages.info(request, f'New category "{custom_category}" created successfully!')
            # Use the category object for the expense
            final_category_obj = category_obj
        elif predicted_category == 'Other' and not custom_category:
            messages.error(request, 'Please enter a custom category name when selecting "Other"')
            return render(request, 'expenses/add_expense.html', context)
        else:
            # Get the existing category by name
            try:
                final_category_obj = Category.objects.get(name=predicted_category)
            except Category.DoesNotExist:
                messages.error(request, f'Category "{predicted_category}" does not exist')
                return render(request, 'expenses/add_expense.html', context)
        
        initial_predicted_category = request.POST.get('initial_predicted_category')
        if predicted_category != initial_predicted_category:
            new_data = {
            'description': description,
            'category': predicted_category,  # Keep string for API call
        }

        update_url = 'http://127.0.0.1:8000/api/update-dataset/'
        response = requests.post(update_url, json={'new_data': new_data})

        user = request.user
        expense_limits = ExpenseLimit.objects.filter(owner=user)
        if expense_limits.exists():
            daily_expense_limit = expense_limits.first().daily_expense_limit
        else:
            daily_expense_limit = 5000  

        
        total_expenses_today = get_expense_of_day(user) + float(amount)
        if total_expenses_today > daily_expense_limit:
            subject = 'Daily Expense Limit Exceeded'
            message = f'Hello {user.username},\n\nYour expenses for today have exceeded your daily expense limit. Please review your expenses.'
            from_email = settings.EMAIL_HOST_USER
            to_email = [user.email]
            send_mail(subject, message, from_email, to_email, fail_silently=False)
            messages.warning(request, 'Your expenses for today exceed your daily expense limit')

        Expense.objects.create(owner=request.user, amount=amount, date=expense_date,
                               category=final_category_obj, description=description)  # Use category object
        messages.success(request, 'Expense saved successfully')
        return redirect('expenses')


@login_required(login_url='/authentication/login')
def expense_edit(request, id):
    expense = Expense.objects.get(pk=id)
    categories = Category.objects.all()
    context = {
        'expense': expense,
        'values': expense,
        'categories': categories
    }
    if request.method == 'GET':
        return render(request, 'expenses/edit-expense.html', context)
    if request.method == 'POST':
        amount = request.POST.get('amount', '').strip()
        description = request.POST.get('description', '').strip()
        date_str = request.POST.get('expense_date', '').strip()
        category = request.POST.get('category', '')

        # Validate required fields
        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/edit-expense.html', context)

        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'expenses/edit-expense.html', context)
            
        if not date_str:
            messages.error(request, 'Date is required')
            return render(request, 'expenses/edit-expense.html', context)
            
        if not category:
            messages.error(request, 'Category is required')
            return render(request, 'expenses/edit-expense.html', context)

        # PARSE AND VALIDATE DATE FIRST - BEFORE ANYTHING ELSE
        try:
            expense_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            today = datetime.date.today()
            if expense_date > today:
                messages.error(request, 'Date cannot be in the future')
                return render(request, 'expenses/edit-expense.html', context)
        except ValueError:
            messages.error(request, 'Please select a valid date')
            return render(request, 'expenses/edit-expense.html', context)

        try:
            expense.owner = request.user
            expense.amount = amount
            expense.date = expense_date
            expense.category = category
            expense.description = description

            expense.save()
            messages.success(request, 'Expense saved successfully')

            return redirect('expenses')
        except ValueError:
            messages.error(request, 'Invalid date format')
            return render(request, 'expenses/edit-expense.html', context)

@login_required(login_url='/authentication/login')
def delete_expense(request, id):
    expense = Expense.objects.get(pk=id)
    expense.delete()
    messages.success(request, 'Expense removed')
    return redirect('expenses')

@login_required(login_url='/authentication/login')
def expense_category_summary(request):
    todays_date = datetime.date.today()
    six_months_ago = todays_date-datetime.timedelta(days=30*6)
    expenses = Expense.objects.filter(owner=request.user,
                                      date__gte=six_months_ago, date__lte=todays_date)
    finalrep = {}

    def get_category_name(expense):
        return expense.category.name
    
    # Get unique category names
    category_list = list(set(map(get_category_name, expenses)))

    def get_expense_category_amount(category_name):
        amount = 0
        filtered_by_category = expenses.filter(category__name=category_name)

        for item in filtered_by_category:
            amount += item.amount
        return amount

    # Calculate total amount for each category
    for category_name in category_list:
        finalrep[category_name] = get_expense_category_amount(category_name)

    return JsonResponse({'expense_category_data': finalrep}, safe=False)

@login_required(login_url='/authentication/login')
def stats_view(request):
    return render(request, 'expenses/stats.html')

@login_required(login_url='/authentication/login')
def predict_category(description):
    predict_category_url = 'http://localhost:8000/api/predict-category/'  # Use the correct URL path
    data = {'description': description}
    response = requests.post(predict_category_url, data=data)

    if response.status_code == 200:
        # Get the predicted category from the response
        predicted_category = response.json().get('predicted_category')
        return predicted_category
    else:
        # Handle the case where the prediction request failed
        return None
    

def set_expense_limit(request):
    if request.method == "POST":
        daily_expense_limit = request.POST.get('daily_expense_limit')
        
        existing_limit = ExpenseLimit.objects.filter(owner=request.user).first()
        
        if existing_limit:
            existing_limit.daily_expense_limit = daily_expense_limit
            existing_limit.save()
        else:
            ExpenseLimit.objects.create(owner=request.user, daily_expense_limit=daily_expense_limit)
        
        messages.success(request, "Daily Expense Limit Updated Successfully!")
        return HttpResponseRedirect('/preferences/')
    else:
        return HttpResponseRedirect('/preferences/')
    
def get_expense_of_day(user):
    current_date=date.today()
    expenses=Expense.objects.filter(owner=user,date=current_date)
    total_expenses=sum(expense.amount for expense in expenses)
    return total_expenses