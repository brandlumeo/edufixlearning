"""
Django settings for edufix_lms project — PRODUCTION (cPanel / edufixlearning.com)
DO NOT use this file for local development.
Upload this file to cPanel as: edufix_lms/settings.py
"""
import os
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set. Add it to your .env file.")

# Read DEBUG from .env (set DEBUG=False in production .env)
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'www.edufixlearning.com',
    'edufixlearning.com',
]

CSRF_TRUSTED_ORIGINS = [
    'https://edufixlearning.com',
    'https://www.edufixlearning.com',
]
# ──────────────────────────────────────────────────────────────────────────────


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local Apps
    'core',
    'courses',
    'users',
    'dashboard',
    'management',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'users.middleware.JWTAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'edufix_lms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'edufix_lms.wsgi.application'


# ── Database (MySQL — production) ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}
# ──────────────────────────────────────────────────────────────────────────────


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'users.User'

# JWT Configuration
JWT_AUTH = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=7),
}

# Password Reset Timeout (30 minutes in seconds)
PASSWORD_RESET_TIMEOUT = 1800

# Email Configuration (SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# ── Security headers ──────────────────────────────────────────────────────────
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_HTTPONLY = False       # JS needs to read the cookie for AJAX
SESSION_COOKIE_HTTPONLY = True

# Namecheap proxy handles SSL — tell Django to trust the forwarded proto header
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# Do NOT set SECURE_SSL_REDIRECT=True on Namecheap — the server already handles it
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0          # Disable HSTS until site is confirmed stable
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# ──────────────────────────────────────────────────────────────────────────────

LOGIN_REDIRECT_URL = 'dashboard:home'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'

# OpenAI API Key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Cloudflare
CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID', '')
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN', '')

# Allow large video uploads for Cloudflare Stream (500 MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024   # 500 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024   # 500 MB


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ── Static & Media files ──────────────────────────────────────────────────────
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
