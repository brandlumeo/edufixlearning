from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re

User = get_user_model()

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    agree_terms = forms.BooleanField(required=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number', 'password']

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if len(full_name) < 2:
            raise ValidationError("Full name must be at least 2 characters.")
        return full_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one number.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        # Set username to email since it's required to be unique by AbstractUser
        user.username = user.email
        if commit:
            user.save()
        return user
