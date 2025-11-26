from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class Category(models.Model):
    # Organizing tips into different topics
    
    name = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="Category name (e.g., Recycling)"
    )
    
    slug = models.SlugField(
        max_length=100, 
        unique=True, 
        help_text="URL-friendly name (auto-generated)"
    )
    
    description = models.TextField(
        blank=True, 
        help_text="Brief description of this category"
    )
    
    icon = models.CharField(
        max_length=50, 
        default='🌱', 
        help_text="Emoji icon for this category"
    )
    
    # Approval system fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_categories',
        help_text="User who created this category"
    )
    
    is_approved = models.BooleanField(
        default=False,
        help_text="Whether this category is approved for use"
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_categories',
        help_text="Moderator/Admin who approved this category"
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this category was approved"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        status = " (Pending)" if not self.is_approved else ""
        return f"{self.name}{status}"
    
    def save(self, *args, **kwargs):
        # Auto-generating slug and handling auto-approval
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Auto-approving if created by moderator/admin
        if self.created_by and not self.is_approved:
            if self.created_by.role in ['moderator', 'admin']:
                self.is_approved = True
                self.approved_by = self.created_by
                from django.utils import timezone
                self.approved_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        # Returning URL to view tips in this category
        return reverse('tips:category_detail', kwargs={'slug': self.slug})
    
    def get_tips_count(self):
        # Returning count of approved tips in this category
        return self.tips.filter(is_published=True).count()
    
    def approve(self, approved_by_user):
        # Approving this category
        from django.utils import timezone
        self.is_approved = True
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()


class Tip(models.Model):
    # Main Tip model for sharing eco-friendly advice

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tips', help_text="User who created this tip")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='tips', help_text="Category this tip belongs to")

    title = models.CharField(max_length=200, help_text="Catchy title for your tip")
    slug = models.SlugField(max_length=200, unique=True, help_text="URL-friendly version of title")
    content = models.TextField(help_text="Detailed explanation of your tip")
    image = models.ImageField(upload_to='tips/', null=True, blank=True, help_text="Optional image to illustrate your tip")

    is_published = models.BooleanField(default=True, help_text="Is this tip visible to everyone?")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tip"
        verbose_name_plural = "Tips"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.title} - by {self.author.username}"

    def save(self, *args, **kwargs):
        # Auto-generating unique slug from title
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            # Ensuring slug is unique
            while Tip.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # Returning URL to view this tip
        return reverse('tips:tip_detail', kwargs={'slug': self.slug})

    def get_likes_count(self):
        # Getting like count
        return self.likes.count()

    def get_comments_count(self):
        # Getting comment count
        return self.comments.count()

    def is_liked_by(self, user):
        # Checking if user liked this tip
        if user.is_authenticated:
            return self.likes.filter(user=user).exists()
        return False

    def get_bookmarks_count(self):
        # Getting bookmark count
        return self.bookmarks.count()

    def is_bookmarked_by(self, user):
        # Checking if user bookmarked this tip
        if user.is_authenticated:
            return self.bookmarks.filter(user=user).exists()
        return False


class Like(models.Model):
    # Tracking which users liked which tips

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes', help_text="User who liked the tip")
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='likes', help_text="The tip that was liked")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'tip']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} liked {self.tip.title}"


class Comment(models.Model):
    # Allowing users to comment on tips

    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='comments', help_text="The tip being commented on")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments', help_text="User who wrote this comment")
    content = models.TextField(help_text="Your comment")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.username} commented on {self.tip.title}"


class Bookmark(models.Model):
    # Allowing users to save tips for later

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks', help_text="User who bookmarked the tip")
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='bookmarks', help_text="The tip that was bookmarked")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'tip']
        ordering = ['-created_at']
        verbose_name = "Bookmark"
        verbose_name_plural = "Bookmarks"

    def __str__(self):
        return f"{self.user.username} bookmarked {self.tip.title}"


class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
