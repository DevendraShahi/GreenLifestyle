from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


class CustomUser(AbstractUser):
    # Extended user model with profile information

    # Profile fields
    profile_picture = models.ImageField( upload_to='profiles/', null=True, blank=True, help_text="Upload a profile picture")

    bio = models.TextField(max_length=500, blank=True, help_text="Tell us about yourself")

    gender = models.CharField(
        max_length=30,
        choices=[
            ('Male', 'Male'),
            ('Female', 'Female'),
            ('Other', 'Other'),
            ('Prefer not to say', 'Prefer not to say'),
        ],
        blank=True,
    )

    education = models.TextField(max_length=500, blank=True, help_text="Your literacy matters to us")

    location = models.CharField(max_length=100, blank=True, help_text="Where are you from?" )

    website = models.URLField(blank=True, help_text="Your personal website or blog"
    )

    eco_interests = models.CharField(max_length=500, blank=True, help_text="Your eco-friendly interests (e.g., recycling, energy saving)")

    # Stats fields
    tips_count = models.IntegerField(default=0, help_text="Number of tips shared")

    followers_count = models.IntegerField( default=0,help_text="Number of followers")

    following_count = models.IntegerField(default=0, help_text="Number of people following")

    impact_score = models.IntegerField(default=0, help_text="Environmental impact score")

    # Account status
    is_verified = models.BooleanField(default=False, help_text="Verified eco-contributor")

    joined_date = models.DateTimeField(auto_now_add=True)

    last_activity = models.DateTimeField(auto_now=True)

    ROLE_CHOICES = [
        ('user', 'Regular User'),
        ('moderator', 'Moderator'),
        ('admin', 'Administrator'),
    ]

    # Use in field
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,  # Use the class attribute
        default='user'
    )

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def get_role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role, 'User')

    # Optional: Add these helper properties to your CustomUser model
    # to make the stats work automatically


    # Add these methods to your CustomUser model in models.py:

    @property
    def tips_count(self):
        '''Get number of tips shared by user'''
        # Replace 'tips' with your actual related name
        return self.tips.count() if hasattr(self, 'tips') else 0

    @property
    def followers_count(self):
        '''Get number of followers'''
        # Replace 'followers' with your actual related name
        return self.followers.count() if hasattr(self, 'followers') else 0

    @property
    def following_count(self):
        '''Get number of users being followed'''
        # Replace 'following' with your actual related name
        return self.following.count() if hasattr(self, 'following') else 0

    @property
    def impact_score(self):
        '''Calculate user's impact score'''
        # Implement your impact score calculation logic
        # Example: tips_count * 2 + followers_count
        return (self.tips_count * 2) + self.followers_count



    def get_followers_count(self):
        """
        Get count of users following this user.
        
        Usage: user.get_followers_count()
        Returns: Integer (e.g., 150)
        """
        return self.followers_set.count()
    
    def get_following_count(self):
        """
        Get count of users this user is following.
        
        Usage: user.get_following_count()
        Returns: Integer (e.g., 200)
        """
        return self.following_set.count()
    
    def is_following(self, user):
        """
        Check if this user is following another user.
        
        Usage: current_user.is_following(other_user)
        Returns: True/False
        """
        return self.following_set.filter(following=user).exists()
    
    def is_followed_by(self, user):
        """
        Check if this user is followed by another user.
        
        Usage: current_user.is_followed_by(other_user)
        Returns: True/False
        """
        return self.followers_set.filter(follower=user).exists()
    
    def follow(self, user):
        """
        Follow another user.
        
        Usage: current_user.follow(other_user)
        """
        if self != user:
            Follow.objects.get_or_create(follower=self, following=user)
    
    def unfollow(self, user):
        """
        Unfollow another user.
        
        Usage: current_user.unfollow(other_user)
        """
        Follow.objects.filter(follower=self, following=user).delete()




# ============================================
# FOLLOW MODEL
# ============================================
class Follow(models.Model):
    """
    Follow model - enables users to follow each other.
    
    Creates a follower/following relationship between users.
    
    Example: User "John" follows User "Jane"
    - follower: John
    - following: Jane
    
    Fields:
    - follower: The user who is following
    - following: The user being followed
    - created_at: When the follow happened
    """
    
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following_set',
        help_text="User who is following"
    )
    
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers_set',
        help_text="User being followed"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Ensure user can't follow the same person twice
        unique_together = ['follower', 'following']
        ordering = ['-created_at']
        verbose_name = "Follow"
        verbose_name_plural = "Follows"
    
    def __str__(self):
        """String: "John follows Jane" """
        return f"{self.follower.username} follows {self.following.username}"
    
    def save(self, *args, **kwargs):
        """Prevent users from following themselves"""
        if self.follower == self.following:
            raise ValueError("Users cannot follow themselves")
        super().save(*args, **kwargs)


# ============================================
# USER ACTIVITY MODEL
# ============================================
class UserActivity(models.Model):
    """
    Track detailed user activity and engagement.

    Stores persistent activity data in database
    (session data is temporary, this is permanent)

    Fields:
    - user: The user (or None for anonymous)
    - session_key: Anonymous session identifier
    - date: Date of activity
    - visits_count: Number of visits on this date
    - page_views: Number of pages viewed
    - tips_viewed: List of tip IDs viewed
    - time_spent: Total time spent (in seconds)
    - last_activity: Last activity timestamp
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='activity_logs',
        help_text="User (null for anonymous users)"
    )

    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        help_text="Session key for anonymous users"
    )

    date = models.DateField(
        default=timezone.now,
        help_text="Date of activity"
    )

    visits_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of visits on this date"
    )

    page_views = models.PositiveIntegerField(
        default=0,
        help_text="Number of pages viewed"
    )

    tips_viewed = models.JSONField(
        default=list,
        blank=True,
        help_text="List of tip IDs viewed"
    )

    time_spent = models.PositiveIntegerField(
        default=0,
        help_text="Time spent in seconds"
    )

    last_activity = models.DateTimeField(
        auto_now=True,
        help_text="Last activity timestamp"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-last_activity']
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['session_key', 'date']),
        ]

    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.date}"
        return f"Anonymous ({self.session_key[:8]}) - {self.date}"

    @classmethod
    def log_activity(cls, request, tip_id=None):
        """
        Log user activity.

        Usage: UserActivity.log_activity(request, tip_id=5)
        """
        today = timezone.now().date()

        if request.user.is_authenticated:
            # Logged in user
            activity, created = cls.objects.get_or_create(
                user=request.user,
                date=today,
                defaults={
                    'visits_count': 1,
                    'page_views': 1,
                }
            )

            if not created:
                activity.visits_count += 1
                activity.page_views += 1
        else:
            # Anonymous user
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key

            activity, created = cls.objects.get_or_create(
                session_key=session_key,
                date=today,
                defaults={
                    'visits_count': 1,
                    'page_views': 1,
                }
            )

            if not created:
                activity.visits_count += 1
                activity.page_views += 1

        # Track tip views
        if tip_id and tip_id not in activity.tips_viewed:
            activity.tips_viewed.append(tip_id)

        activity.save()
        return activity

    def get_total_visits(self):
        """Get total visits for this user"""
        if self.user:
            return UserActivity.objects.filter(user=self.user).aggregate(
                total=models.Sum('visits_count')
            )['total'] or 0
        return self.visits_count

