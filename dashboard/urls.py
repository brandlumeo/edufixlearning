from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('my-courses/', views.my_courses, name='enrolled_courses'),
    path('settings/', views.settings_view, name='settings'),
    path('ai-tutor/', views.ai_tutor, name='ai_tutor'),
    path('assignments/', views.assignments_view, name='assignments'),
    path('admin-analytics/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-analytics/upload-class/', views.upload_class_view, name='upload_class'),
    path('admin-analytics/create-course/', views.create_course_view, name='create_course'),
    path('admin-analytics/create-assignment/', views.create_assignment_view, name='create_assignment'),
    path('admin-analytics/leads/create/', views.lead_create_view, name='lead_create'),
    path('admin-analytics/leads/<int:lead_id>/status/', views.lead_status_view, name='lead_status'),
    path('admin-analytics/leads/<int:lead_id>/update/', views.lead_update_view, name='lead_update'),
    path('admin-analytics/students/export-csv/', views.export_students_csv, name='export_students_csv'),
    path('admin-analytics/students/<int:user_id>/toggle-active/', views.student_toggle_active_view, name='student_toggle_active'),
    path('admin-analytics/batches/create/', views.batch_create_view, name='batch_create'),
    path('admin-analytics/batches/<int:batch_id>/edit/', views.batch_edit_view, name='batch_edit'),
    path('admin-analytics/batches/<int:batch_id>/delete/', views.batch_delete_view, name='batch_delete'),
    path('admin-analytics/batches/<int:batch_id>/assign-students/', views.batch_assign_students_view, name='batch_assign_students'),
    path('admin-analytics/submissions/<int:submission_id>/review/', views.submission_review_view, name='submission_review'),
    path('admin-analytics/certificates/issue/', views.certificate_issue_view, name='certificate_issue'),
    path('admin-analytics/certificates/<str:cert_uid>/approve/', views.certificate_approve_view, name='certificate_approve'),
    path('admin-analytics/stream-status/<str:video_id>/', views.stream_status_view, name='stream_status'),
    path('certificates/', views.certificates_view, name='certificates'),
]
