from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def home_view(request):
    """Homepage showing welcome message and features"""

    context = {
        'is_authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None,
    }

    return render(request, 'home.html', context)
