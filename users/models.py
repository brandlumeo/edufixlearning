from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator

class User(AbstractUser):
    # Full Name is already covered by first_name and last_name in AbstractUser, 
    # but we'll use a single field for 'Full Name' as requested.
    full_name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    email = models.EmailField(unique=True)
    phone_regex = RegexValidator(regex=r'^\d{10}$', message="Phone number must be entered as: '9999999999'. Up to 10 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=10, blank=True)
    
    is_verified = models.BooleanField(default=False)
    login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Custom User Fields
    is_instructor = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']

    def __str__(self):
        return self.email

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    date = models.DateField(auto_now_add=True)
    activity_type = models.CharField(max_length=50) # lesson_watch, assignment_submit, login
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ('user', 'date', 'activity_type')
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"
