import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from courses.models import Course, EmailLog


class Command(BaseCommand):
    help = (
        "Send a rotating 7-day promo email to registered students who have "
        "not purchased any course yet (one course offer at a time)."
    )

    def handle(self, *args, **options):
        User = get_user_model()
        now = timezone.now()
        cutoff = now - datetime.timedelta(days=7)

        live_courses = list(Course.objects.filter(status='published', price__gt=0).order_by('id'))
        if not live_courses:
            self.stdout.write("No purchasable courses found; nothing to promote.")
            return

        candidates = (
            User.objects.filter(is_active=True, is_staff=False, is_superuser=False)
            .annotate(enrollment_count=Count('enrollments'))
            .filter(enrollment_count=0)
            .exclude(email='')
        )

        sent_count = 0
        for user in candidates:
            last_promo = EmailLog.objects.filter(user=user, email_type='promo').order_by('-sent_at').first()
            if last_promo and last_promo.sent_at > cutoff:
                continue

            promo_sent_total = EmailLog.objects.filter(user=user, email_type='promo').count()
            course = live_courses[promo_sent_total % len(live_courses)]

            display_price = course.discounted_price if course.discounted_price else course.price
            course_url = f"https://edufixlearning.com/courses/{course.slug}/"
            first_name = (user.full_name or user.username or 'there').split()[0]

            subject = f"{first_name}, a course pick for you: {course.title}"
            message = (
                f"Hi {user.full_name or user.username},\n\n"
                f"We noticed you created an Edufix Learning account but haven't started a course yet. "
                f"Here's one we think you'll like:\n\n"
                f"{course.title}\n"
                f"Price: Rs.{display_price}\n\n"
                f"Enroll now: {course_url}\n\n"
                f"If you have any questions, reach out to us at info@edufixlearning.com or WhatsApp +91 7034893345.\n\n"
                f"Edufix Learning Academy"
            )
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'NOTIFICATIONS_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                EmailLog.objects.create(user=user, email_type='promo', course=course)
                sent_count += 1
            except Exception:
                self.stderr.write(f"Failed to send promo email to {user.email}")

        self.stdout.write(f"Promo emails sent: {sent_count}")
