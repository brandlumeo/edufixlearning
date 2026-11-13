import logging
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse, FileResponse, HttpResponseForbidden
from django.contrib import messages
from .models import Course, Lesson, Category, Enrollment, LessonProgress, Module, Assignment, Submission, Certificate, PaymentSubmission, RazorpayPayment, CourseReview
from .forms import SubmissionForm, PaymentSubmissionForm
from django.utils import timezone
from .utils import generate_certificate_pdf, generate_upi_qr_base64, notify_admin_whatsapp
import razorpay
import json
import io
from django.views.decorators.csrf import csrf_exempt

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
        # Split courses into purchasable (live) vs unpriced (coming soon)
        # so the catalog doesn't mix dead-end "Coming Soon" cards into
        # the buyable grid.
        context['live_courses'] = [c for c in context['courses'] if c.price and c.price > 0]
        context['coming_soon_courses'] = [c for c in context['courses'] if not c.price]
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
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)

    # Check enrollment (free-preview lessons are viewable without enrollment)
    is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    if not is_enrolled and not request.user.is_staff and not lesson.is_free_preview:
        messages.error(request, "You must be enrolled to view this course.")
        return redirect('courses:course_detail', slug=course_slug)
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

        if not request.user.is_staff:
            if not CourseReview.objects.filter(student=request.user, course=certificate.course).exists():
                messages.info(request, "Please share a quick review of the course to unlock your certificate download.")
                return redirect(f"{reverse('dashboard:certificates')}?review_course={certificate.course.id}")

        custom_name = request.GET.get('name', '').strip()[:100]
        student_name = custom_name if custom_name else (
            getattr(certificate.student, 'full_name', None) or certificate.student.username
        )

        custom_course = request.GET.get('course_title', '').strip()[:150]
        course_name = custom_course if custom_course else certificate.course.title

        # Always use today's date so the certificate shows the download date
        issue_date = timezone.now().strftime('%d %B %Y')

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

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="EDUFIX_Certificate_{cert_uid}.pdf"'
        return response

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


@login_required(login_url='register')
def checkout_view(request, slug):
    course = get_object_or_404(Course, slug=slug)

    if Enrollment.objects.filter(student=request.user, course=course).exists():
        return redirect('courses:course_detail', slug=course.slug)

    if not course.price or course.price <= 0:
        Enrollment.objects.get_or_create(student=request.user, course=course)
        messages.success(request, f"You're enrolled in {course.title}!")
        return redirect('courses:course_detail', slug=course.slug)

    pending_submission = PaymentSubmission.objects.filter(
        student=request.user, course=course, status=PaymentSubmission.STATUS_PENDING
    ).first()

    if request.method == 'POST':
        if pending_submission:
            messages.info(request, "You already have a payment submitted for this course. Please wait for review.")
            return redirect('courses:checkout', slug=course.slug)
        form = PaymentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.student = request.user
            submission.course = course
            submission.amount = course.effective_price
            submission.save()
            try:
                review_url = f"{request.scheme}://{request.get_host()}/dashboard/admin-analytics/?tab=payments"
                notify_admin_whatsapp(
                    f"New payment submission on Edufix: {request.user.get_full_name() or request.user.username} "
                    f"paid Rs.{course.effective_price} for '{course.title}'. UTR: {submission.utr_reference}. Review: {review_url}"
                )
            except Exception:
                logger.exception("WhatsApp notify failed for submission %s", submission.pk)
            messages.success(
                request,
                "Thanks! Your payment has been submitted and is pending review. "
                "You'll get access to the course as soon as it's verified."
            )
            return redirect('courses:checkout', slug=course.slug)
    else:
        form = PaymentSubmissionForm()

    qr_code = None
    if not pending_submission:
        qr_code = generate_upi_qr_base64(course.effective_price, course.title)

    context = {
        'course': course,
        'form': form,
        'qr_code': qr_code,
        'upi_id': getattr(settings, 'UPI_ID', ''),
        'pending_submission': pending_submission,
        'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', ''),
    }
    return render(request, 'courses/checkout.html', context)


@login_required
@require_POST
def razorpay_create_order(request, slug):
    course = get_object_or_404(Course, slug=slug, status='published')

    if Enrollment.objects.filter(student=request.user, course=course).exists():
        return JsonResponse({'error': 'You are already enrolled in this course.'}, status=400)

    if not getattr(settings, 'RAZORPAY_KEY_ID', '') or not getattr(settings, 'RAZORPAY_KEY_SECRET', ''):
        return JsonResponse({'error': 'Online payment is not configured yet. Please use UPI or WhatsApp.'}, status=400)

    amount_paise = int(course.effective_price * 100)
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        order = client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'payment_capture': 1,
            'notes': {'course_slug': course.slug, 'student_id': str(request.user.id)},
        })
    except Exception:
        logger.exception("Razorpay order creation failed for course %s", course.slug)
        return JsonResponse({'error': 'Could not start payment. Please try again.'}, status=500)

    RazorpayPayment.objects.create(
        student=request.user,
        course=course,
        razorpay_order_id=order['id'],
        amount=course.effective_price,
        status=RazorpayPayment.STATUS_CREATED,
    )

    return JsonResponse({
        'order_id': order['id'],
        'amount': amount_paise,
        'currency': 'INR',
        'key': settings.RAZORPAY_KEY_ID,
        'name': 'Edufix Learning Academy',
        'description': course.title,
        'prefill_name': request.user.get_full_name() or request.user.username,
        'prefill_email': request.user.email,
    })


@login_required
@require_POST
def razorpay_verify_payment(request, slug):
    course = get_object_or_404(Course, slug=slug, status='published')
    order_id = request.POST.get('razorpay_order_id', '')
    payment_id = request.POST.get('razorpay_payment_id', '')
    signature = request.POST.get('razorpay_signature', '')

    payment_record = RazorpayPayment.objects.filter(
        student=request.user, course=course, razorpay_order_id=order_id
    ).order_by('-created_at').first()
    if not payment_record:
        return JsonResponse({'error': 'Payment record not found.'}, status=400)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature,
        })
    except razorpay.errors.SignatureVerificationError:
        payment_record.status = RazorpayPayment.STATUS_FAILED
        payment_record.save(update_fields=['status'])
        return JsonResponse({'error': 'Payment verification failed.'}, status=400)

    payment_record.razorpay_payment_id = payment_id
    payment_record.razorpay_signature = signature
    payment_record.status = RazorpayPayment.STATUS_PAID
    payment_record.paid_at = timezone.now()
    payment_record.save()

    Enrollment.objects.get_or_create(
        student=request.user, course=course,
        defaults={'payment_id': payment_id},
    )

    messages.success(request, f"Payment successful! You're enrolled in {course.title}.")

    return JsonResponse({
        'success': True,
        'redirect_url': reverse('courses:course_detail', kwargs={'slug': course.slug}),
        'amount': float(payment_record.amount),
    })


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """Server-side fallback for payment confirmation."""
    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
    signature = request.headers.get('X-Razorpay-Signature', '')
    body = request.body

    if webhook_secret:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            client.utility.verify_webhook_signature(body.decode('utf-8'), signature, webhook_secret)
        except razorpay.errors.SignatureVerificationError:
            logger.warning("Razorpay webhook signature verification failed")
            return HttpResponse(status=400)
    else:
        logger.warning("RAZORPAY_WEBHOOK_SECRET is not configured; skipping webhook signature check")

    try:
        event = json.loads(body)
    except ValueError:
        return HttpResponse(status=400)

    if event.get('event') != 'payment.captured':
        return HttpResponse(status=200)

    try:
        payment_entity = event['payload']['payment']['entity']
        order_id = payment_entity['order_id']
        payment_id = payment_entity['id']
    except (KeyError, TypeError):
        return HttpResponse(status=400)

    payment_record = RazorpayPayment.objects.filter(razorpay_order_id=order_id).order_by('-created_at').first()
    if not payment_record:
        logger.warning("Razorpay webhook: no local order found for %s", order_id)
        return HttpResponse(status=200)

    if payment_record.status != RazorpayPayment.STATUS_PAID:
        payment_record.razorpay_payment_id = payment_id
        payment_record.status = RazorpayPayment.STATUS_PAID
        payment_record.paid_at = timezone.now()
        payment_record.save()

    Enrollment.objects.get_or_create(
        student_id=payment_record.student_id,
        course_id=payment_record.course_id,
        defaults={'payment_id': payment_id},
    )

    return HttpResponse(status=200)


@login_required
@require_POST
def submit_course_review(request, slug):
    """Student review, required after finishing all lessons and before the
    certificate can be downloaded. Goes to admin for moderation before it can
    be shown anywhere on the public site -- never auto-published."""
    course = get_object_or_404(Course, slug=slug)

    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, "You need to be enrolled in this course to review it.")
        return redirect('dashboard:certificates')

    course_lessons = Lesson.objects.filter(module__course=course)
    total = course_lessons.count()
    completed = LessonProgress.objects.filter(
        student=request.user, lesson__in=course_lessons, is_completed=True
    ).count()
    if total == 0 or completed < total:
        messages.error(request, "Please complete all lessons before leaving a review.")
        return redirect('dashboard:certificates')

    try:
        rating = int(request.POST.get('rating', 5))
    except (TypeError, ValueError):
        rating = 5
    rating = max(1, min(5, rating))
    text = request.POST.get('text', '').strip()[:2000]
    if not text:
        messages.error(request, "Please write a few words about your experience.")
        return redirect(f"{reverse('dashboard:certificates')}?review_course={course.id}")

    CourseReview.objects.update_or_create(
        student=request.user,
        course=course,
        defaults={
            'rating': rating,
            'text': text,
            'status': CourseReview.STATUS_PENDING,
            'reviewed_at': None,
        },
    )
    reviewer_name = getattr(request.user, 'full_name', '') or request.user.username
    notify_admin_whatsapp(
        f"New review pending approval: '{course.title}' by {reviewer_name} ({rating})."
    )
    messages.success(request, "Thanks for your review! Your certificate is now ready to download.")
    return redirect('dashboard:certificates')
