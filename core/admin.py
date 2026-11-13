from django.contrib import admin

# Register your models here.
from .models import Review, SiteConfiguration


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("student_name", "role", "rating", "is_active", "display_order", "created_at")
    list_editable = ("is_active", "display_order")
    list_filter = ("is_active", "rating")
    search_fields = ("student_name", "role", "review_text")


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ("maintenance_mode", "updated_at")
    fields = ("maintenance_mode", "maintenance_message")

    def has_add_permission(self, request):
        return not SiteConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
