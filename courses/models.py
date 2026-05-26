from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duration = models.FloatField(help_text="Duration in hours")
    
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
    cf_stream_video_id = models.CharField(max_length=200, blank=True, help_text="Cloudflare Stream video UID")
    cf_stream_status   = models.CharField(max_length=20, choices=CF_STATUS_CHOICES, default=CF_STATUS_NONE)
    duration_seconds = models.PositiveIntegerField(default=0)
    is_free_preview  = models.BooleanField(default=False)
    order_index      = models.PositiveIntegerField(default=0)
    content          = models.TextField(blank=True)

    class Meta:
        ordering = ['order_index']

    @property
    def stream_embed_url(self):
        if self.cf_stream_video_id:
            return f"https://iframe.cloudflarestream.com/{self.cf_stream_video_id}"
        return None

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

class Certificate(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    certificate_uid = models.CharField(max_length=50, unique=True)
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True, help_text="Upload custom certificate image or PDF")
    is_approved = models.BooleanField(default=False, help_text="Admin must approve before student can download")
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
