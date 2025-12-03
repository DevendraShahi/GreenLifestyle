from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from tips.models import Tip, Category, Like, Comment
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def dashboard_view(request):
    """Admin dashboard with statistics."""
    
    # Basic counts
    total_users = User.objects.count()
    total_tips = Tip.objects.count()
    total_categories = Category.objects.count()
    
    # Engagement stats
    total_likes = Like.objects.count()
    total_comments = Comment.objects.count()
    
    # Recent activity (last 30 days)
    last_month = timezone.now() - timedelta(days=30)
    new_users = User.objects.filter(date_joined__gte=last_month).count()
    new_tips = Tip.objects.filter(created_at__gte=last_month).count()
    
    # Pending categories
    pending_categories = Category.objects.filter(is_approved=False).count()
    
    context = {
        'total_users': total_users,
        'total_tips': total_tips,
        'total_categories': total_categories,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'new_users': new_users,
        'new_tips': new_tips,
        'pending_categories': pending_categories,
        'page_title': 'Admin Dashboard'
    }
    
    return render(request, 'administration/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def user_list_view(request):
    """List all users."""
    users = User.objects.all().order_by('-date_joined')
    
    # Get recommended moderators (high impact, active, regular users)
    recommended_moderators = User.objects.filter(
        role='user',
        is_active=True
    ).order_by('-impact_score')[:3]
    
    context = {
        'users': users,
        'recommended_moderators': recommended_moderators
    }
    return render(request, 'administration/users/list.html', context)

@login_required
@user_passes_test(is_admin)
def user_edit_view(request, user_id):
    """Edit a user."""
    user = get_user_model().objects.get(id=user_id)
    
    if request.method == 'POST':
        from .forms import UserEditForm
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('administration:user_list')
    else:
        from .forms import UserEditForm
        form = UserEditForm(instance=user)
        
    return render(request, 'administration/users/form.html', {'form': form, 'target_user': user})

@login_required
@user_passes_test(is_admin)
def user_delete_view(request, user_id):
    """Delete a user."""
    user = get_user_model().objects.get(id=user_id)
    
    if request.method == 'POST':
        user.delete()
        return redirect('administration:user_list')
        
    return render(request, 'administration/users/confirm_delete.html', {'target_user': user})

@login_required
@user_passes_test(is_admin)
def tip_list_view(request):
    """List all tips."""
    tips = Tip.objects.select_related('author', 'category').order_by('-created_at')
    return render(request, 'administration/tips/list.html', {'tips': tips})

@login_required
@user_passes_test(is_admin)
def tip_edit_view(request, tip_id):
    """Edit a tip."""
    tip = Tip.objects.get(id=tip_id)
    
    if request.method == 'POST':
        from tips.forms import TipForm
        form = TipForm(request.POST, request.FILES, instance=tip)
        if form.is_valid():
            form.save()
            return redirect('administration:tip_list')
    else:
        from tips.forms import TipForm
        form = TipForm(instance=tip)
        
    return render(request, 'administration/tips/form.html', {'form': form, 'tip': tip})

@login_required
@user_passes_test(is_admin)
def tip_delete_view(request, tip_id):
    """Delete a tip."""
    tip = Tip.objects.get(id=tip_id)
    
    if request.method == 'POST':
        tip.delete()
        return redirect('administration:tip_list')
        
    return render(request, 'administration/tips/confirm_delete.html', {'tip': tip})

@login_required
@user_passes_test(is_admin)
def category_list_view(request):
    """List all categories."""
    categories = Category.objects.annotate(tips_count=Count('tips')).order_by('name')
    return render(request, 'administration/categories/list.html', {'categories': categories})

@login_required
@user_passes_test(is_admin)
def category_create_view(request):
    """Create a new category."""
    if request.method == 'POST':
        from tips.forms import CategoryForm
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.is_approved = True
            category.approved_by = request.user
            category.approved_at = timezone.now()
            category.save()
            return redirect('administration:category_list')
    else:
        from tips.forms import CategoryForm
        form = CategoryForm()
        
    return render(request, 'administration/categories/form.html', {'form': form, 'title': 'Create Category'})

@login_required
@user_passes_test(is_admin)
def category_edit_view(request, category_id):
    """Edit a category."""
    category = Category.objects.get(id=category_id)
    
    if request.method == 'POST':
        from tips.forms import CategoryForm
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('administration:category_list')
    else:
        from tips.forms import CategoryForm
        form = CategoryForm(instance=category)
        
    return render(request, 'administration/categories/form.html', {'form': form, 'title': 'Edit Category', 'category': category})

@login_required
@user_passes_test(is_admin)
def category_delete_view(request, category_id):
    """Delete a category."""
    category = Category.objects.get(id=category_id)
    
    if request.method == 'POST':
        category.delete()
        return redirect('administration:category_list')
        
    return render(request, 'administration/categories/confirm_delete.html', {'category': category})


# API Endpoints for Inline Updates
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

@login_required
@user_passes_test(is_admin)
@require_POST
def api_toggle_user_status(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        # Don't allow disabling yourself
        if user == request.user:
            return JsonResponse({'success': False, 'error': 'You cannot disable your own account.'})
            
        data = json.loads(request.body)
        is_active = data.get('is_active')
        
        user.is_active = is_active
        user.save()
        
        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@user_passes_test(is_admin)
@require_POST
def api_update_user_role(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        # Don't allow changing your own role
        if user == request.user:
            return JsonResponse({'success': False, 'error': 'You cannot change your own role.'})
            
        data = json.loads(request.body)
        role = data.get('role')
        
        if role not in ['user', 'moderator', 'admin']:
            return JsonResponse({'success': False, 'error': 'Invalid role'})
            
        user.role = role
        # Update Django permissions based on role
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role == 'moderator':
            user.is_staff = True
            user.is_superuser = False
        else:
            user.is_staff = False
            user.is_superuser = False
            
        user.save()
        
        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@user_passes_test(is_admin)
@require_POST
def api_toggle_tip_status(request, tip_id):
    try:
        tip = Tip.objects.get(id=tip_id)
        data = json.loads(request.body)
        is_published = data.get('is_published')
        
        tip.is_published = is_published
        tip.save()
        
        return JsonResponse({'success': True})
    except Tip.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tip not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@user_passes_test(is_admin)
@require_POST
def api_toggle_category_status(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
        data = json.loads(request.body)
        is_approved = data.get('is_approved')
        
        if is_approved and not category.is_approved:
            category.approve(request.user)
        else:
            category.is_approved = is_approved
            category.save()
        
        return JsonResponse({'success': True})
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
