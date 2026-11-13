from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re
from django.utils.crypto import get_random_string

User = get_user_model()

class UserRegistrationForm(forms.ModelForm):
    agree_terms = forms.BooleanField(required=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number']

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

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(get_random_string(48))
        # Set username to email since it's required to be unique by AbstractUser
        user.username = user.email
        if commit:
            user.save()
        return user
