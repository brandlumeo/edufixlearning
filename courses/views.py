from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from .models import Course, Lesson, Category, Enrollment, LessonProgress, Module, Assignment, Submission, Certificate
from .forms import SubmissionForm
from django.utils import timezone
from .utils import generate_certificate_pdf
import json
import io

class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    
    def get_queryset(self):
        return Course.objects.filter(status='published')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        if self.request.user.is_authenticated:
            context['enrolled_course_ids'] = list(Enrollment.objects.filter(student=self.request.user).values_list('course_id', flat=True))
        else:
            context['enrolled_course_ids'] = []
        return context

class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Group lessons by modules
        context['modules'] = self.object.modules.prefetch_related('lessons').all()
        # Flat lessons list for curriculum display (ordered by module then lesson order)
        context['lessons'] = Lesson.objects.filter(
            module__course=self.object
        ).select_related('module').order_by('module__order_index', 'order_index')
        # Check enrollment
        context['is_enrolled'] = False
        if self.request.user.is_authenticated:
            context['is_enrolled'] = Enrollment.objects.filter(student=self.request.user, course=self.object).exists()
        return context

@login_required
def lesson_view(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check enrollment
    if not Enrollment.objects.filter(student=request.user, course=course).exists() and not request.user.is_staff:
        messages.error(request, "You must be enrolled to view this course.")
        return redirect('courses:course_detail', slug=course_slug)

    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    modules = course.modules.prefetch_related('lessons').all()
    
    # Handle Assignment Submission
    assignment = lesson.assignments.first()
    submission_form = SubmissionForm()
    
    if request.method == 'POST' and 'submit_assignment' in request.POST:
        if assignment:
            form = SubmissionForm(request.POST, request.FILES)
            if form.is_valid():
                submission = form.save(commit=False)
                submission.assignment = assignment
                submission.student = request.user
                submission.status = 'submitted'
                submission.save()
                messages.success(request, "Assignment submitted successfully!")
                return redirect('courses:lesson_view', course_slug=course_slug, lesson_id=lesson_id)

    # Get completed lessons list
    completed_lessons = LessonProgress.objects.filter(
        student=request.user, 
        is_completed=True
    ).values_list('lesson_id', flat=True)
    
    # Get existing submissions
    user_submissions = Submission.objects.filter(student=request.user, assignment__lesson=lesson)
    
    context = {
        'course': course,
        'lesson': lesson,
        'modules': modules,
        'completed_lessons': completed_lessons,
        'assignment': assignment,
        'submission_form': submission_form,
        'user_submissions': user_submissions,
    }
    return render(request, 'courses/lesson_view.html', context)

@login_required
def update_progress(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        lesson_id = data.get('lesson_id')
        is_completed = data.get('is_completed', False)
        
        lesson = get_object_or_404(Lesson, id=lesson_id)
        # Ensure user is enrolled
        if not Enrollment.objects.filter(student=request.user, course=lesson.module.course).exists():
            return JsonResponse({'error': 'Not enrolled'}, status=403)
            
        progress, created = LessonProgress.objects.get_or_create(
            student=request.user,
            lesson=lesson
        )
        progress.is_completed = is_completed
        progress.save()
        
        # Check for Course Completion (100%)
        course = lesson.module.course
        total_lessons = Lesson.objects.filter(module__course=course).count()
        completed_count = LessonProgress.objects.filter(student=request.user, lesson__module__course=course, is_completed=True).count()
        
        if total_lessons > 0 and completed_count == total_lessons:
            # Issue Certificate if not already issued
            if not Certificate.objects.filter(student=request.user, course=course).exists():
                import uuid
                uid = str(uuid.uuid4())[:8].upper()
                Certificate.objects.create(
                    student=request.user,
                    course=course,
                    certificate_uid=f"EDUFIX-{uid}"
                )
                return JsonResponse({'status': 'success', 'course_completed': True})
        
        return JsonResponse({'status': 'success', 'course_completed': False})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def download_certificate(request, cert_uid):
    certificate = get_object_or_404(Certificate, certificate_uid=cert_uid, student=request.user)
    
    # If the admin has uploaded a custom certificate file, serve that instead
    if certificate.certificate_file:
        return FileResponse(certificate.certificate_file.open('rb'), as_attachment=True, filename=f"EDUFIX_Certificate_{cert_uid}.{certificate.certificate_file.name.split('.')[-1]}")
    
    custom_name = request.GET.get('name', '').strip()[:100]  # Limit length for PDF safety
    student_name = custom_name if custom_name else (certificate.student.full_name or certificate.student.username)
    
    buffer, uid = generate_certificate_pdf(
        student_name=student_name,
        course_name=certificate.course.title,
        issue_date=certificate.issued_at.strftime('%d %B %Y')
    )
    
    return FileResponse(buffer, as_attachment=True, filename=f'EDUFIX_Certificate_{cert_uid}.pdf')

def verify_certificate(request, cert_uid):
    certificate = get_object_or_404(Certificate, certificate_uid=cert_uid)
    return render(request, 'courses/verify_certificate.html', {'certificate': certificate})


@login_required
def stream_status_view(request, video_id):
    """
    AJAX endpoint — returns Cloudflare Stream processing status.
    Accessible by any logged-in user so the lesson page spinner can
    auto-reload once the video becomes ready.
    """
    from courses.utils_cf_stream import get_video_status
    import logging
    logger = logging.getLogger(__name__)
    try:
        info = get_video_status(video_id)
        # Update the DB record the moment Cloudflare says it's ready
        if info['ready']:
            Lesson.objects.filter(
                cf_stream_video_id=video_id,
                cf_stream_status='processing'
            ).update(cf_stream_status='ready')
        return JsonResponse(info)
    except Exception as e:
        logger.exception("Error polling stream status for %s", video_id)
        return JsonResponse({'ready': False, 'state': 'error', 'error': str(e)}, status=500)
