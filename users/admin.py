from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import User, UserActivity
from courses.models import Course, Enrollment

class AdminUserCreationForm(UserCreationForm):
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(status='published'),
        required=False,
        help_text="Select a course to enroll this student immediately."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username', 'full_name', 'phone_number', 'is_instructor')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            course = self.cleaned_data.get('course')
            if course:
                Enrollment.objects.get_or_create(student=user, course=course)
        return user

class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1

class CustomUserAdmin(UserAdmin):
    model = User
    add_form = AdminUserCreationForm
    
    list_display = ['email', 'username', 'full_name', 'is_staff', 'is_verified', 'is_instructor']
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('full_name', 'phone_number', 'is_verified', 'is_instructor', 'profile_picture', 'bio')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'full_name', 'phone_number', 'is_instructor', 'course', 'password1', 'password2'),
        }),
    )
    inlines = [EnrollmentInline]

admin.site.register(User, CustomUserAdmin)

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'activity_type')
    list_filter = ('activity_type', 'date')
