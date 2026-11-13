from django.db import models

# Create your models here.


class Review(models.Model):
    # Student testimonial shown in the homepage "Student Success Stories" section.
    # Add, edit, hide, or reorder entries via the Django admin (/admin/) -- no code changes needed.
    student_name = models.CharField(max_length=100)
    role = models.CharField(max_length=150, blank=True, help_text="e.g. 'Freelance Video Editor', 'Graphic Designer'")
    review_text = models.TextField(help_text="The testimonial quote (shown in italics; quote marks are added automatically)")
    rating = models.PositiveSmallIntegerField(default=5, choices=[(i, str(i) + ' star' + ('s' if i != 1 else '')) for i in range(1, 6)])
    is_active = models.BooleanField(default=True, help_text="Uncheck to hide this review from the site without deleting it")
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return self.student_name + ' (' + str(self.rating) + ' star' + ('s' if self.rating != 1 else '') + ')'


class SiteConfiguration(models.Model):
    """Singleton row (id=1) used to drive site-wide controls from the admin panel."""
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(
        blank=True,
        default="We're currently performing scheduled maintenance and will be back online shortly. Thanks for your patience!",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return "Site Configuration"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
