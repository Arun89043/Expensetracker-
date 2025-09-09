from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from userpreferences.models import UserPreference

class BaseFinanceView(LoginRequiredMixin, View):
    """
    Base view class for financial features in the application.
    
    This class provides common functionality for views dealing with financial data,
    including pagination, sorting, and currency handling. It enforces login requirements
    and provides consistent context data handling across financial views.
    
    Attributes:
        login_url (str): URL to redirect to if user is not authenticated
        items_per_page (int): Number of items to show per page
        template_name (str): Template to render (must be set by subclass)
        context_object_name (str): Name for the main queryset in context
    """
    
    login_url = '/authentication/login'
    items_per_page = 5
    template_name = None
    context_object_name = 'items'

    def get_queryset(self):
        raise NotImplementedError("Subclasses must implement get_queryset()")

    def get_currency(self):
        try:
            return UserPreference.objects.get(user=self.request.user).currency
        except UserPreference.DoesNotExist:
            return None

    def get_sorted_queryset(self, queryset):
        sort_order = self.request.GET.get('sort')
        if sort_order == 'amount_asc':
            return queryset.order_by('amount')
        elif sort_order == 'amount_desc':
            return queryset.order_by('-amount')
        elif sort_order == 'date_asc':
            return queryset.order_by('date')
        elif sort_order == 'date_desc':
            return queryset.order_by('-date')
        return queryset

    def get_paginated_data(self, queryset):
        paginator = Paginator(queryset, self.items_per_page)
        page_number = self.request.GET.get('page')
        return Paginator.get_page(paginator, page_number)

    def get_context_data(self, **kwargs):
        queryset = self.get_queryset()
        sorted_queryset = self.get_sorted_queryset(queryset)
        page_obj = self.get_paginated_data(sorted_queryset)
        currency = self.get_currency()

        context = {
            self.context_object_name: sorted_queryset,
            'page_obj': page_obj,
            'currency': currency,
            'total': page_obj.paginator.num_pages,
            'sort_order': self.request.GET.get('sort'),
        }
        context.update(kwargs)
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)
