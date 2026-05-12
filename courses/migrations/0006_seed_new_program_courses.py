# Data migration: add six academy programs to the course catalog.

import base64

from django.core.files.base import ContentFile
from django.db import migrations
from django.utils.text import slugify

# 1x1 transparent PNG (valid image for required ImageField)
PLACEHOLDER_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _course_rows():
    """Title, duration (hours), short description."""
    return [
        (
            "10 Days AI-Integrated Poster Designing",
            40.0,
            "A 10-day intensive covering poster layout, typography, and AI-assisted "
            "design workflows for print and digital campaigns.",
        ),
        (
            "10 Days AI-Integrated Mobile Video Editing",
            40.0,
            "A 10-day program focused on editing professional short-form video on mobile "
            "devices using modern apps and AI-powered tools.",
        ),
        (
            "Master Metalist",
            24.0,
            "Structured training to master core listing and catalog concepts used in "
            "creative and digital product workflows.",
        ),
        (
            "Master Networking",
            36.0,
            "Foundations through practical skills in computer networks, protocols, "
            "and real-world troubleshooting.",
        ),
        (
            "Digital Marketing",
            32.0,
            "SEO, social media, analytics, and campaign planning for brands and "
            "freelance practitioners.",
        ),
        (
            "Computer Graphics Designing Course",
            48.0,
            "Raster and vector graphics, composition, color theory, and industry "
            "tools for visual design projects.",
        ),
    ]


def seed_courses(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    Category = apps.get_model("courses", "Category")
    User = apps.get_model("users", "User")

    instructor = (
        User.objects.filter(is_superuser=True).first()
        or User.objects.filter(is_staff=True).first()
        or User.objects.order_by("pk").first()
    )
    if not instructor:
        return

    category, _ = Category.objects.get_or_create(
        slug="edufix-programs",
        defaults={
            "title": "Edufix Programs",
            "icon": "fa-layer-group",
        },
    )

    for title, duration_hours, description in _course_rows():
        slug = slugify(title)
        if Course.objects.filter(slug=slug).exists():
            continue
        thumb = ContentFile(PLACEHOLDER_PNG, name=f"{slug}.png")
        Course.objects.create(
            title=title,
            slug=slug,
            description=description,
            thumbnail=thumb,
            price="0.00",
            discounted_price=None,
            duration=duration_hours,
            instructor=instructor,
            category=category,
            status="published",
            seo_title=title[:100],
            seo_description=description[:300],
        )


def unseed_courses(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    slugs = [slugify(title) for title, _, __ in _course_rows()]
    Course.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0005_certificate_certificate_file"),
    ]

    operations = [
        migrations.RunPython(seed_courses, unseed_courses),
    ]
