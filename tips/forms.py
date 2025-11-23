from django import forms
from .models import Tip, Comment, Category
from django.core.exceptions import ValidationError


# ============================================
# TIP FORM
# ============================================
class TipForm(forms.ModelForm):
    """
    Form for creating and editing tips.

    This form handles:
    - Title validation
    - Content validation
    - Category selection
    - Image upload
    - Custom styling with Tailwind CSS

    How it works:
    1. User fills out form
    2. Django validates data
    3. If valid, save to database
    4. If invalid, show errors
    """

    class Meta:
        model = Tip
        fields = ['title', 'category', 'content', 'image', 'is_published']

        # Custom widgets for styling
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200',
                'placeholder': 'Enter a catchy title for your tip...',
                'maxlength': '200'
            }),

            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200 cursor-pointer'
            }),

            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200 resize-none',
                'rows': 8,
                'placeholder': 'Share your eco-friendly tip in detail...'
            }),

            'image': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-600 dark:text-gray-400 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 dark:file:bg-emerald-900/30 file:text-emerald-700 dark:file:text-emerald-400 hover:file:bg-emerald-100 dark:hover:file:bg-emerald-900/50 cursor-pointer transition-all duration-200',
                'accept': 'image/*'
            }),

            'is_published': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer'
            }),
        }

        # Custom labels
        labels = {
            '
            '
            'title': 'Tip Title',
            'category': 'Category',
            'content': 'Tip Content',
            'image': 'Upload Image (Optional)',
            'is_published': 'Publish immediately'
        }

        # Help text for fields
        help_texts = {
            'title': 'Make it catchy and descriptive (max 200 characters)',
            'content': 'Provide detailed, actionable advice',
            'image': 'Add an image to make your tip more engaging (JPG, PNG, max 5MB)',
            'is_published': 'Uncheck to save as draft'
        }

            # Optional field for creating a new category
    new_category_name = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none',
            'placeholder': 'Or create a new category...',
        }),
        help_text='Leave empty to use existing category from dropdown'
    )

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        new_category_name = cleaned_data.get('new_category_name')
        
        # If both are empty, require one
        if not category and not new_category_name:
            raise ValidationError('Please select an existing category or create a new one.')
        
        # If new category name is provided, check it doesn't already exist
        if new_category_name:
            if Category.objects.filter(name__iexact=new_category_name.strip()).exists():
                raise ValidationError(f'Category "{new_category_name}" already exists. Please select it from the dropdown.')
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # If a new category name was provided, create it
        new_category_name = self.cleaned_data.get('new_category_name')
        if new_category_name and new_category_name.strip():
            # Create the new category
            new_category, created = Category.objects.get_or_create(
                name=new_category_name.strip()
            )
            instance.category = new_category
        
        if commit:
            instance.save()
        return instance

    def clean_title(self):
        """
        Validate the title field.

        Checks:
        1. Title is not empty
        2. Title is at least 10 characters
        3. Title doesn't contain only special characters

        Returns: cleaned title
        Raises: ValidationError if invalid
        """
        title = self.cleaned_data.get('title')

        if not title:
            raise ValidationError('Title is required.')

        if len(title.strip()) < 10:
            raise ValidationError('Title must be at least 10 characters long.')

        # Check if title contains at least some alphanumeric characters
        if not any(c.isalnum() for c in title):
            raise ValidationError('Title must contain letters or numbers.')

        return title.strip()

    def clean_content(self):
        """
        Validate the content field.

        Checks:
        1. Content is not empty
        2. Content is at least 50 characters
        3. Content has substance (not just repeated characters)

        Returns: cleaned content
        Raises: ValidationError if invalid
        """
        content = self.cleaned_data.get('content')

        if not content:
            raise ValidationError('Content is required.')

        content = content.strip()

        if len(content) < 50:
            raise ValidationError('Content must be at least 50 characters long. Provide detailed advice.')

        # Check for repeated characters (spam detection)
        if len(set(content)) < 10:
            raise ValidationError('Content seems invalid. Please provide meaningful advice.')

        return content

    def clean_image(self):
        """
        Validate uploaded image.

        Checks:
        1. File size (max 5MB)
        2. File type (only images)

        Returns: cleaned image or None
        Raises: ValidationError if invalid
        """
        image = self.cleaned_data.get('image')

        if image:
            # Check file size (5MB = 5 * 1024 * 1024 bytes)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('Image file size cannot exceed 5MB.')

            # Check file extension
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            ext = image.name.split('.')[-1].lower()

            if ext not in valid_extensions:
                raise ValidationError(f'Unsupported file type. Allowed: {", ".join(valid_extensions)}')

        return image


# ============================================
# COMMENT FORM
# ============================================
class CommentForm(forms.ModelForm):
    """
    Form for adding comments to tips.

    Simple form with just content field.
    Used when users want to comment on a tip.

    How it works:
    1. User types comment
    2. Form validates (min 5 characters)
    3. If valid, save to 27

    """

    class Meta:
        model = Comment
        fields = ['content']

        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200 resize-none',
                'rows': 3,
                'placeholder': 'Share your thoughts or add your own experience...'
            }),
        }

        labels = {
            'content': 'Your Comment'
        }

    def clean_content(self):
        """
        Validate comment content.

        Checks:
        1. Not empty
        2. At least 5 characters
        3. Not just whitespace

        Returns: cleaned content
        Raises: ValidationError if invalid
        """
        content = self.cleaned_data.get('content')

        if not content:
            raise ValidationError('Comment cannot be empty.')

        content = content.strip()

        if len(content) < 3:
            raise ValidationError('Comment must be at least 3 characters long.')

        return content


# ============================================
# CATEGORY FORM (Admin/Moderator use)
# ============================================
class CategoryForm(forms.ModelForm):
    """
    Form for creating/editing categories.

    Usually used by admins or moderators.
    Regular users won't see this form.
    """

    class Meta:
        model = Category
        fields = ['name', 'description', 'icon']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200',
                'placeholder': 'Category name (e.g., Recycling)'
            }),

            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200 resize-none',
                'rows': 4,
                'placeholder': 'Brief description of this category...'
            }),

            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200',
                'placeholder': 'Emoji icon (e.g., 🌱, ♻️, 💡)'
            }),
        }

    def clean_name(self):
        """
        Validate category name.

        Checks:
        1. Not empty
        2. At least 3 characters
        3. Not duplicate (if creating new)

        Returns: cleaned name
        """
        name = self.cleaned_data.get('name')

        if not name:
            raise ValidationError('Category name is required.')

        name = name.strip()

        if len(name) < 3:
            raise ValidationError('Category name must be at least 3 characters.')

        # Check for duplicate (exclude current instance if editing)
        if self.instance.pk:
            # Editing existing category
            if Category.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
                raise ValidationError(f'Category "{name}" already exists.')
        else:
            # Creating new category
            if Category.objects.filter(name__iexact=name).exists():
                raise ValidationError(f'Category "{name}" already exists.')

        return name


    """
    User submits form
        ↓
    Django calls clean_<field>() for each field
        ↓
    If all validations pass → form.is_valid() returns True
        ↓
    Access cleaned  form.cleaned_data['title']
        ↓
    Save to database: form.save()

    """
