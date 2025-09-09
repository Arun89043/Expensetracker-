#!/usr/bin/env python
"""
Script to add default expense categories to the ExpenseTracker database.
Run this script to populate the Category table with common expense categories.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expensetracker.settings')
django.setup()

from expenses.models import Category

def add_default_categories():
    """Add default expense categories to the database."""
    
    default_categories = [
        'Food & Dining',
        'Transportation',
        'Shopping',
        'Entertainment',
        'Bills & Utilities',
        'Healthcare',
        'Travel',
        'Education',
        'Personal Care',
        'Home & Garden',
        'Groceries',
        'Gas & Fuel',
        'Clothing',
        'Electronics',
        'Sports & Fitness',
        'Gifts & Donations',
        'Business',
        'Insurance',
        'Taxes',
        'Other'
    ]
    
    print("Adding default expense categories...")
    
    categories_added = 0
    categories_existed = 0
    
    for category_name in default_categories:
        category, created = Category.objects.get_or_create(name=category_name)
        if created:
            print(f"✅ Added: {category_name}")
            categories_added += 1
        else:
            print(f"⚠️  Already exists: {category_name}")
            categories_existed += 1
    
    print(f"\n📊 Summary:")
    print(f"   • Categories added: {categories_added}")
    print(f"   • Categories already existed: {categories_existed}")
    print(f"   • Total categories in database: {Category.objects.count()}")
    print(f"\n🎉 Default categories setup complete!")
    print(f"You can now select categories when adding expenses.")

if __name__ == '__main__':
    add_default_categories()
