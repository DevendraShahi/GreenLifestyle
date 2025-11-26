from django.urls import path
from django.contrib.auth import views as auth_views
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

    # Activity tracking
    path('activity/', views.activity_history_view, name='activity_history'),

    # Follow system
    path('follow/<str:username>/', views.toggle_follow_view, name='toggle_follow'),
    path('<str:username>/followers/', views.followers_list_view, name='followers_list'),
    path('<str:username>/following/', views.following_list_view, name='following_list'),

    # Password Reset 
    path('password-reset/', views.password_reset_view, name='password_reset'),
         
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/accounts/password-reset-complete/'
         ), 
         name='password_reset_confirm'),
         
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),

    # Password Change
    path('password-change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='accounts/password_change_form.html',
             success_url='/accounts/password-change/done/'
         ), 
         name='password_change'),
         
    path('password-change/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/password_change_done.html'
         ), 
         name='password_change_done'),

    # User profile (Keep this last to avoid conflicts)
    path('delete/', views.delete_account_view, name='delete_account'),
    path('<str:username>/', views.profile_view, name='profile'),
]
