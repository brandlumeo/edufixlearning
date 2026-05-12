import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edufix_lms.settings')
django.setup()

from users.forms import UserRegistrationForm
from django.contrib.auth import get_user_model

User = get_user_model()

data = {
    'full_name': 'Test User',
    'email': 'test_unique@example.com',
    'phone_number': '1234567890',
    'password': 'Password123',
    'confirm_password': 'Password123',
    'agree_terms': 'on'
}

form = UserRegistrationForm(data=data)
if form.is_valid():
    print("Form is valid!")
    user = form.save()
    print(f"User created: {user.email}")
else:
    print("Form is INVALID!")
    print(form.errors)
