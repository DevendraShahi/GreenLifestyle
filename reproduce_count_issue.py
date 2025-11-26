
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GreenLifestyle.settings')
django.setup()

from django.contrib.auth import get_user_model
from tips.models import Tip, Like, Comment, Category
from django.db.models import Count

User = get_user_model()

def run():
    # Setup data
    user1, _ = User.objects.get_or_create(username='testuser1', email='test1@example.com')
    user2, _ = User.objects.get_or_create(username='testuser2', email='test2@example.com')
    
    category, _ = Category.objects.get_or_create(name='Test Category', slug='test-category')
    
    tip, created = Tip.objects.get_or_create(
        title='Test Tip for Counting',
        slug='test-tip-counting',
        author=user1,
        category=category,
        content='Content'
    )
    
    # Clear existing interactions
    Like.objects.filter(tip=tip).delete()
    Comment.objects.filter(tip=tip).delete()
    
    # Add 2 likes
    Like.objects.create(user=user1, tip=tip)
    Like.objects.create(user=user2, tip=tip)
    
    # Add 3 comments
    Comment.objects.create(tip=tip, author=user1, content='Comment 1')
    Comment.objects.create(tip=tip, author=user2, content='Comment 2')
    Comment.objects.create(tip=tip, author=user1, content='Comment 3')
    
    print(f"Actual Likes: {Like.objects.filter(tip=tip).count()}")
    print(f"Actual Comments: {Comment.objects.filter(tip=tip).count()}")
    
    # Query using the problematic annotation
    qs = Tip.objects.filter(id=tip.id).annotate(
        likes_count=Count('likes', distinct=True),
        comments_count=Count('comments', distinct=True)
    )
    
    annotated_tip = qs.first()
    print(f"Annotated Likes: {annotated_tip.likes_count}")
    print(f"Annotated Comments: {annotated_tip.comments_count}")
    
    if annotated_tip.likes_count != 2 or annotated_tip.comments_count != 3:
        print("ISSUE REPRODUCED: Counts are incorrect!")
    else:
        print("Counts are correct.")

if __name__ == '__main__':
    run()
