from django.urls import path
from . import views

app_name = 'tips'

urlpatterns = [
    # ============================================
    # LIST & BROWSE
    # ============================================
    path('', views.tip_list_view, name='tip_list'),
    
    
    # ============================================
    # CREATE, EDIT, DELETE
    # ============================================
    path('create/', views.create_tip_view, name='create_tip'),
    path('<slug:slug>/edit/', views.edit_tip_view, name='edit_tip'),
    path('<slug:slug>/delete/', views.delete_tip_view, name='delete_tip'),
    
    
    # ============================================
    # INTERACTIONS
    # ============================================
    path('<slug:slug>/like/', views.toggle_like_view, name='toggle_like'),
    path('<slug:slug>/bookmark/', views.toggle_bookmark_view, name='toggle_bookmark'),
    path('comments/<int:comment_id>/delete/', views.delete_comment_view, name='delete_comment'),
    
    
    # ============================================
    # USER TIPS & SAVED
    # ============================================
    path('my-tips/', views.my_tips_view, name='my_tips'),
    path('saved/', views.saved_tips_view, name='saved_tips'),
    
    
    # ============================================
    # CATEGORIES
    # ============================================
    path('category/<slug:slug>/', views.category_detail_view, name='category_detail'),
    
    
    # ============================================
    # DETAIL
    # ============================================
    path('<slug:slug>/', views.tip_detail_view, name='tip_detail'),
]
