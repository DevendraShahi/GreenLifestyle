from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser
from django.contrib.auth.forms import UserChangeForm
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError


class SignupForm(UserCreationForm):
    """Form for new users to register"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500',
            'placeholder': 'Enter your email'
        })
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500',
                'placeholder': 'Choose a username'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500',
            'placeholder': 'Create a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500',
            'placeholder': 'Confirm your password'
        })

    def clean_email(self):
        """Validate email isn't already used"""
        email = self.cleaned_data.get('email')

        if email and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")

        return email

    def clean_username(self):
        """Validate username"""
        username = self.cleaned_data.get('username')

        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters long.")

        if not username.isalnum() and '_' not in username:
            raise forms.ValidationError("Username can only contain letters, numbers, and underscores.")

        return username


class LoginForm(AuthenticationForm):
    """Form for users to login"""

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500',
            'placeholder': 'Enter your username'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500',
            'placeholder': 'Enter your password'
        })
    )


class UserProfileForm(forms.ModelForm):
    """Form for user profile editing"""

    class Meta:
        model = CustomUser
        fields = [
            'profile_picture',
            'first_name',
            'last_name',
            'email',
            'bio',
            'location',
            'website',
            'gender',
            'education',
            'eco_interests',
        ]
        widgets = {
            'profile_picture': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 dark:file:bg-emerald-900/30 dark:file:text-emerald-400 dark:hover:file:bg-emerald-900/50 cursor-pointer transition-all duration-200',
                'accept': 'image/*'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-700 dark:text-white transition-all duration-200',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-700 dark:text-white transition-all duration-200',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-700 dark:text-white transition-all duration-200',
                'placeholder': 'email@example.com'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-700 dark:text-white transition-all duration-200',
                'rows': 4,
                'placeholder': 'Tell us about yourself...',
                'maxlength': '500'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-700 dark:text-white transition-all duration-200',
                'placeholder': 'City, Country'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-700 dark:text-white transition-all duration-200',
                'placeholder': 'https://yourwebsite.com'
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-700 dark:text-white transition-all duration-200'
            }),
            'education': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-700 dark:text-white transition-all duration-200',
                'rows': 3,
                'placeholder': 'Your educational background...',
                'maxlength': '500'
            }),
            'eco_interests': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-gray-700 dark:text-white transition-all duration-200',
                'rows': 3,
                'placeholder': 'e.g., recycling, energy saving, sustainable living...'
            }),
        }

    def clean_email(self):
        """Validate email isn't already used by another user"""
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def clean_profile_picture(self):
        """Validate profile picture"""
        profile_picture = self.cleaned_data.get('profile_picture')

        if profile_picture:
            # Check file size (max 5MB)
            if profile_picture.size > 5 * 1024 * 1024:
                raise ValidationError('Image file size cannot exceed 5MB.')

            # Check file extension
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            ext = profile_picture.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise ValidationError(f'Unsupported file extension. Allowed: {", ".join(valid_extensions)}')

        return profile_picture

    def clean_bio(self):
        """Validate bio length"""
        bio = self.cleaned_data.get('bio')
        if bio and len(bio) > 500:
            raise ValidationError('Bio cannot exceed 500 characters.')
        return bio

    def clean_website(self):
        """Validate website URL"""
        website = self.cleaned_data.get('website')
        if website:
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website
        return website

    def clean_education(self):
        """Validate education length"""
        education = self.cleaned_data.get('education')
        if education and len(education) > 500:
            raise ValidationError('Education cannot exceed 500 characters.')
        return education