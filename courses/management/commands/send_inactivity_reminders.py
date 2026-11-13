import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from courses.models import Enrollment, EmailLog, LessonProgress, Lesson


class Command(BaseCommand):
    help = (
        "Every 2 days, remind students who purchased a course but haven't "
        "finished it (or haven't started watching) to continue."
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

            completed_count = LessonProgress.objects.filter(
                student=user, lesson__module__course=course, is_completed=True
            ).count()
            if completed_count >= total_lessons:
                continue

            last_reminder = EmailLog.objects.filter(
                user=user, email_type='inactivity_reminder', course=course
            ).order_by('-sent_at').first()
            reference_time = last_reminder.sent_at if last_reminder else enrollment.enrolled_at
            if (now - reference_time).days < 2:
                continue

            progress_pct = int((completed_count / total_lessons) * 100) if total_lessons else 0
            course_url = f"https://edufixlearning.com/courses/{course.slug}/learn/"

            if completed_count == 0:
                progress_line = "You haven't started watching yet."
            else:
                progress_line = f"You're {progress_pct}% through the course."

            subject = f"Don't lose momentum on {course.title}"
            message = (
                f"Hi {user.full_name or user.username},\n\n"
                f"Just a friendly reminder about {course.title}  {progress_line}\n\n"
                f"Pick up where you left off: {course_url}\n\n"
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
                EmailLog.objects.create(user=user, email_type='inactivity_reminder', course=course)
                sent_count += 1
            except Exception:
                self.stderr.write(f"Failed to send inactivity reminder to {user.email}")

        self.stdout.write(f"Inactivity reminder emails sent: {sent_count}")
