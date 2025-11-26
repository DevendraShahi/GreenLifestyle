from .models import CustomUser

def update_user_impact_score(user):
    """
    Recalculating and updating the user's impact score and stats.
    """
    if not user.is_authenticated:
        return

    # Calculate new values
    tips_count = user.tips.filter(is_published=True).count() if hasattr(user, 'tips') else 0
    
    # Check for correct related names for followers/following based on Follow model
    followers_count = 0
    if hasattr(user, 'followers_set'):
        followers_count = user.followers_set.count()
    elif hasattr(user, 'followers'):
        followers_count = user.followers.count()
        
    following_count = 0
    if hasattr(user, 'following_set'):
        following_count = user.following_set.count()
    elif hasattr(user, 'following'):
        following_count = user.following.count()
    
    impact_score = (tips_count * 2) + followers_count
    
    # Update the database directly
    CustomUser.objects.filter(pk=user.pk).update(
        tips_count=tips_count,
        followers_count=followers_count,
        following_count=following_count,
        impact_score=impact_score
    )
