from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


class CustomUser(AbstractUser):
    # Extending user model with profile information

    # Profile fields
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True, help_text="Upload a profile picture")
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
    location = models.CharField(max_length=100, blank=True, help_text="Where are you from?")
    website = models.URLField(blank=True, help_text="Your personal website or blog")
    eco_interests = models.CharField(max_length=500, blank=True, help_text="Your eco-friendly interests (e.g., recycling, energy saving)")

    # Stats fields
    tips_count = models.IntegerField(default=0, help_text="Number of tips shared")
    followers_count = models.IntegerField(default=0, help_text="Number of followers")
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

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
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

    @property
    def tips_count(self):
        # Getting number of tips shared by user
        return self.tips.count() if hasattr(self, 'tips') else 0

    @property
    def followers_count(self):
        # Getting number of followers
        return self.followers.count() if hasattr(self, 'followers') else 0

    @property
    def following_count(self):
        # Getting number of users being followed
        return self.following.count() if hasattr(self, 'following') else 0

    @property
    def impact_score(self):
        # Calculating user's impact score
        return (self.tips_count * 2) + self.followers_count

    def get_followers_count(self):
        # Getting count of users following this user
        return self.followers_set.count()
    
    def get_following_count(self):
        # Getting count of users this user is following
        return self.following_set.count()
    
    def is_following(self, user):
        # Checking if this user is following another user
        return self.following_set.filter(following=user).exists()
    
    def is_followed_by(self, user):
        # Checking if this user is followed by another user
        return self.followers_set.filter(follower=user).exists()
    
    def follow(self, user):
        # Following another user
        if self != user:
            Follow.objects.get_or_create(follower=self, following=user)
    
    def unfollow(self, user):
        # Unfollowing another user
        Follow.objects.filter(follower=self, following=user).delete()


class Follow(models.Model):
    # Enabling users to follow each other
    
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
        unique_together = ['follower', 'following']
        ordering = ['-created_at']
        verbose_name = "Follow"
        verbose_name_plural = "Follows"
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
    
    def save(self, *args, **kwargs):
        # Preventing users from following themselves
        if self.follower == self.following:
            raise ValueError("Users cannot follow themselves")
        super().save(*args, **kwargs)


class UserActivity(models.Model):
    # Tracking detailed user activity and engagement

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
        # Logging user activity
        today = timezone.now().date()

        if request.user.is_authenticated:
            # Handling logged in user
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
            # Handling anonymous user
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

        # Tracking tip views
        if tip_id and tip_id not in activity.tips_viewed:
            activity.tips_viewed.append(tip_id)

        activity.save()
        return activity

    def get_total_visits(self):
        # Getting total visits for this user
        if self.user:
            return UserActivity.objects.filter(user=self.user).aggregate(
                total=models.Sum('visits_count')
            )['total'] or 0
        return self.visits_count

