from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list'),
    path('update-progress/', views.update_progress, name='update_progress'),
    path('stream-status/<str:video_id>/', views.stream_status_view, name='stream_status'),
    path('certificate/download/<str:cert_uid>/', views.download_certificate, name='download_certificate'),
    path('certificate/verify/<str:cert_uid>/', views.verify_certificate, name='verify_certificate'),
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('<slug:course_slug>/lesson/<int:lesson_id>/', views.lesson_view, name='lesson_view'),
    path('<slug:slug>/checkout/', views.checkout_view, name='checkout'),
    path('<slug:slug>/razorpay/order/', views.razorpay_create_order, name='razorpay_create_order'),
    path('<slug:slug>/razorpay/verify/', views.razorpay_verify_payment, name='razorpay_verify_payment'),
        path('razorpay/webhook/', views.razorpay_webhook, name='razorpay_webhook'),
    path('<slug:slug>/review/submit/', views.submit_course_review, name='submit_review'),
]
