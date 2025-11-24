from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import CustomUser, Follow, UserActivity

# Register CustomUser in the admin panel and use this class to manage it
@admin.register(CustomUser)

class CustomUserAdmin(admin.ModelAdmin):
    # Admin interface for managing users

    # Showing these columns when viewing users
    list_display = ['username', 'email', 'role', 'gender', 'education' , 'is_staff']

    # Adding filters on the right side
    list_filter = ['role', 'is_staff', 'is_active']

    # Allowing searching by username or email
    search_fields = ['username', 'email']


# ============================================
# FOLLOW ADMIN
# ============================================
@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """
    Manage follows in admin panel.
    """
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('follower', 'following')


# ============================================
# USER ACTIVITY ADMIN
# ============================================
@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """
    Manage user activity in admin.
    """
    list_display = ['get_user_display', 'date', 'visits_count', 'page_views', 'tips_viewed_count', 'last_activity']
    list_filter = ['date', 'user']
    search_fields = ['user__username', 'session_key']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'last_activity']

    def get_user_display(self, obj):
        if obj.user:
            return obj.user.username
        return f"Anonymous ({obj.session_key[:8]}...)"

    get_user_display.short_description = 'User'

    def tips_viewed_count(self, obj):
        return len(obj.tips_viewed)

    tips_viewed_count.short_description = 'Tips Viewed'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')
