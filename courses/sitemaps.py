from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Course


class CourseSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Course.objects.filter(status='published')

    def location(self, obj):
        return reverse('courses:course_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    changefreq = 'daily'
    priority = 1.0

    def items(self):
        return ['courses:course_list']

    def location(self, item):
        return reverse(item)
