from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse


# ============================================
# CATEGORY MODEL
# ============================================
class Category(models.Model):
    """
    Category model for organizing tips into different topics.

    Example categories:
    - Recycling
    - Energy Saving
    - Sustainable Living
    - Zero Waste

    Fields explained:
    - name: The category name (e.g., "Recycling")
    - slug: URL-friendly version (e.g., "recycling")
    - description: What this category is about
    - icon: Emoji or icon for visual representation
    - created_at: When this category was created
    """
    
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
    
    # NEW FIELDS FOR APPROVAL SYSTEM
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
        """Auto-generate slug and handle auto-approval"""
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Auto-approve if created by moderator/admin
        if self.created_by and not self.is_approved:
            if self.created_by.role in ['moderator', 'admin']:
                self.is_approved = True
                self.approved_by = self.created_by
                from django.utils import timezone
                self.approved_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Returns the URL to view tips in this category"""
        return reverse('tips:category_detail', kwargs={'slug': self.slug})
    
    def get_tips_count(self):
        """Returns how many approved tips are in this category"""
        return self.tips.filter(is_published=True).count()
    
    def approve(self, approved_by_user):
        """Approve this category"""
        from django.utils import timezone
        self.is_approved = True
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()


# ============================================
# TIP MODEL
# ============================================
class Tip(models.Model):
    """
    Main Tip model - the core of our platform.

    A tip is a piece of advice shared by users about eco-friendly practices.

    Fields explained:
    - author: Who created this tip (linked to CustomUser)
    - category: Which category this tip belongs to
    - title: Short, catchy title
    - slug: URL-friendly version of title
    - content: The actual tip content (detailed advice)
    - image: Optional image to illustrate the tip
    - is_published: Whether tip is visible to everyone
    - created_at: When tip was created
    - updated_at: Last time tip was edited
    """

    # Relationship with User
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tips', help_text="User who created this tip")

    # Relationship with Category
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='tips', help_text="Category this tip belongs to")

    # Basic fields
    title = models.CharField(max_length=200, help_text="Catchy title for your tip")

    slug = models.SlugField(max_length=200, unique=True, help_text="URL-friendly version of title")

    content = models.TextField(help_text="Detailed explanation of your tip")

    image = models.ImageField(upload_to='tips/', null=True, blank=True, help_text="Optional image to illustrate your tip")

    # Status
    is_published = models.BooleanField(default=True, help_text="Is this tip visible to everyone?")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tip"
        verbose_name_plural = "Tips"
        ordering = ['-created_at']  # Newest first
        indexes = [
            models.Index(fields=['-created_at']),  # Speed up queries
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        """
        String representation: "5 Ways to Reduce Plastic - by John"
        """
        return f"{self.title} - by {self.author.username}"

    def save(self, *args, **kwargs):
        """
        Auto-generate unique slug from title.

        Example: "5 Ways to Reduce Plastic" → "5-ways-to-reduce-plastic"

        If slug exists, add number: "5-ways-to-reduce-plastic-2"
        """
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            # Ensure slug is unique
            while Tip.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Returns URL to view this tip.

        Example: /tips/5-ways-to-reduce-plastic/
        """
        return reverse('tips:tip_detail', kwargs={'slug': self.slug})

    def get_likes_count(self):
        """
        How many people liked this tip?

        Usage: tip.get_likes_count()
        Returns: Integer (e.g., 42)
        """
        return self.likes.count()

    def get_comments_count(self):
        """
        How many comments on this tip?

        Usage: tip.get_comments_count()
        Returns: Integer (e.g., 8)
        """
        return self.comments.count()

    def is_liked_by(self, user):
        """
        Check if a specific user liked this tip.

        Usage: tip.is_liked_by(request.user)
        Returns: True/False
        """
        if user.is_authenticated:
            return self.likes.filter(user=user).exists()
        return False

    def get_bookmarks_count(self):
        """
        How many people bookmarked this tip?

        Usage: tip.get_bookmarks_count()
        Returns: Integer (e.g., 15)
        """
        return self.bookmarks.count()

    def is_bookmarked_by(self, user):
        """
        Check if a specific user bookmarked this tip.

        Usage: tip.is_bookmarked_by(request.user)
        Returns: True/False
        """
        if user.is_authenticated:
            return self.bookmarks.filter(user=user).exists()
        return False

# ============================================
# LIKE MODEL
# ============================================
class Like(models.Model):
    """
    Like model - tracks which users liked which tips.

    This creates a "many-to-many" relationship between users and tips.

    Example: User "John" liked Tip "5 Ways to Reduce Plastic"

    Fields:
    - user: Who liked the tip
    - tip: Which tip was liked
    - created_at: When the like happened
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes', help_text="User who liked the tip")

    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='likes', help_text="The tip that was liked")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure user can only like a tip once
        unique_together = ['user', 'tip']
        ordering = ['-created_at']

    def __str__(self):
        """
        String: "John liked 5 Ways to Reduce Plastic"
        """
        return f"{self.user.username} liked {self.tip.title}"


# ============================================
# COMMENT MODEL
# ============================================
class Comment(models.Model):
    """
    Comment model - allows users to comment on tips.

    Users can share their thoughts, ask questions, or add their own experiences.

    Fields:
    - tip: Which tip this comment is on
    - author: Who wrote the comment
    - content: The actual comment text
    - created_at: When comment was posted
    - updated_at: Last edit time
    """

    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='comments', help_text="The tip being commented on")

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments', help_text="User who wrote this comment")

    content = models.TextField(
        help_text="Your comment"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Newest first

    def __str__(self):
        """
        String: "John commented on 5 Ways to Reduce Plastic"
        """
        return f"{self.author.username} commented on {self.tip.title}"



    # ============================================
    # BOOKMARK MODEL
    # ============================================
class Bookmark(models.Model):
    """
    Bookmark model - allows users to save tips for later.

    Similar to Like, but for saving/bookmarking tips.
    Users can quickly access their saved tips.

    Fields:
    - user: Who saved the tip
    - tip: Which tip was saved
    - created_at: When it was saved
    """

    user = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks', help_text="User who bookmarked the tip")

    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='bookmarks', help_text="The tip that was bookmarked")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure user can only bookmark a tip once
        unique_together = ['user', 'tip']
        ordering = ['-created_at']
        verbose_name = "Bookmark"
        verbose_name_plural = "Bookmarks"

    def __str__(self):
        """String: "Nandha bookmarked 5 Ways to Reduce Plastic" """
        return f"{self.user.username} bookmarked {self.tip.title}"



    """
            USER (CustomUser)
        ├── Can create many TIPS (author)
        ├── Can like many TIPS (through Like model)
        └── Can comment on many TIPS (through Comment model)
        
        CATEGORY
        └── Can have many TIPS (category)
        
        TIP
        ├── Belongs to one USER (author)
        ├── Belongs to one CATEGORY (category)
        ├── Can have many LIKES (through Like model)
        └── Can have many COMMENTS
        
    """
