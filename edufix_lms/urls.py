from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from courses.sitemaps import CourseSitemap, StaticViewSitemap
from django.http import HttpResponse


def google_site_verification(request):
    return HttpResponse(
        "google-site-verification: google363f93697879ae76.html",
        content_type="text/plain",
    )


def google_site_verification_2(request):
    return HttpResponse(
        "google-site-verification: google38229da66ea7a6d5.html",
        content_type="text/plain",
    )

sitemaps = {
    'courses': CourseSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('google363f93697879ae76.html', google_site_verification),
    path('google38229da66ea7a6d5.html', google_site_verification_2),
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('users.urls')),
    path('courses/', include('courses.urls')),
    path('dashboard/', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
