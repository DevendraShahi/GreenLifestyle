from django import forms
from .models import Tip, Category, Comment
from django.core.exceptions import ValidationError


class TipForm(forms.ModelForm):
    # Creating/editing tips with optional category creation
    
    # Optional fields for creating a new category
    new_category_name = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200',
            'placeholder': 'New category name...'
        }),
        help_text='Create a new category if none of the existing ones fit'
    )
    
    new_category_icon = forms.CharField(
        required=False,
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200',
            'placeholder': 'Enter emoji (e.g., 🌱 ♻️ 💡)'
        }),
        help_text='Emoji icon for the new category'
    )
    
    new_category_description = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200 resize-none',
            'rows': 2,
            'placeholder': 'Brief description of the category...'
        }),
        help_text='Describe what this category is about'
    )
    
    class Meta:
        model = Tip
        fields = ['title', 'content', 'category', 'image', 'is_published']
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200',
                'placeholder': 'Give your tip a catchy title...'
            }),
            
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200 resize-none',
                'rows': 8,
                'placeholder': 'Share your eco-friendly tip in detail...'
            }),
            
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200'
            }),
            
            'image': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 dark:file:bg-emerald-900/30 dark:file:text-emerald-400 dark:hover:file:bg-emerald-900/50 cursor-pointer transition-all duration-200',
                'accept': 'image/*'
            }),
            
            'is_published': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-emerald-600 bg-gray-100 border-gray-300 rounded focus:ring-emerald-500 dark:focus:ring-emerald-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Showing only approved categories in dropdown
        approved_categories = Category.objects.filter(is_approved=True).order_by('name')
        self.fields['category'].queryset = approved_categories
        self.fields['category'].required = False
        self.fields['category'].empty_label = "-- Select a category --"
        
        # Showing helpful message if no approved categories exist
        if not approved_categories.exists():
            self.fields['category'].empty_label = "-- No categories available, create one below --"
    
    def clean(self):
        # Validating that either existing category is selected OR new category is provided
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        new_category_name = cleaned_data.get('new_category_name', '').strip()
        
        # Checking if either category or new category name is provided
        if not category and not new_category_name:
            raise ValidationError('Please select an existing category or create a new one.')
        
        # Validating required fields if creating new category
        if new_category_name:
            new_category_icon = cleaned_data.get('new_category_icon', '').strip()
            
            if not new_category_icon:
                raise ValidationError('Please provide an emoji icon for the new category.')
            
            # Checking if category already exists
            if Category.objects.filter(name__iexact=new_category_name).exists():
                raise ValidationError(f'Category "{new_category_name}" already exists. Please select it from the dropdown.')
        
        return cleaned_data
    
    def save(self, commit=True):
        # Saving tip and creating new category if provided
        instance = super().save(commit=False)
        
        # Checking if user wants to create a new category
        new_category_name = self.cleaned_data.get('new_category_name', '').strip()
        
        if new_category_name:
            # Creating new category
            new_category = Category.objects.create(
                name=new_category_name,
                description=self.cleaned_data.get('new_category_description', '').strip(),
                icon=self.cleaned_data.get('new_category_icon', '🌱').strip(),
                created_by=self.user,
                is_approved=False
            )
            
            # Auto-approving if user is moderator or admin
            if self.user and hasattr(self.user, 'role') and self.user.role in ['moderator', 'admin']:
                from django.utils import timezone
                new_category.is_approved = True
                new_category.approved_by = self.user
                new_category.approved_at = timezone.now()
                new_category.save()
            
            instance.category = new_category
        
        if commit:
            instance.save()
        
        return instance


class CommentForm(forms.ModelForm):
    # Adding comments to tips
    
    class Meta:
        model = Comment
        fields = ['content']
        
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200 resize-none',
                'rows': 3,
                'placeholder': 'Share your thoughts...'
            })
        }


class CategoryForm(forms.ModelForm):
    # Creating/editing categories
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200',
                'placeholder': 'Category name (e.g., Recycling, Zero Waste)'
            }),
            
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200 resize-none',
                'rows': 4,
                'placeholder': 'Describe what this category is about...'
            }),
            
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200',
                'placeholder': 'Emoji icon (e.g., 🌱, ♻️, 💡, 🌍)'
            }),
        }
    
    def clean_name(self):
        # Validating category name
        name = self.cleaned_data.get('name')
        
        if not name:
            raise ValidationError('Category name is required.')
        
        name = name.strip()
        
        if len(name) < 3:
            raise ValidationError('Category name must be at least 3 characters long.')
        
        if len(name) > 100:
            raise ValidationError('Category name cannot exceed 100 characters.')
        
        # Checking for duplicate (excluding current instance if editing)
        if self.instance.pk:
            # Editing existing category
            if Category.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
                raise ValidationError(f'A category named "{name}" already exists.')
        else:
            # Creating new category
            if Category.objects.filter(name__iexact=name).exists():
                raise ValidationError(f'A category named "{name}" already exists.')
        
        return name
    
    def clean_icon(self):
        # Validating icon field
        icon = self.cleaned_data.get('icon')
        
        if not icon:
            raise ValidationError('Please provide an emoji icon for this category.')
        
        icon = icon.strip()
        
        if len(icon) > 10:
            raise ValidationError('Icon should be a single emoji (1-4 characters).')
        
        return icon
    
    def clean_description(self):
        # Validating description field
        description = self.cleaned_data.get('description', '').strip()
        
        if description and len(description) > 500:
            raise ValidationError('Description cannot exceed 500 characters.')
        
        return description


class CategoryRequestForm(forms.ModelForm):
    # Requesting new categories (for regular users)
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200 resize-none',
            'rows': 3,
            'placeholder': 'Why is this category needed? (Optional)'
        }),
        required=False,
        help_text='Explain why this category would be useful'
    )
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200',
                'placeholder': 'Category name (e.g., Sustainable Fashion)'
            }),
            
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200 resize-none',
                'rows': 3,
                'placeholder': 'Brief description of this category...'
            }),
            
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-800 dark:text-white transition-all duration-200',
                'placeholder': '🌱 (Choose an emoji)'
            }),
        }
    
    def clean_name(self):
        # Validating category name
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise ValidationError('Category name is required.')
        
        if len(name) < 3:
            raise ValidationError('Category name must be at least 3 characters.')
        
        # Checking if category already exists or is pending
        if Category.objects.filter(name__iexact=name).exists():
            raise ValidationError(f'A category named "{name}" already exists.')
        
        return name