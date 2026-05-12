from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list'),
    path('update-progress/', views.update_progress, name='update_progress'),
    path('certificate/download/<str:cert_uid>/', views.download_certificate, name='download_certificate'),
    path('certificate/verify/<str:cert_uid>/', views.verify_certificate, name='verify_certificate'),
    path('video/<int:lesson_id>/', views.serve_video, name='serve_video'),
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('<slug:course_slug>/lesson/<int:lesson_id>/', views.lesson_view, name='lesson_view'),
]
