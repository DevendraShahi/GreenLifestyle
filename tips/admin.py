from django.contrib import admin
from .models import Category, Tip, Like, Comment, Bookmark

"""
Admin Panel Configuration

This makes our models accessible in Django admin panel.
Visit: http://localhost:8000/admin/
"""


# ============================================
# CATEGORY ADMIN
# ============================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Customize how categories appear in admin.
    """
    list_display = ['name', 'slug', 'icon', 'get_tips_count', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}  # Auto-fill slug from name

    def get_tips_count(self, obj):
        """Show tip count in admin list"""
        return obj.tips.count()

    get_tips_count.short_description = 'Tips Count'


# ============================================
# TIP ADMIN
# ============================================
@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    """
    Customize how tips appear in admin.
    """
    list_display = ['title', 'author', 'category', 'is_published', 'get_likes_count', 'get_comments_count',
                    'created_at']
    list_filter = ['is_published', 'category', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'

    def get_likes_count(self, obj):
        return obj.likes.count()

    get_likes_count.short_description = 'Likes'

    def get_comments_count(self, obj):
        return obj.comments.count()

    get_comments_count.short_description = 'Comments'


# ============================================
# LIKE ADMIN
# ============================================
@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """
    Manage likes in admin.
    """
    list_display = ['user', 'tip', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'tip__title']


# ============================================
# COMMENT ADMIN
# ============================================
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Manage comments in admin.
    """
    list_display = ['author', 'tip', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['author__username', 'tip__title', 'content']

    def content_preview(self, obj):
        """Show first 50 characters of comment"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Content'


# ============================================
# BOOKMARK ADMIN
# ============================================
@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    """
    Manage bookmarks in admin.
    """
    list_display = ['user', 'tip', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'tip__title']
    date_hierarchy = 'created_at'

