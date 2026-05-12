from django.db import models
from django.conf import settings

class Batch(models.Model):
    STATUS_CHOICES = (
        ('upcoming', 'Upcoming'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    )
    MODE_CHOICES = (
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('hybrid', 'Hybrid'),
    )

    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='batches')
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, limit_choices_to={'is_instructor': True}, related_name='conducted_batches')
    name = models.CharField(max_length=100)
    batch_code = models.CharField(max_length=20, blank=True, help_text="Short ID/code e.g. PR-01")
    start_date = models.DateField()
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Last scheduled day of this batch (optional).",
    )
    schedule = models.CharField(max_length=200, help_text="e.g. Mon–Fri 10:00 AM – 12:00 PM")
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Room, campus, lab name, or physical address.",
    )
    online_meeting_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Zoom, Google Meet, Microsoft Teams, or other class link.",
    )
    total_seats = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='offline')
    total_classes = models.IntegerField(default=0)
    completed_classes = models.IntegerField(default=0)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='assigned_batches', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Batch"
        verbose_name_plural = "Batches"

    def __str__(self):
        return f"{self.course.title} - {self.name}"

    @property
    def progress_percent(self):
        if self.total_classes > 0:
            return min(int(self.completed_classes / self.total_classes * 100), 100)
        return 0

    @property
    def pending_classes(self):
        return max(self.total_classes - self.completed_classes, 0)

class Attendance(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=True)
    remark = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('batch', 'student', 'date')

class FeeRecord(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fee_records')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField()
    last_payment_date = models.DateField(null=True, blank=True)
    is_fully_paid = models.BooleanField(default=False)

    @property
    def pending_amount(self):
        return self.total_amount - self.amount_paid

    def __str__(self):
        return f"{self.student.username} - {self.course.title}"

class PlacementOutcome(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='placements')
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=100)
    placement_date = models.DateField()
    package_details = models.CharField(max_length=100, blank=True)
    is_freelance = models.BooleanField(default=False)
    testimonial = models.TextField(blank=True)

class AssetInventory(models.Model):
    CATEGORY_CHOICES = (
        ('hardware', 'Hardware/Lab'),
        ('software', 'Software License'),
        ('equipment', 'Other Equipment'),
    )
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    total_count = models.IntegerField()
    used_count = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default='Active')

    class Meta:
        verbose_name = "Asset Inventory"
        verbose_name_plural = "Asset Inventories"

    def __str__(self):
        return self.name

class Lead(models.Model):
    STATUS_CHOICES = (
        ('new', 'New Enquiry'),
        ('contacted', 'Contacted'),
        ('converted', 'Converted'),
        ('lost', 'Lost'),
    )
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    course_interested = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, related_name='leads')
    source = models.CharField(max_length=100, default='Website', help_text="e.g. Website, Instagram, Referral")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    notes = models.TextField(blank=True, help_text="Internal notes from staff")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def notes_plain(self):
        return (self.notes or "").replace("\r", " ").replace("\n", " ")

    def __str__(self):
        course_label = self.course_interested.title if self.course_interested else "General"
        return f"{self.name} - {course_label}"

class SupportTicket(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    )
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"#{self.id} - {self.subject}"
