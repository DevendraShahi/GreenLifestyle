

from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .models import CustomUser, Follow, UserActivity
from tips.models import Tip
from .forms import UserProfileForm, SignupForm, LoginForm


# Developed by Devendra
@login_required(login_url='accounts:login')
def profile_view(request, username=None):
    """Displaying user profile."""
    
    # Getting profile user
    if username is None:
        profile_user = request.user
    else:
        profile_user = get_object_or_404(CustomUser, username=username)
    
    is_own_profile = profile_user == request.user
    
    # Handling form submission
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
            # Showing errors
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f'{error}')
                    else:
                        field_name = field.replace('_', ' ').title()
                        messages.error(request, f'{field_name}: {error}')
    
    # Checking follow status
    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = request.user.is_following(profile_user)
    
    # Getting impact breakdown
    try:
        from accounts.utils import get_impact_breakdown
        impact_breakdown = get_impact_breakdown(profile_user)
    except ImportError:
        impact_breakdown = None
    
    # Getting recent tips
    recent_tips = Tip.objects.filter(
        author=profile_user,
        is_published=True
    ).order_by('-created_at')[:5]
    
    # Getting posts
    posts = Tip.objects.filter(author=profile_user).order_by('-created_at')

    # Getting stats
    tips_count = getattr(profile_user, 'tips_count', 0)
    followers_count = profile_user.followers_count
    following_count = profile_user.following_count
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


# Developed by Devendra
@login_required(login_url='accounts:login')
def edit_profile_view(request):
    """Handling profile editing."""

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


# Developed by Devendra
@login_required(login_url='accounts:login')
def profile_settings_view(request):
    """Displaying settings."""

    context = {
        'user': request.user,
    }

    return render(request, 'accounts/settings.html', context)


# Developed by Devendra
def login_view(request):
    """Handling login."""

    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_username()}!')
                return redirect('/accounts/profile')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


# Developed by Devendra
def signup_view(request):
    """Handling registration."""

    if request.user.is_authenticated:
        return redirect('accounts:profile')  

    if request.method == 'POST':
        form = SignupForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '✓ Account created successfully! Welcome to Green Lifestyle!')
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
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


# Developed by Devendra
def password_reset_view(request):
    
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            
            # Generate reset link components
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            # Redirect directly to password reset confirm page
            return redirect('accounts:password_reset_confirm', uidb64=uid, token=token)
            
        except CustomUser.DoesNotExist:
            messages.error(request, 'No user found with this email address.')
            
    return render(request, 'accounts/password_reset_form.html')


# Developed by Devendra
@login_required(login_url='accounts:login')
def logout_view(request):
    """Handling logout."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')


# Developed by Nandha and Priya
@login_required(login_url='accounts:login')
@require_POST
def toggle_follow_view(request, username):
    """Toggling follow status."""
    
    user_to_follow = get_object_or_404(CustomUser, username=username)
    
    # Checking self-follow
    if request.user == user_to_follow:
        return JsonResponse({'error': 'Cannot follow yourself'}, status=400)
    
    # Checking existing follow
    follow_obj = Follow.objects.filter(
        follower=request.user,
        following=user_to_follow
    ).first()
    
    if follow_obj:
        # Unfollowing
        follow_obj.delete()
        is_following = False
    else:
        # Following
        Follow.objects.create(
            follower=request.user,
            following=user_to_follow
        )
        is_following = True
    
    # Getting counts
    followers_count = user_to_follow.get_followers_count()
    following_count = user_to_follow.get_following_count()
    
    return JsonResponse({
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count
    })


# Developed by Nandha and Priya
@login_required(login_url='accounts:login')
def followers_list_view(request, username):
    """Displaying followers."""
    
    user = get_object_or_404(CustomUser, username=username)
    
    # Getting followers
    followers_qs = (Follow.objects.filter(
        following=user)
    .select_related('follower').order_by('-created_at'))
    
    # Paginating results
    paginator = Paginator(followers_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Adding status
    for follow in page_obj:
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


# Developed by Nandha and Priya
@login_required(login_url='accounts:login')
def following_list_view(request, username):
    """Displaying following."""
    
    user = get_object_or_404(CustomUser, username=username)
    
    # Getting following
    following_qs = Follow.objects.filter(
        follower=user
    ).select_related('following').order_by('-created_at')
    
    # Paginating results
    paginator = Paginator(following_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Adding status
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


# Developed by Devendra
@login_required(login_url='accounts:login')
def activity_history_view(request):
    """Displaying activity history."""

    # Getting session
    session_activity = request.session.get('activity', {}).copy()
    
    # Parse timestamps for display
    if 'first_visit' in session_activity:
        try:
            val = session_activity['first_visit']
            if isinstance(val, str):
                session_activity['first_visit'] = datetime.fromisoformat(val)
        except (ValueError, TypeError):
            pass
            
    if 'last_visit' in session_activity:
        try:
            val = session_activity['last_visit']
            if isinstance(val, str):
                session_activity['last_visit'] = datetime.fromisoformat(val)
        except (ValueError, TypeError):
            pass

    # Getting logs
    activity_logs = UserActivity.objects.filter(
        user=request.user
    ).order_by('-date')[:30]

    # Calculating stats
    total_visits = UserActivity.objects.filter(
        user=request.user
    ).aggregate(
        total_visits=models.Sum('visits_count'),
        total_pages=models.Sum('page_views'),
    )

    # Getting today's activity
    today = timezone.localtime(timezone.now()).date()
    today_activity = UserActivity.objects.filter(
        user=request.user,
        date=today
    ).first()

    # Calculating streak
    login_streak = calculate_login_streak(request.user)

    # Getting most viewed
    all_tips_viewed = []
    for log in activity_logs:
        all_tips_viewed.extend(log.tips_viewed)

    from collections import Counter
    most_viewed_tip_ids = Counter(all_tips_viewed).most_common(5)

    # Getting most viewed tips
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


# Developed by Devendra
def calculate_login_streak(user):
    """Calculating login streak."""
    activities = UserActivity.objects.filter(
        user=user
    ).order_by('-date').values_list('date', flat=True)

    if not activities:
        return 0

    streak = 1
    today = timezone.localtime(timezone.now()).date()

    # Checking recent visit
    if activities[0] < today - timedelta(days=1):
        return 0

    for i in range(len(activities) - 1):
        diff = (activities[i] - activities[i + 1]).days
        if diff == 1:
            streak += 1
        elif diff > 1:
            break

    return streak


# Developed by Devendra
@login_required(login_url='accounts:login')
def delete_account_view(request):
    """Handling account deletion."""
    
    if request.method == 'POST':
        user = request.user
        logout(request)  # Logout before deleting to avoid session issues
        user.delete()
        messages.success(request, 'Your account has been successfully deleted.')
        return redirect('core:home')
        
    return render(request, 'accounts/delete_account_confirm.html')
