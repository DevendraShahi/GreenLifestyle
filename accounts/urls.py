from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Auth views
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile views
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/settings/', views.profile_settings_view, name='settings'),
    
    # Follow system
    path('follow/<str:username>/', views.toggle_follow_view, name='toggle_follow'),
    path('<str:username>/followers/', views.followers_list_view, name='followers_list'),
    path('<str:username>/following/', views.following_list_view, name='following_list'),
    
    # User profile (must be last)
    path('<str:username>/', views.profile_view, name='profile'),
]
