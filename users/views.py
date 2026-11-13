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
from django.utils.crypto import get_random_string
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next', '')
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
                return render(request, 'registration/login.html', {'next': next_url})

            user = authenticate(request, username=email, password=password)
            if user:
                # Reset attempts on success
                user.login_attempts = 0
                user.locked_until = None
                user.save()

                # Issue JWT
                access_token = generate_access_token(user)
                refresh_token = generate_refresh_token(user)
                
                from django.utils.http import url_has_allowed_host_and_scheme
                safe_next = next_url if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}) else None
                response = redirect(safe_next) if safe_next else redirect('dashboard:home')
                
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

    return render(request, 'registration/login.html', {'next': next_url})

def logout_view(request):
    logout(request)
    response = redirect('login')
    # Match the cookie flags for reliable deletion
    response.delete_cookie('access_token', path='/', samesite='Lax')
    return response

def register_view(request):
    next_url = request.GET.get('next') or request.POST.get('next', '')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_verified = True # Auto-verify for local development
            user.save()
            
            # Send Verification Email (wrapped so email failures don't break registration)
            try:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                verification_link = f"{request.scheme}://{request.get_host()}/accounts/verify/{uid}/{token}/"
                password_link = f"{request.scheme}://{request.get_host()}/accounts/password-reset-confirm/{uid}/{token}/"

                subject = "Welcome to EduFix - verify your email & set your password"
                message = (
                f"Hi {user.full_name}, welcome to Edufix Learning Academy!\n\n"
                f"Please verify your email by clicking here: {verification_link}\n\n"
                f"You were signed up without a password so you could get straight to your course. "
                f"Set a password now so you can log back in anytime: {password_link}\n\n"
                f"(This is also your permanent set/reset-password link - you can always get a new one "
                f"from the 'Forgot Password?' link on the login page.)"
            )
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            except Exception:
                # Email sending failed — log it but don't block the user
                pass

            messages.success(request, "Welcome! Your account is ready.")
            # Log the user in immediately so they land straight on checkout
            # instead of being sent back to a separate login form.
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            # They were never asked to create a password (passwordless signup for
            # a faster checkout) - flag this session so a one-time "create your
            # password" popup shows on their next page load.
            request.session['needs_password_setup'] = True

            from django.utils.http import url_has_allowed_host_and_scheme
            safe_next = next_url if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}) else None
            response = redirect(safe_next) if safe_next else redirect('dashboard:home')

            access_token = generate_access_token(user)
            response.set_cookie(
                key='access_token',
                value=access_token,
                max_age=3600,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                path='/'
            )
            return response
    else:
        initial_email = request.GET.get('email', '')
        form = UserRegistrationForm(initial={'email': initial_email})
    
    return render(request, 'users/register.html', {'form': form, 'next': next_url})

def google_signin_view(request):
    """Verify a Google Identity Services ID token (posted from the
    'Sign in with Google' button) and log the user in, creating an
    account automatically the first time. No password is ever needed
    for accounts created this way."""
    if request.method != 'POST':
        return redirect('login')

    from google.oauth2 import id_token as google_id_token
    from google.auth.transport import requests as google_requests

    credential = request.POST.get('credential')
    next_url = request.POST.get('next', '')
    google_client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')

    try:
        idinfo = google_id_token.verify_oauth2_token(
            credential, google_requests.Request(), google_client_id
        )
    except Exception:
        messages.error(request, "Google sign-in failed. Please try again or use email.")
        return redirect(f'/accounts/register/?next={next_url}') if next_url else redirect('register')

    email = idinfo.get('email')
    full_name = idinfo.get('name') or (email.split('@')[0] if email else 'Edufix Student')

    if not email or not idinfo.get('email_verified'):
        messages.error(request, "Google sign-in failed. Please try again or use email.")
        return redirect(f'/accounts/register/?next={next_url}') if next_url else redirect('register')

    user, created = User.objects.get_or_create(
        email=email,
        defaults={'full_name': full_name, 'username': email, 'is_verified': True},
    )
    if created:
        user.set_password(get_random_string(48))
        user.save()

    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)

    from django.utils.http import url_has_allowed_host_and_scheme
    safe_next = next_url if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}) else None
    response = redirect(safe_next) if safe_next else redirect('dashboard:home')

    access_token = generate_access_token(user)
    response.set_cookie(
        key='access_token',
        value=access_token,
        max_age=3600,
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
        path='/'
    )
    return response


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save()

        try:
            send_mail(
                subject="Welcome to Edufix Learning Academy!",
                message=(
                    f"Hi {user.get_full_name() or user.username},\n\n"
                    f"Your email is verified and your Edufix Learning Academy account is now active.\n"
                    f"You can log in any time here: https://edufixlearning.com/accounts/login/\n\n"
                    f"If you have any questions, reach out to us at info@edufixlearning.com.\n\n"
                    f"Welcome aboard!\nEdufix Learning Academy"
                ),
                from_email=getattr(settings, 'NOTIFICATIONS_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass

        messages.success(request, "Email verified successfully! You can now login.")
        return redirect('login')
    else:
        messages.error(request, "Verification link is invalid or has expired.")
        return redirect('core:index')

from django.contrib.auth.views import PasswordResetView
import logging

class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    
    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Password reset email sending failed: {e}", exc_info=True)
            messages.error(
                self.request, 
                "Failed to send password reset email. This is likely due to incorrect or expired "
                "email server (SMTP) settings. Please check your credentials or try again later."
            )
            return self.form_invalid(form)



@login_required
def set_password_view(request):
    """
    Lets an already-logged-in user (typically someone who signed up through
    the passwordless flow) set a real password, without losing their session.
    Used by the "create your password" popup shown after signup.
    """
    next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard:home'
    if request.method == 'POST':
        pw1 = request.POST.get('password1', '')
        pw2 = request.POST.get('password2', '')
        if not pw1 or pw1 != pw2:
            messages.error(request, "Those passwords don't match. Please try again.")
        else:
            try:
                validate_password(pw1, user=request.user)
            except ValidationError as e:
                messages.error(request, " ".join(e.messages))
            else:
                request.user.set_password(pw1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                request.session['needs_password_setup'] = False
                messages.success(request, "Password created! You can now log in with your email and password anytime.")
    from django.utils.http import url_has_allowed_host_and_scheme
    safe_next = next_url if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}) else 'dashboard:home'
    if safe_next == 'dashboard:home':
        return redirect('dashboard:home')
    return redirect(safe_next)


@login_required
def dismiss_password_prompt_view(request):
    """Hides the "create your password" popup for the rest of this session."""
    request.session['needs_password_setup'] = False
    next_url = request.POST.get('next') or request.GET.get('next')
    from django.utils.http import url_has_allowed_host_and_scheme
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('dashboard:home')
