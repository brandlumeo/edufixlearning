from django.contrib import admin
from .models import Batch, Attendance, FeeRecord, PlacementOutcome, AssetInventory, Lead, SupportTicket

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "course",
        "instructor",
        "start_date",
        "end_date",
        "schedule",
        "location",
        "total_seats",
        "is_active",
    )
    list_filter = ("is_active", "course")
    search_fields = ("name", "location", "schedule")
    filter_horizontal = ("students",)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('batch', 'student', 'date', 'is_present')
    list_filter = ('date', 'is_present', 'batch')

@admin.register(FeeRecord)
class FeeRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'total_amount', 'amount_paid', 'due_date', 'is_fully_paid')
    list_filter = ('is_fully_paid', 'due_date')
    search_fields = ('student__username', 'student__full_name')

@admin.register(PlacementOutcome)
class PlacementOutcomeAdmin(admin.ModelAdmin):
    list_display = ('student', 'company', 'position', 'placement_date')
    search_fields = ('student__username', 'company')

@admin.register(AssetInventory)
class AssetInventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'total_count', 'used_count', 'status')
    list_filter = ('category', 'status')

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'course_interested', 'source', 'status', 'created_at')
    list_filter = ('status', 'source')
    search_fields = ('name', 'email', 'phone')

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'subject', 'status', 'created_at', 'resolved_at')
    list_filter = ('status',)
    search_fields = ('subject', 'student__username', 'student__email')
