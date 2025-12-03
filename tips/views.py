

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Tip, Category, Like, Comment, Bookmark
from .forms import TipForm, CommentForm
from django.views.decorators.http import require_POST
from accounts.models import UserActivity

from django.db.models import Q, Count
from django.core.paginator import Paginator

from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from accounts.utils import update_user_impact_score

# Developed by Krish
def tip_list_view(request):
    """Displaying tips."""

    tips = Tip.objects.filter(is_published=True, author__is_active=True).select_related('author', 'category').annotate(
        likes_count=Count('likes', distinct=True),
        comments_count=Count('comments', distinct=True)
    )

    # Filtering by category
    category_slug = request.GET.get('category')
    if category_slug:
        tips = tips.filter(category__slug=category_slug)

    # Searching tips
    search_query = request.GET.get('search')
    if search_query:
        tips = tips.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    # Filtering by date
    date_range = request.GET.get('date_range')
    if date_range == 'last_7_days':
        since = timezone.now() - timedelta(days=7)
        tips = tips.filter(created_at__gte=since)
    elif date_range == 'last_month':
        since = timezone.now() - timedelta(days=30)
        tips = tips.filter(created_at__gte=since)

    # Sorting tips
    sort_by = request.GET.get('sort_by')
    if sort_by == 'oldest':
        tips = tips.order_by('created_at')
    elif sort_by == 'most_liked':
        tips = tips.order_by('-likes_count', '-created_at')
    elif sort_by == 'most_commented':
        tips = tips.order_by('-comments_count', '-created_at')
    else:
        # Defaulting to newest
        tips = tips.order_by('-created_at')

    paginator = Paginator(tips, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Adding display names and interaction status
    for tip in page_obj:
        tip.author_display_name = tip.author.get_full_name() or tip.author.username
        
        if request.user.is_authenticated:
            tip.is_liked = tip.likes.filter(user=request.user).exists()
            tip.is_bookmarked = tip.bookmarks.filter(user=request.user).exists()
        else:
            tip.is_liked = False
            tip.is_bookmarked = False

    categories = Category.objects.filter(is_approved=True)

    # Getting stats
    total_tips = Tip.objects.filter(is_published=True, author__is_active=True).count()
    total_likes = Like.objects.count()

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_slug,
        'date_range': date_range,
        'sort_by': sort_by,
        'total_tips': total_tips,
        'total_likes': total_likes,
    }

    return render(request, 'tips/tip_list.html', context)


# Developed by Krish
def tip_detail_view(request, slug):
    """Displaying tip details."""

    tip = get_object_or_404(
        Tip.objects.select_related('author', 'category'),
        slug=slug
    )

    # Checking if tip is published or user is author
    if not tip.is_published and tip.author != request.user:
        # If not published and not author, return 404
        from django.http import Http404
        raise Http404("No Tip matches the given query.")

    # Tracking view
    UserActivity.log_activity(request, tip_id=tip.id)
    comments = tip.comments.select_related('author').order_by('-created_at')

    # Checking interactions
    is_liked = False
    is_bookmarked = False
    if request.user.is_authenticated:
        is_liked = tip.likes.filter(user=request.user).exists()
        is_bookmarked = tip.bookmarks.filter(user=request.user).exists()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to comment.')
            return redirect('accounts:login')

        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.tip = tip
            comment.author = request.user
            comment.save()

            # Updating impact
            update_user_impact_score(request.user)
            update_user_impact_score(tip.author)

            messages.success(request, '✓ Comment added successfully!')
            return redirect('tips:tip_detail', slug=tip.slug)
    else:
        comment_form = CommentForm()

    related_tips = Tip.objects.filter(
        category=tip.category,
        is_published=True,
        author__is_active=True
    ).exclude(
        id=tip.id
    ).order_by('-created_at')[:3]

    # Adding display names
    tip.author_display_name = tip.author.get_full_name() or tip.author.username
    
    for comment in comments:
        comment.author_display_name = comment.author.get_full_name() or comment.author.username

    context = {
        'tip': tip,
        'comments': comments,
        'comment_form': comment_form,
        'is_liked': is_liked,
        'is_bookmarked': is_bookmarked,
        'related_tips': related_tips,
    }

    return render(request, 'tips/tip_detail.html', context)


# Developed by Devendra
@login_required(login_url='accounts:login')
def create_tip_view(request):
    """Creating new tip."""

    if request.method == 'POST':
        # Handling submission
        form = TipForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            tip = form.save(commit=False)
            tip.author = request.user
            tip.is_published = form.cleaned_data.get('is_published', False)
            tip.save()

            messages.success(request, '✓ Tip created successfully!')
            return redirect('tips:tip_detail', slug=tip.slug)
        else:
            # Showing errors
            messages.error(request, '✗ Please correct the errors below.')
    else:
        # Showing form
        form = TipForm(user=request.user)

    context = {
        'form': form,
        'page_title': 'Create New Tip'
    }

    return render(request, 'tips/tip_form.html', context)


# Developed by Devendra
@login_required(login_url='accounts:login')
def edit_tip_view(request, slug):
    """Editing tip."""

    # Getting tip
    tip = get_object_or_404(Tip, slug=slug)

    # Checking permission
    if tip.author != request.user:
        messages.error(request, '✗ You can only edit your own tips.')
        return redirect('tips:tip_detail', slug=tip.slug)

    if request.method == 'POST':
        # Handling submission
        form = TipForm(request.POST, request.FILES, instance=tip, user=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, '✓ Tip updated successfully!')
            return redirect('tips:tip_detail', slug=tip.slug)
        else:
            messages.error(request, '✗ Please correct the errors below.')
    else:
        # Showing form
        form = TipForm(instance=tip, user=request.user)

    context = {
        'form': form,
        'tip': tip,
        'page_title': 'Edit Tip'
    }

    return render(request, 'tips/tip_form.html', context)


# Developed by Devendra
@login_required(login_url='accounts:login')
def delete_tip_view(request, slug):
    """Deleting tip."""

    tip = get_object_or_404(Tip, slug=slug)

    # Checking permission
    if tip.author != request.user:
        messages.error(request, '✗ You can only delete your own tips.')
        return redirect('tips:tip_detail', slug=tip.slug)

    if request.method == 'POST':
        # Confirming deletion
        tip.delete()
        messages.success(request, '✓ Tip deleted successfully.')
        return redirect('tips:tip_list')

    context = {
        'tip': tip
    }

    return render(request, 'tips/tip_confirm_delete.html', context)


# Developed by Nandha and Priya
@login_required(login_url='accounts:login')
@require_POST
def toggle_like_view(request, slug):
    """Toggling like status."""

    tip = get_object_or_404(Tip, slug=slug, is_published=True)

    # Checking existing like
    like, created = Like.objects.get_or_create(user=request.user, tip=tip)

    if not created:
        # Removing like
        like.delete()
        liked = False
    else:
        # Adding like
        liked = True

    # Getting count
    likes_count = tip.likes.count()

    return JsonResponse({
        'liked': liked,
        'likes_count': likes_count
    })


# Developed by Devendra
@login_required(login_url='accounts:login')
@require_POST
def delete_comment_view(request, comment_id):
    """Deleting comment."""

    comment = get_object_or_404(Comment, id=comment_id)
    tip_slug = comment.tip.slug

    # Checking permission
    if comment.author != request.user:
        messages.error(request, '✗ You can only delete your own comments.')
        return redirect('tips:tip_detail', slug=tip_slug)

    comment.delete()
    messages.success(request, '✓ Comment deleted successfully.')

    return redirect('tips:tip_detail', slug=tip_slug)


# Developed by Devendra
@login_required(login_url='accounts:login')
def my_tips_view(request):
    """Displaying user tips."""

    tips = Tip.objects.filter(
        author=request.user
    ).annotate(
        likes_count=Count('likes', distinct=True),
        comments_count=Count('comments', distinct=True)
    ).order_by('-created_at')

    # Paginating tips
    paginator = Paginator(tips, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Adding display names
    for tip in page_obj:
        tip.author_display_name = tip.author.get_full_name() or tip.author.username

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'tips/my_tips.html', context)


# Developed by Devendra
def category_detail_view(request, slug):
    """Displaying category tips."""

    category = get_object_or_404(Category, slug=slug)

    # Checking if category is approved
    if not category.is_approved:
        from django.http import Http404
        raise Http404("Category not found or pending approval.")

    tips = Tip.objects.filter(
        category=category,
        is_published=True,
        author__is_active=True
    ).select_related('author').annotate(
        likes_count=Count('likes', distinct=True),
        comments_count=Count('comments', distinct=True)
    ).order_by('-created_at')

    # Paginating tips
    paginator = Paginator(tips, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
    }

    return render(request, 'tips/category_detail.html', context)


# Developed by Nandha and Priya
@login_required(login_url='accounts:login')
@require_POST
def toggle_bookmark_view(request, slug):
    """Toggling bookmark status."""

    tip = get_object_or_404(Tip, slug=slug, is_published=True)

    # Checking existing bookmark
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, tip=tip)

    if not created:
        # Removing bookmark
        bookmark.delete()
        bookmarked = False
    else:
        # Adding bookmark
        bookmarked = True

    # Getting count
    bookmarks_count = tip.bookmarks.count()

    return JsonResponse({
        'bookmarked': bookmarked,
        'bookmarks_count': bookmarks_count
    })


# Developed by Nandha and Priya
@login_required(login_url='accounts:login')
def saved_tips_view(request):
    """Displaying saved tips."""

    # Getting bookmarks
    bookmarks = Bookmark.objects.filter(
        user=request.user
    ).select_related(
        'tip__author',
        'tip__category'
    ).annotate(
        likes_count=Count('tip__likes', distinct=True),
        comments_count=Count('tip__comments', distinct=True)
    ).order_by('-created_at')

    # Paginating bookmarks
    paginator = Paginator(bookmarks, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Adding display names
    for bookmark in page_obj:
        bookmark.tip.author_display_name = bookmark.tip.author.get_full_name() or bookmark.tip.author.username

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'tips/saved_tips.html', context)


# Developed by Devendra
@login_required(login_url='accounts:login')
def community_view(request):
    """Displaying community members."""
    User = get_user_model()
    
    # Getting all users except self and inactive users
    users = User.objects.exclude(id=request.user.id).filter(is_active=True).order_by('-date_joined')
    
    # Splitting into following and suggested
    following_users = []
    suggested_users = []
    
    for user in users:
        user.is_following = request.user.is_following(user)
        if user.is_following:
            following_users.append(user)
        else:
            suggested_users.append(user)
            
    context = {
        'following_users': following_users,
        'suggested_users': suggested_users,
    }
    
    return render(request, 'tips/community.html', context)


# Developed by Nandha and Priya
@login_required(login_url='accounts:login')
@require_POST
def toggle_follow_view(request, username):
    """Toggling follow status."""
    User = get_user_model()
    
    target_user = get_object_or_404(User, username=username)
    
    if request.user == target_user:
        return JsonResponse({'error': 'You cannot follow yourself.'}, status=400)
        
    if request.user.is_following(target_user):
        request.user.unfollow(target_user)
        is_following = False
    else:
        request.user.follow(target_user)
        is_following = True
        
    # Updating impact scores
    update_user_impact_score(request.user)
    update_user_impact_score(target_user)
        
    return JsonResponse({
        'is_following': is_following,
        'followers_count': target_user.get_followers_count()
    })