import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import timezone

from courses.models import Course, Enrollment, EmailLog, LessonProgress, Lesson


class Command(BaseCommand):
    help = (
        "10 days after a student finishes a course, send a feedback request "
        "email that also recommends other courses."
    )

    def handle(self, *args, **options):
        now = timezone.now()
        sent_count = 0

        for enrollment in Enrollment.objects.select_related('student', 'course').all():
            user = enrollment.student
            course = enrollment.course
            if not user.email:
                continue

            total_lessons = Lesson.objects.filter(module__course=course).count()
            if total_lessons == 0:
                continue

            completed_qs = LessonProgress.objects.filter(
                student=user, lesson__module__course=course, is_completed=True
            )
            completed_count = completed_qs.count()
            if completed_count < total_lessons:
                continue

            completion_date = completed_qs.aggregate(last=Max('watched_at'))['last']
            if not completion_date or (now - completion_date).days < 10:
                continue

            already_sent = EmailLog.objects.filter(
                user=user, email_type='completion_feedback', course=course
            ).exists()
            if already_sent:
                continue

            other_courses = list(
                Course.objects.filter(status='published', price__gt=0)
                .exclude(id=course.id)
                .exclude(enrolled_students__student=user)
                .order_by('id')[:3]
            )
            recommendations = ""
            if other_courses:
                lines = [f"- {c.title} (Rs.{c.discounted_price or c.price})  https://edufixlearning.com/courses/{c.slug}/" for c in other_courses]
                recommendations = "\nYou might also like:\n" + "\n".join(lines) + "\n"

            subject = f"How was {course.title}? We'd love your feedback"
            message = (
                f"Hi {user.full_name or user.username},\n\n"
                f"Congratulations on completing {course.title}! We'd really appreciate your feedback  "
                f"it helps other students and helps us improve.\n\n"
                f"Leave a review here: https://edufixlearning.com/courses/{course.slug}/\n"
                f"{recommendations}\n"
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
                EmailLog.objects.create(user=user, email_type='completion_feedback', course=course)
                sent_count += 1
            except Exception:
                self.stderr.write(f"Failed to send completion feedback email to {user.email}")

        self.stdout.write(f"Completion feedback emails sent: {sent_count}")
