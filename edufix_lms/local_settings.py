from .settings import *  # noqa: F403
from .settings import BASE_DIR, MIDDLEWARE, STORAGES

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "tmp" / "edufix-local.sqlite3",
    },
}
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "edufix@localhost"
GOOGLE_OAUTH_CLIENT_ID = ""
MEDIA_ROOT = BASE_DIR / "tmp" / "local-media"
STATIC_ROOT = BASE_DIR / "tmp" / "local-static"
STORAGES = {
    **STORAGES,
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
MIDDLEWARE = ["edufix_lms.local_settings.local_browser_policy", *MIDDLEWARE]


def local_browser_policy(get_response):
    def middleware(request):
        response = get_response(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com "
            "https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com "
            "https://cdn.jsdelivr.net; "
            "img-src 'self' data: blob:; connect-src 'self'; frame-src 'self'; form-action 'self'"
        )
        return response

    return middleware
