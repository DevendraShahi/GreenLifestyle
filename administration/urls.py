from django.urls import path
from . import views

app_name = 'administration'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    
    # Users
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:user_id>/edit/', views.user_edit_view, name='user_edit'),
    path('users/<int:user_id>/edit/', views.user_edit_view, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete_view, name='user_delete'),
    
    # Tips
    path('tips/', views.tip_list_view, name='tip_list'),
    path('tips/<int:tip_id>/edit/', views.tip_edit_view, name='tip_edit'),
    path('tips/<int:tip_id>/delete/', views.tip_delete_view, name='tip_delete'),
    
    # Categories
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/create/', views.category_create_view, name='category_create'),
    path('categories/<int:category_id>/edit/', views.category_edit_view, name='category_edit'),
    path('categories/<int:category_id>/delete/', views.category_delete_view, name='category_delete'),
    
    # API endpoints
    path('api/user/<int:user_id>/toggle-status/', views.api_toggle_user_status, name='api_toggle_user_status'),
    path('api/user/<int:user_id>/update-role/', views.api_update_user_role, name='api_update_user_role'),
    path('api/tip/<int:tip_id>/toggle-status/', views.api_toggle_tip_status, name='api_toggle_tip_status'),
    path('api/category/<int:category_id>/toggle-status/', views.api_toggle_category_status, name='api_toggle_category_status'),
]
