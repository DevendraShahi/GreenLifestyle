"""
Script to approve all existing categories after migration.
Run this once with: python manage.py shell < approve_categories.py
"""

from tips.models import Category
from django.utils import timezone

# Approve all existing categories
categories = Category.objects.filter(is_approved=False)

for category in categories:
    category.is_approved = True
    category.approved_at = timezone.now()
    category.save()
    print(f"Approved: {category.name}")

print(f"\nTotal categories approved: {categories.count()}")
print(f"Total approved categories: {Category.objects.filter(is_approved=True).count()}")
