from django.contrib import admin
from .models import (
    Category, Course, Module, Lesson, Resource, Enrollment, 
    LessonProgress, Assignment, Submission, Certificate, 
    Notification, Announcement, Discussion, Question, Answer, Event
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'price', 'status', 'created_at')
    list_filter = ('status', 'category', 'instructor')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'instructor', 'category', 'description', 'thumbnail')
        }),
        ('Pricing', {
            'fields': ('price', 'discounted_price')
        }),
        ('Details', {
            'fields': ('status', 'duration')
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description')
        }),
    )

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order_index')
    list_filter = ('course',)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order_index', 'is_free_preview')
    list_filter = ('module__course', 'module')

admin.site.register(Resource)
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at')
    list_filter = ('course',)

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'is_completed', 'watched_at')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'deadline')

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'status', 'submitted_at')
    list_filter = ('status', 'assignment')

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'certificate_uid', 'issued_at', 'has_file')
    list_filter = ('course',)
    search_fields = ('certificate_uid', 'student__username', 'student__email')
    
    def has_file(self, obj):
        return bool(obj.certificate_file)
    has_file.boolean = True
    has_file.short_description = 'File Uploaded'
admin.site.register(Notification)
admin.site.register(Announcement)

@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'created_at')
    list_filter = ('course',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'lesson', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'lesson__module__course')

admin.site.register(Answer)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_time')
    list_filter = ('event_type',)
