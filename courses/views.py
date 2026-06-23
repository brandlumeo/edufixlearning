import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, FileResponse, HttpResponseForbidden
from django.contrib import messages
from .models import Course, Lesson, Category, Enrollment, LessonProgress, Module, Assignment, Submission, Certificate
from .forms import SubmissionForm
from django.utils import timezone
from .utils import generate_certificate_pdf
import json
import io

logger = logging.getLogger(__name__)

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
    
    # Find next lesson in the index order
    course_lessons = Lesson.objects.filter(
        module__course=course
    ).select_related('module').order_by('module__order_index', 'order_index')
    
    next_lesson = None
    lessons_list = list(course_lessons)
    for i, l in enumerate(lessons_list):
        if l.id == lesson.id:
            if i + 1 < len(lessons_list):
                next_lesson = lessons_list[i + 1]
            break
    
    context = {
        'course': course,
        'lesson': lesson,
        'modules': modules,
        'completed_lessons': completed_lessons,
        'assignment': assignment,
        'submission_form': submission_form,
        'user_submissions': user_submissions,
        'next_lesson': next_lesson,
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
    if request.GET.get('test') == 'ping':
        return HttpResponse("PONG - The server is running the new code!", status=200, content_type="text/plain")
    try:
        if request.user.is_staff:
            certificate = get_object_or_404(Certificate, certificate_uid=cert_uid)
        else:
            certificate = get_object_or_404(
                Certificate,
                certificate_uid=cert_uid,
                student=request.user,
                is_approved=True
            )

        custom_name = request.GET.get('name', '').strip()[:100]
        student_name = custom_name if custom_name else (
            getattr(certificate.student, 'full_name', None) or certificate.student.username
        )

        custom_course = request.GET.get('course_title', '').strip()[:150]
        course_name = custom_course if custom_course else certificate.course.title

        # Safely obtain the issue date
        issue_date_raw = getattr(certificate, 'issued_at', None)
        issue_date = (
            issue_date_raw.strftime('%d %B %Y')
            if issue_date_raw
            else timezone.now().strftime('%d %B %Y')
        )

        # ── Resolve template file ─────────────────────────────────────────────
        # Only pass a FieldFile if the physical file actually exists in storage,
        # otherwise production would get FileNotFoundError inside the PDF generator.
        def _safe_field_file(field_file):
            """Return field_file only if it has a name AND the file exists."""
            if not field_file:
                return None
            name = getattr(field_file, 'name', None)
            if not name:
                return None
            storage = getattr(field_file, 'storage', None)
            if storage:
                try:
                    if storage.exists(name):
                        return field_file
                except Exception:
                    pass
            return None

        template_file = None

        # 1) CertificateTemplate model (admin cert panel upload)
        try:
            ct_model = certificate.course.certificate_template_model
            template_file = _safe_field_file(
                ct_model.certificate_template if ct_model else None
            )
        except Exception:
            pass

        # 2) Course.certificate_template field
        if not template_file:
            template_file = _safe_field_file(
                getattr(certificate.course, 'certificate_template', None)
            )

        # 3) Per-student certificate_file (legacy)
        if not template_file:
            template_file = _safe_field_file(
                getattr(certificate, 'certificate_file', None)
            )

        buffer, uid = generate_certificate_pdf(
            student_name=student_name,
            course_name=course_name,
            issue_date=issue_date,
            template_file=template_file,
        )

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f'EDUFIX_Certificate_{cert_uid}.pdf'
        )

    except Exception as exc:
        import traceback
        error_trace = traceback.format_exc()
        logger.exception(
            "download_certificate failed: cert_uid=%s user=%s error=%s",
            cert_uid,
            getattr(request.user, 'username', 'unknown'),
            exc,
        )
        return HttpResponse(
            f"Certificate generation failed!\n\nID: {cert_uid}\nError details:\n{error_trace}",
            status=200,
            content_type="text/plain",
        )


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
