from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tips.models import Tip, Category
from accounts.models import CustomUser, UserActivity


def home_view(request):
    """Homepage showing welcome message and features"""
    
    # Log activity
    UserActivity.log_activity(request)

    # stats
    total_tips = Tip.objects.count()
    total_users = CustomUser.objects.count()
    total_categories = Category.objects.count()

    context = {
        'is_authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None,
        'total_tips': total_tips,
        'total_users': total_users,
        'total_categories': total_categories,
    }

    return render(request, 'home.html', context)
