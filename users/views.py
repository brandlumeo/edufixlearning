from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from .utils import generate_access_token, generate_refresh_token
from .forms import UserRegistrationForm

User = get_user_model()

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        try:
            user = User.objects.get(email=email)
            
            # Check Account Lock
            if user.locked_until and user.locked_until > timezone.now():
                minutes_left = int((user.locked_until - timezone.now()).total_seconds() / 60)
                messages.error(request, f"Account locked. Try again in {minutes_left} minutes.")
                return render(request, 'registration/login.html')

            user = authenticate(request, username=email, password=password)
            if user:
                # Reset attempts on success
                user.login_attempts = 0
                user.locked_until = None
                user.save()

                # Issue JWT
                access_token = generate_access_token(user)
                refresh_token = generate_refresh_token(user)
                
                response = redirect('dashboard:home')
                
                # Set httpOnly cookies
                # Access token: 1 hour
                # Refresh token: 7 days if remember_me
                max_age = 3600 # 1 hour
                if remember_me:
                    max_age = 7 * 24 * 3600 # 7 days
                
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    max_age=max_age,
                    httponly=True,
                    secure=not settings.DEBUG, # Secure in production
                    samesite='Lax',
                    path='/'
                )
                
                # Also do a standard Django login for session fallback/compatibility
                login(request, user)
                
                return response
            else:
                # Failed attempt
                user = User.objects.get(email=email) # Reload
                user.login_attempts += 1
                if user.login_attempts >= 5:
                    user.locked_until = timezone.now() + timedelta(minutes=15)
                    messages.error(request, "Too many failed attempts. Account locked for 15 minutes.")
                else:
                    messages.error(request, "Invalid email or password.")
                user.save()
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")

    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    response = redirect('login')
    # Match the cookie flags for reliable deletion
    response.delete_cookie('access_token', path='/', samesite='Lax')
    return response

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_verified = True # Auto-verify for local development
            user.save()
            
            # Send Verification Email
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_link = f"{request.scheme}://{request.get_host()}/accounts/verify/{uid}/{token}/"
            
            subject = "Verify your EduFix Account"
            message = f"Hi {user.full_name}, please verify your email by clicking here: {verification_link}"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            
            messages.success(request, "Registration successful! Please check your email to verify your account.")
            return redirect('login')
    else:
        initial_email = request.GET.get('email', '')
        form = UserRegistrationForm(initial={'email': initial_email})
    
    return render(request, 'users/register.html', {'form': form})

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save()
        messages.success(request, "Email verified successfully! You can now login.")
        return redirect('login')
    else:
        messages.error(request, "Verification link is invalid or has expired.")
        return redirect('core:index')
