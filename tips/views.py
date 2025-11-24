from django.shortcuts import render

# Create your views here.

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


def tip_list_view(request):


    tips = Tip.objects.filter(is_published=True).select_related('author', 'category').annotate(
        likes_count=Count('likes'),
        comments_count=Count('comments')
    )

    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        tips = tips.filter(category__slug=category_slug)

    # Search keywords in title/content
    search_query = request.GET.get('search')
    if search_query:
        tips = tips.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    # Filter by date range
    date_range = request.GET.get('date_range')
    if date_range == 'last_7_days':
        since = timezone.now() - timedelta(days=7)
        tips = tips.filter(created_at__gte=since)
    elif date_range == 'last_month':
        since = timezone.now() - timedelta(days=30)
        tips = tips.filter(created_at__gte=since)

    # Sort by choice
    sort_by = request.GET.get('sort_by')
    if sort_by == 'oldest':
        tips = tips.order_by('created_at')
    elif sort_by == 'most_liked':
        tips = tips.order_by('-likes_count', '-created_at')
    elif sort_by == 'most_commented':
        tips = tips.order_by('-comments_count', '-created_at')
    else:
        # Default newest first
        tips = tips.order_by('-created_at')

    paginator = Paginator(tips, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add display names to tips
    for tip in page_obj:
        tip.author_display_name = tip.author.get_full_name() or tip.author.username

    categories = Category.objects.all()

    # Stats for sidebar
    total_tips = Tip.objects.filter(is_published=True).count()
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


# ============================================
# TIP DETAIL VIEW
# ============================================

def tip_detail_view(request, slug):
    """
        Show single tip with full details, comments, and like button.

        What this does:
        1. Gets tip by slug (URL-friendly ID)
        2. Loads all comments for this tip
        3. Checks if current user liked this tip
        4. Handles comment form submission
        5. Shows related tips (same category)

        URL: /tips/slug-of-tip/
        Template: tips/tip_detail.html

        Parameters:
        - slug: URL slug of the tip (e.g., "5-ways-to-reduce-plastic")

        Context:
        - tip: The tip object
        - comments: All comments on this tip
        - comment_form: Form to add new comment
        - is_liked: Whether user liked this tip
        - related_tips: Similar tips
        """

    """Show single tip with full details."""

    tip = get_object_or_404(
        Tip.objects.select_related('author', 'category'),
        slug=slug,
        is_published=True
    )

    # Track tip view in activity
    UserActivity.log_activity(request, tip_id=tip.id)
    comments = tip.comments.select_related('author').order_by('-created_at')

    # Check if user liked/bookmarked this tip
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

            # Update impact scores
            from accounts.utils import update_user_impact_score
            update_user_impact_score(request.user)
            update_user_impact_score(tip.author)

            messages.success(request, '✓ Comment added successfully!')
            return redirect('tips:tip_detail', slug=tip.slug)
    else:
        comment_form = CommentForm()

    related_tips = Tip.objects.filter(
        category=tip.category,
        is_published=True
    ).exclude(
        id=tip.id
    ).order_by('-created_at')[:3]

    # Add display names for template
    tip.author_display_name = tip.author.get_full_name() or tip.author.username
    
    # Add display names to comments
    for comment in comments:
        comment.author_display_name = comment.author.get_full_name() or comment.author.username

    context = {
        'tip': tip,
        'comments': comments,
        'comment_form': comment_form,
        'is_liked': is_liked,
        'is_bookmarked': is_bookmarked,  # Add this
        'related_tips': related_tips,
    }

    return render(request, 'tips/tip_detail.html', context)


# ============================================
# CREATE TIP VIEW
# ============================================
@login_required(login_url='accounts:login')
def create_tip_view(request):
    """
    Allow logged-in users to create new tips.

    What this does:
    1. Shows empty form (GET request)
    2. Validates and saves tip (POST request)
    3. Sets current user as author
    4. Redirects to tip detail page on success

    URL: /tips/create/
    Template: tips/tip_form.html

    Requires: User must be logged in (@login_required)

    Context:
    - form: TipForm instance
    - page_title: "Create New Tip"
    """

    if request.method == 'POST':
        # User submitted form
        form = TipForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            # Form is valid, save it
            tip = form.save(commit=False)  # Don't save to DB yet
            tip.author = request.user  # Set author to current user
            tip.save()  # Now save to database

            messages.success(request, '✓ Tip created successfully!')
            return redirect('tips:tip_detail', slug=tip.slug)
        else:
            # Form has errors
            messages.error(request, '✗ Please correct the errors below.')
    else:
        # Show empty form
        form = TipForm(user=request.user)

    context = {
        'form': form,
        'page_title': 'Create New Tip'
    }

    return render(request, 'tips/tip_form.html', context)


# ============================================
# EDIT TIP VIEW
# ============================================
@login_required(login_url='accounts:login')
def edit_tip_view(request, slug):
    """
    Allow users to edit their own tips.

    What this does:
    1. Gets the tip by slug
    2. Checks if user is the author (security)
    3. Shows pre-filled form with tip data
    4. Saves changes on submit

    URL: /tips/slug/edit/
    Template: tips/tip_form.html

    Security: Only tip author can edit

    Parameters:
    - slug: Tip's URL slug

    Context:
    - form: Pre-filled TipForm
    - tip: The tip being edited
    - page_title: "Edit Tip"
    """

    # Get tip or 404
    tip = get_object_or_404(Tip, slug=slug)

    # Security check: Only author can edit
    if tip.author != request.user:
        messages.error(request, '✗ You can only edit your own tips.')
        return redirect('tips:tip_detail', slug=tip.slug)

    if request.method == 'POST':
        # User submitted changes
        form = TipForm(request.POST, request.FILES, instance=tip, user=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, '✓ Tip updated successfully!')
            return redirect('tips:tip_detail', slug=tip.slug)
        else:
            messages.error(request, '✗ Please correct the errors below.')
    else:
        # Show pre-filled form
        form = TipForm(instance=tip, user=request.user)

    context = {
        'form': form,
        'tip': tip,
        'page_title': 'Edit Tip'
    }

    return render(request, 'tips/tip_form.html', context)


# ============================================
# DELETE TIP VIEW
# ============================================
@login_required(login_url='accounts:login')
def delete_tip_view(request, slug):
    """
    Allow users to delete their own tips.

    What this does:
    1. Gets the tip
    2. Checks if user is author (security)
    3. Shows confirmation page (GET)
    4. Deletes tip (POST)

    URL: /tips/slug/delete/
    Template: tips/tip_confirm_delete.html

    Security: Only tip author can delete

    Parameters:
    - slug: Tip's URL slug
    """

    tip = get_object_or_404(Tip, slug=slug)

    # Security check
    if tip.author != request.user:
        messages.error(request, '✗ You can only delete your own tips.')
        return redirect('tips:tip_detail', slug=tip.slug)

    if request.method == 'POST':
        # User confirmed deletion
        tip.delete()
        messages.success(request, '✓ Tip deleted successfully.')
        return redirect('tips:tip_list')

    context = {
        'tip': tip
    }

    return render(request, 'tips/tip_confirm_delete.html', context)


# ============================================
# LIKE/UNLIKE TIP VIEW (AJAX)
# ============================================
@login_required(login_url='accounts:login')
@require_POST
def toggle_like_view(request, slug):
    """
    Toggle like/unlike for a tip (AJAX endpoint).

    What this does:
    1. Gets the tip
    2. Checks if user already liked it
    3. If liked: Remove like
    4. If not liked: Add like
    5. Returns JSON response with new like count

    URL: /tips/slug/like/
    Method: POST only
    Returns: JSON

    Response format:
    {
        "liked": true/false,
        "likes_count": 42
    }

    Used with JavaScript for instant feedback.
    """

    tip = get_object_or_404(Tip, slug=slug, is_published=True)

    # Check if user already liked this tip
    like, created = Like.objects.get_or_create(user=request.user, tip=tip)

    if not created:
        # Like already exists, so unlike (delete it)
        like.delete()
        liked = False
    else:
        # New like was created
        liked = True

    # Get updated like count
    likes_count = tip.likes.count()

    # Return JSON response
    return JsonResponse({
        'liked': liked,
        'likes_count': likes_count
    })


# ============================================
# DELETE COMMENT VIEW
# ============================================
@login_required(login_url='accounts:login')
def delete_comment_view(request, comment_id):
    """
    Allow users to delete their own comments.

    What this does:
    1. Gets the comment
    2. Checks if user is author
    3. Deletes comment
    4. Redirects back to tip

    URL: /tips/comments/<id>/delete/
    Security: Only comment author can delete
    """

    comment = get_object_or_404(Comment, id=comment_id)
    tip_slug = comment.tip.slug

    # Security check
    if comment.author != request.user:
        messages.error(request, '✗ You can only delete your own comments.')
        return redirect('tips:tip_detail', slug=tip_slug)

    comment.delete()
    messages.success(request, '✓ Comment deleted successfully.')

    return redirect('tips:tip_detail', slug=tip_slug)


# ============================================
# USER'S TIPS VIEW
# ============================================
@login_required(login_url='accounts:login')
def my_tips_view(request):
    """
    Show all tips created by current user.

    What this does:
    1. Gets all tips by current user
    2. Shows both published and draft tips
    3. Adds pagination

    URL: /tips/my-tips/
    Template: tips/my_tips.html

    Context:
    - tips: User's tips (paginated)
    """

    tips = Tip.objects.filter(
        author=request.user
    ).annotate(
        likes_count=Count('likes'),
        comments_count=Count('comments')
    ).order_by('-created_at')

    # Pagination: 10 tips per page
    paginator = Paginator(tips, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add display names to tips
    for tip in page_obj:
        tip.author_display_name = tip.author.get_full_name() or tip.author.username

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'tips/my_tips.html', context)


# ============================================
# CATEGORY DETAIL VIEW
# ============================================
def category_detail_view(request, slug):
    """
    Show all tips in a specific category.

    What this does:
    1. Gets the category
    2. Gets all published tips in this category
    3. Adds pagination

    URL: /tips/category/slug/
    Template: tips/category_detail.html

    Parameters:
    - slug: Category's URL slug
    """

    category = get_object_or_404(Category, slug=slug)

    tips = Tip.objects.filter(
        category=category,
        is_published=True
    ).select_related('author').annotate(
        likes_count=Count('likes'),
        comments_count=Count('comments')
    ).order_by('-created_at')

    # Pagination
    paginator = Paginator(tips, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
    }

    return render(request, 'tips/category_detail.html', context)


# ============================================
# BOOKMARK/UNBOOKMARK TIP VIEW (AJAX)
# ============================================
@login_required(login_url='accounts:login')
@require_POST
def toggle_bookmark_view(request, slug):
    """
    Toggle bookmark/unbookmark for a tip (AJAX endpoint).

    What this does:
    1. Gets the tip
    2. Checks if user already bookmarked it
    3. If bookmarked: Remove bookmark
    4. If not bookmarked: Add bookmark
    5. Returns JSON response

    URL: /tips/slug/bookmark/
    Method: POST only
    Returns: JSON

    Response format:
    {
        "bookmarked": true/false,
        "bookmarks_count": 10
    }
    """

    tip = get_object_or_404(Tip, slug=slug, is_published=True)

    # Import Bookmark model
    from .models import Bookmark

    # Check if bookmark already exists
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, tip=tip)

    if not created:
        # Bookmark already exists, so remove it (unbookmark)
        bookmark.delete()
        bookmarked = False
    else:
        # New bookmark was created
        bookmarked = True

    # Get updated bookmark count
    bookmarks_count = tip.bookmarks.count()

    # Return JSON response
    return JsonResponse({
        'bookmarked': bookmarked,
        'bookmarks_count': bookmarks_count
    })


# ============================================
# SAVED TIPS VIEW
# ============================================
@login_required(login_url='accounts:login')
def saved_tips_view(request):
    """
    Show all tips bookmarked by current user.

    What this does:
    1. Gets all bookmarks by current user
    2. Extracts the tips from bookmarks
    3. Adds pagination
    4. Renders template

    URL: /tips/saved/
    Template: tips/saved_tips.html

    Context:
    - page_obj: Paginated bookmarks
    """

    # Get user's bookmarks with related tip data
    bookmarks = Bookmark.objects.filter(
        user=request.user
    ).select_related(
        'tip__author',
        'tip__category'
    ).annotate(
        likes_count=Count('tip__likes'),
        comments_count=Count('tip__comments')
    ).order_by('-created_at')

    # Pagination: 12 bookmarks per page
    paginator = Paginator(bookmarks, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add display names to bookmarked tips
    for bookmark in page_obj:
        bookmark.tip.author_display_name = bookmark.tip.author.get_full_name() or bookmark.tip.author.username

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'tips/saved_tips.html', context)


"""
    1. List View tip_list_view
        •	Shows multiple items
        •	Has pagination
        •	Has filtering/search
    2. Detail View tip_detail_view
        •	Shows single item
        •	Loads related data (comments, likes)
    3. Create View create_tip_view
        •	Shows empty form (GET)
        •	Saves new data (POST)
    4. Update View edit_tip_view
        •	Shows pre-filled form (GET)
        •	Updates existing data (POST)
    5. Delete View delete_tip_view
        •	Shows confirmation (GET)
        •	Deletes data (POST)
	6. AJAX View toggle_like_view
        •	Returns JSON (not HTML)
        •	Used with JavaScript
        •	Fast, no page reload
"""