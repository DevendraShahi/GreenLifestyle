# views.py - UPDATED VERSION
# This combines profile viewing and editing in one view for inline editing
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models  # Add this for aggregate functions

from .models import CustomUser
from tips.models import Tip
from .forms import UserProfileForm, SignupForm, LoginForm
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import CustomUser, Follow, UserActivity


@login_required(login_url='accounts:login')
def profile_view(request, username=None):
    """
    Display user profile - own or other user's
    Also handles profile editing for own profile (inline editing)
    """
    
    if username is None:
        profile_user = request.user
    else:
        profile_user = get_object_or_404(CustomUser, username=username)
    
    is_own_profile = profile_user == request.user
    
    # Handle profile edit form submission (for inline editing)
    if request.method == 'POST' and is_own_profile:
        form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile_user
        )

        if form.is_valid():
            form.save()
            messages.success(request, '✓ Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            # Show error messages
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f'{error}')
                    else:
                        field_name = field.replace('_', ' ').title()
                        messages.error(request, f'{field_name}: {error}')
    
    # Check if current user is following this profile
    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = request.user.is_following(profile_user)
    
    # Get impact breakdown (if you have this function)
    try:
        from accounts.utils import get_impact_breakdown
        impact_breakdown = get_impact_breakdown(profile_user)
    except ImportError:
        impact_breakdown = None
    
    # Get user's recent tips
    recent_tips = Tip.objects.filter(
        author=profile_user,
        is_published=True
    ).order_by('-created_at')[:5]
    
    # Get all posts for the "Posts" tab
    posts = Tip.objects.filter(author=profile_user).order_by('-created_at')

    # Stats
    # Use the properties from the model if they exist, otherwise 0
    tips_count = getattr(profile_user, 'tips_count', 0)
    followers_count = profile_user.get_followers_count() if hasattr(profile_user, 'get_followers_count') else 0
    following_count = profile_user.get_following_count() if hasattr(profile_user, 'get_following_count') else 0
    impact_score = getattr(profile_user, 'impact_score', 0)
    
    context = {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'is_following': is_following,
        'tips_count': tips_count,
        'followers_count': followers_count,
        'following_count': following_count,
        'impact_score': impact_score,
        'impact_breakdown': impact_breakdown,
        'is_verified': getattr(profile_user, 'is_verified', False),
        'joined_date': profile_user.joined_date,
        'recent_tips': recent_tips,
        'posts': posts,
    }
    
    return render(request, 'accounts/profile.html', context)


# Alternative: Separate view for profile editing (if you want a dedicated page)
@login_required(login_url='accounts:login')
def edit_profile_view(request):
    """
    Dedicated profile editing page (optional - not needed if using inline editing)
    """

    if request.method == 'POST':
        form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )

        if form.is_valid():
            form.save()
            messages.success(request, '✓ Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f'{error}')
                    else:
                        field_name = field.replace('_', ' ').title()
                        messages.error(request, f'{field_name}: {error}')
    else:
        form = UserProfileForm(instance=request.user)

    context = {
        'form': form,
        'page_title': 'Edit Profile'
    }

    return render(request, 'accounts/edit_profile.html', context)


@login_required(login_url='accounts:login')
def profile_settings_view(request):
    """
    User account settings page
    Note: The settings are now integrated in the profile page sidebar
    This view can be used if you want a separate settings page
    """

    context = {
        'user': request.user,
    }

    return render(request, 'accounts/settings.html', context)


# Login View
def login_view(request):
    """
    User login
    """

    if request.user.is_authenticated:
        return redirect('home')  # Change 'home' to your home URL name

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')

                # Redirect to next parameter or home
                return redirect('/accounts/profile')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


# Signup View
def signup_view(request):
    """
    User registration
    """

    if request.user.is_authenticated:
        return redirect('accounts:profile')  

    if request.method == 'POST':
        form = SignupForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '✓ Account created successfully! Welcome to Green Lifestyle!')
            return redirect('accounts:profile')  #
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f'{error}')
                    else:
                        field_name = field.replace('_', ' ').title()
                        messages.error(request, f'{field_name}: {error}')
    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


# Logout View
@login_required(login_url='accounts:login')
def logout_view(request):
    """
    User logout
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')




# ============================================
# TOGGLE FOLLOW VIEW (AJAX)
# ============================================
@login_required(login_url='accounts:login')
@require_POST
def toggle_follow_view(request, username):
    """
    Toggle follow/unfollow for a user (AJAX endpoint).
    
    What this does:
    1. Gets the target user
    2. Checks if already following
    3. If following: Unfollow
    4. If not following: Follow
    5. Returns JSON response
    
    URL: /accounts/follow/<username>/
    Method: POST only
    Returns: JSON
    """
    
    user_to_follow = get_object_or_404(CustomUser, username=username)
    
    # Can't follow yourself
    if request.user == user_to_follow:
        return JsonResponse({'error': 'Cannot follow yourself'}, status=400)
    
    # Check if already following
    follow_obj = Follow.objects.filter(
        follower=request.user,
        following=user_to_follow
    ).first()
    
    if follow_obj:
        # Already following, so unfollow
        follow_obj.delete()
        is_following = False
    else:
        # Not following, so follow
        Follow.objects.create(
            follower=request.user,
            following=user_to_follow
        )
        is_following = True
    
    # Get updated counts
    followers_count = user_to_follow.get_followers_count()
    following_count = user_to_follow.get_following_count()
    
    return JsonResponse({
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count
    })


# ============================================
# FOLLOWERS LIST VIEW
# ============================================
@login_required(login_url='accounts:login')
def followers_list_view(request, username):
    """
    Show list of users following a specific user.
    
    URL: /accounts/<username>/followers/
    Template: accounts/followers_list.html
    """
    
    user = get_object_or_404(CustomUser, username=username)
    
    # Get followers queryset
    followers_qs = Follow.objects.filter(
        following=user
    ).select_related('follower').order_by('-created_at')
    
    # Pagination - Paginate the queryset FIRST
    paginator = Paginator(followers_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add follow status for each follower ON THE CURRENT PAGE ONLY
    # We can't modify the objects in page_obj directly easily if it's a queryset slice,
    # so we'll iterate and attach attributes, or use a list.
    # However, page_obj iterates over the sliced queryset.
    
    for follow in page_obj:
        # Check if current user is following this follower
        if request.user.is_authenticated and request.user != follow.follower:
            follow.is_followed_by_current_user = request.user.is_following(follow.follower)
        else:
            follow.is_followed_by_current_user = False
    
    context = {
        'profile_user': user,
        'page_obj': page_obj,
        'is_own_profile': user == request.user,
    }
    
    return render(request, 'accounts/followers_list.html', context)


# ============================================
# FOLLOWING LIST VIEW
# ============================================
@login_required(login_url='accounts:login')
def following_list_view(request, username):
    """
    Show list of users that a specific user is following.
    
    URL: /accounts/<username>/following/
    Template: accounts/following_list.html
    """
    
    user = get_object_or_404(CustomUser, username=username)
    
    # Get following queryset
    following_qs = Follow.objects.filter(
        follower=user
    ).select_related('following').order_by('-created_at')
    
    # Pagination - Paginate the queryset FIRST
    paginator = Paginator(following_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add is_following status for each user ON THE CURRENT PAGE ONLY
    for follow in page_obj:
        if request.user.is_authenticated:
            follow.is_following_current_user = request.user.is_following(follow.following)
        else:
            follow.is_following_current_user = False
    
    context = {
        'profile_user': user,
        'page_obj': page_obj,
        'is_own_profile': user == request.user,
    }
    
    return render(request, 'accounts/following_list.html', context)


@login_required(login_url='accounts:login')
def activity_history_view(request):
    """
    Show user's activity history and statistics.

    URL: /accounts/activity/
    Template: accounts/activity_history.html
    """

    # Get session activity
    session_activity = request.session.get('activity', {})

    # Get database activity logs
    activity_logs = UserActivity.objects.filter(
        user=request.user
    ).order_by('-date')[:30]  # Last 30 days

    # Calculate statistics
    total_visits = UserActivity.objects.filter(
        user=request.user
    ).aggregate(
        total_visits=models.Sum('visits_count'),
        total_pages=models.Sum('page_views'),
    )

    # Get today's activity
    today = timezone.now().date()
    today_activity = UserActivity.objects.filter(
        user=request.user,
        date=today
    ).first()

    # Calculate login streak
    login_streak = calculate_login_streak(request.user)

    # Get most viewed tips
    all_tips_viewed = []
    for log in activity_logs:
        all_tips_viewed.extend(log.tips_viewed)

    from collections import Counter
    most_viewed_tip_ids = Counter(all_tips_viewed).most_common(5)

    from tips.models import Tip
    most_viewed_tips = []
    for tip_id, count in most_viewed_tip_ids:
        try:
            tip = Tip.objects.get(id=tip_id)
            most_viewed_tips.append({'tip': tip, 'views': count})
        except Tip.DoesNotExist:
            pass

    context = {
        'session_activity': session_activity,
        'activity_logs': activity_logs,
        'total_visits': total_visits['total_visits'] or 0,
        'total_pages': total_visits['total_pages'] or 0,
        'today_activity': today_activity,
        'login_streak': login_streak,
        'most_viewed_tips': most_viewed_tips,
    }

    return render(request, 'accounts/activity_history.html', context)


def calculate_login_streak(user):
    """Calculate consecutive days user has logged in"""
    activities = UserActivity.objects.filter(
        user=user
    ).order_by('-date').values_list('date', flat=True)

    if not activities:
        return 0

    streak = 1
    today = timezone.now().date()

    # Check if user visited today or yesterday
    if activities[0] < today - timedelta(days=1):
        return 0

    for i in range(len(activities) - 1):
        diff = (activities[i] - activities[i + 1]).days
        if diff == 1:
            streak += 1
        elif diff > 1:
            break

    return streak

