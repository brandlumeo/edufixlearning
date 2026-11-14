import re
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver


def extract_youtube_id(value):
    """Accept a YouTube URL or raw 11-char video ID; return the ID or None."""
    if not value:
        return None
    value = value.strip()
    if re.fullmatch(r'[\w-]{11}', value):
        return value
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([\w-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)
    return None


class Category(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, help_text="FontAwesome icon name")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.title

class Course(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField() # Rich text or long text
    thumbnail = models.ImageField(upload_to='course_thumbnails/')
    certificate_template = models.ImageField(upload_to='certificate_templates/', blank=True, null=True, help_text="Upload certificate template image (JPG/PNG) for this course")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    offer_expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Real deadline for the current limited-time offer on this course. "
                   "When set (and in the future), a countdown bar shows on the course page. "
                   "Leave blank to hide the countdown -- never set a fake/past date just to create urgency."
    )
    duration = models.FloatField(help_text="Duration in hours")
    trainer_name = models.CharField(max_length=100, blank=True, help_text="Personal trainer/mentor name shown to enrolled students")
    trainer_whatsapp = models.CharField(max_length=20, blank=True, help_text="WhatsApp number with country code, e.g. +919876543210")
    
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    seo_title = models.CharField(max_length=100, blank=True)
    seo_description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def effective_price(self):
        """Actual price to charge/display: the discounted price when one is genuinely set, otherwise the regular price."""
        if self.discounted_price and self.discounted_price > 0:
            return self.discounted_price
        return self.price

    @property
    def original_price_display(self):
        """Original or pre-discount price (for strikethrough comparison)."""
        if self.discounted_price and self.price and self.price > self.discounted_price:
            return int(float(self.price))
        if self.slug == 'master-metalist':
            return 3999
        if self.slug in ('10-days-ai-integrated-mobile-video-editing', 'edufix-creative-mastery-class'):
            return 2999
        return int(float(self.effective_price))

    @property
    def discount_percentage(self):
        """Calculates discount percentage against original price."""
        try:
            orig = float(self.original_price_display)
            curr = float(self.effective_price)
            if orig > curr > 0:
                return round(((orig - curr) / orig) * 100)
        except (ValueError, TypeError, ZeroDivisionError):
            pass
        return 0


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    order_index = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order_index']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Lesson(models.Model):
    CF_STATUS_NONE       = 'none'
    CF_STATUS_PROCESSING = 'processing'
    CF_STATUS_READY      = 'ready'
    CF_STATUS_ERROR      = 'error'
    CF_STATUS_CHOICES = [
        (CF_STATUS_NONE,       'None'),
        (CF_STATUS_PROCESSING, 'Processing'),
        (CF_STATUS_READY,      'Ready'),
        (CF_STATUS_ERROR,      'Error'),
    ]

    module           = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title            = models.CharField(max_length=200)
    # Stores YouTube video ID/URL (preferred) or legacy Cloudflare Stream UID
    cf_stream_video_id = models.CharField(max_length=200, blank=True, help_text="YouTube video URL or ID (legacy: Cloudflare Stream UID)")
    cf_stream_status   = models.CharField(max_length=20, choices=CF_STATUS_CHOICES, default=CF_STATUS_NONE)
    duration_seconds = models.PositiveIntegerField(default=0)
    is_free_preview  = models.BooleanField(default=False)
    order_index      = models.PositiveIntegerField(default=0)
    content          = models.TextField(blank=True)

    class Meta:
        ordering = ['order_index']

    @property
    def youtube_id(self):
        return extract_youtube_id(self.cf_stream_video_id)

    @property
    def is_youtube(self):
        return bool(self.youtube_id)

    @property
    def stream_embed_url(self):
        if not self.cf_stream_video_id:
            return None
        yt_id = self.youtube_id
        if yt_id:
            return f"https://www.youtube-nocookie.com/embed/{yt_id}"
        # Legacy Cloudflare Stream fallback for old lessons
        return f"https://iframe.cloudflarestream.com/{self.cf_stream_video_id}"

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class Resource(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='resources')
    file_name = models.CharField(max_length=200)
    file = models.FileField(upload_to='lesson_resources/')
    file_type = models.CharField(max_length=50) # pdf, psd, mp4, etc.

class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrolled_students')
    payment_id = models.CharField(max_length=100, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

class LessonProgress(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    watched_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'lesson')
        verbose_name_plural = "Lesson Progresses"

class Assignment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateTimeField()
    allowed_types = models.CharField(max_length=200, help_text="Comma separated types e.g. JPG,PSD,MP4")

class Submission(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('needs_revision', 'Needs Revision'),
    )
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to='submissions/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

class CertificateTemplate(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='certificate_template_model')
    certificate_template = models.ImageField(upload_to='certificate_templates/', help_text="Upload certificate template image (JPG/PNG) for this course")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Template for {self.course.title}"

class Certificate(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    certificate_uid = models.CharField(max_length=50, unique=True)
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True, help_text="Upload custom certificate image or PDF")
    is_approved = models.BooleanField(default=False, help_text="Admin must approve before student can download")
    # Timestamp when the certificate is created (auto set)
    issued_at = models.DateTimeField(auto_now_add=True)


@receiver(post_save, sender=Enrollment)
def create_certificate_on_enrollment(sender, instance, created, **kwargs):
    if created:
        import uuid
        if not Certificate.objects.filter(student=instance.student, course=instance.course).exists():
            uid = f"CERT-{uuid.uuid4().hex[:8].upper()}"
            Certificate.objects.create(
                student=instance.student,
                course=instance.course,
                certificate_uid=uid,
                is_approved=False,
            )

class Notification(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50) # lesson_added, feedback_received, etc.
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Discussion(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='discussions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class Question(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='questions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    is_instructor_answer = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Event(models.Model):
    EVENT_TYPES = (
        ('live_session', 'Live Session'),
        ('assignment_deadline', 'Assignment Deadline'),
        ('class', 'Regular Class'),
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    link = models.URLField(blank=True, help_text="Link for live sessions")
    
    def __str__(self):
        return self.title


class PaymentSubmission(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_submissions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payment_submissions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    utr_reference = models.CharField(max_length=100, help_text="UPI transaction ID / UTR reference number")
    proof_image = models.ImageField(upload_to='payment_proofs/%Y/%m/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    admin_note = models.CharField(max_length=255, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='reviewed_payment_submissions'
    )

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student} - {self.course} ({self.status})"


class RazorpayPayment(models.Model):
    STATUS_CREATED = 'created'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_CREATED, 'Created'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='razorpay_payments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='razorpay_payments')
    razorpay_order_id = models.CharField(max_length=100)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_CREATED)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student} - {self.course} - {self.status}"


class CourseReview(models.Model):
    """A student's review of a course, submitted after finishing all lessons.
    Held for admin moderation before it can be shown on the public site.
    """
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_reviews')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)
    text = models.TextField(max_length=2000)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student} - {self.course} ({self.rating}, {self.status})"


class EmailLog(models.Model):
    """Tracks marketing/lifecycle emails sent to students so the
    promo drip, completion-feedback, and inactivity-reminder cron
    jobs never send duplicates."""
    EMAIL_TYPES = [
        ('promo', 'Promotional Offer'),
        ('completion_feedback', 'Course Completion Feedback'),
        ('inactivity_reminder', 'Inactivity Reminder'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='email_logs')
    email_type = models.CharField(max_length=30, choices=EMAIL_TYPES)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['user', 'email_type', 'sent_at'])]
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.user} - {self.email_type} - {self.sent_at:%Y-%m-%d}"
