import logging
import re

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Q

logger = logging.getLogger(__name__)

_ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
_MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
_PHONE_RE = re.compile(r'^\d{10}$')
from courses.models import (
    Enrollment, LessonProgress, Course, Lesson, Module, 
    Announcement, Certificate, Assignment, Submission, 
    Event, Discussion, Question, Notification, Resource, Category
)
from users.models import UserActivity
from django.contrib.auth import get_user_model

User = get_user_model()

def get_student_dashboard_data(user):
    enrollments = Enrollment.objects.filter(student=user).select_related('course')
    enrolled_course_ids = set([e.course.id for e in enrollments])
    enrollment_by_course_id = {e.course_id: e for e in enrollments}
    all_published_courses = Course.objects.filter(status='published')
    
    course_data = []
    all_dashboard_courses = []
    total_lessons_completed = 0
    total_hours_watched = 0
    all_total_lessons = 0
    all_completed_lessons = 0
    
    for course in all_published_courses:
        is_enrolled = course.id in enrolled_course_ids
        
        course_lessons = Lesson.objects.filter(module__course=course)
        total_lessons = course_lessons.count()
        
        completed_lessons = 0
        module_progress = []
        progress_percent = 0
        resume_lesson = None
        last_watched = None

        if is_enrolled:
            completed_lessons = LessonProgress.objects.filter(
                student=user, 
                lesson__in=course_lessons, 
                is_completed=True
            ).count()
            
            all_total_lessons += total_lessons
            all_completed_lessons += completed_lessons
            
            modules = Module.objects.filter(course=course).prefetch_related('lessons')
            for module in modules:
                m_lessons = module.lessons.all()
                m_total = m_lessons.count()
                m_completed = LessonProgress.objects.filter(
                    student=user, 
                    lesson__in=m_lessons, 
                    is_completed=True
                ).count()
                module_progress.append({
                    'title': module.title,
                    'percent': int((m_completed / m_total * 100)) if m_total > 0 else 0,
                    'is_completed': m_completed == m_total if m_total > 0 else False
                })

            progress_percent = int((completed_lessons / total_lessons * 100)) if total_lessons > 0 else 0
            
            last_progress = LessonProgress.objects.filter(
                student=user, 
                lesson__module__course=course
            ).order_by('-watched_at').first()
            
            if last_progress:
                resume_lesson = last_progress.lesson
            else:
                resume_lesson = course_lessons.order_by('module__order_index', 'order_index').first()
                
            last_watched = last_progress.watched_at if last_progress else None
            
            total_lessons_completed += completed_lessons
            total_hours_watched += (completed_lessons * 15) / 60

        enr = enrollment_by_course_id.get(course.id) if is_enrolled else None
        course_item = {
            'id': course.id,
            'course': course,
            'is_enrolled': is_enrolled,
            'progress': progress_percent,
            'completed_lessons': completed_lessons,
            'total_lessons': total_lessons,
            'left_lessons': total_lessons - completed_lessons,
            'module_progress': module_progress,
            'resume_lesson': resume_lesson,
            'last_watched': last_watched,
            'enrolled_at': enr.enrolled_at if enr else None,
        }

        all_dashboard_courses.append(course_item)
        if is_enrolled:
            course_data.append(course_item)

    # Attendance Summary
    attendance_records = Attendance.objects.filter(student=user).order_by('-date')
    total_classes = attendance_records.count()
    attended_classes = attendance_records.filter(is_present=True).count()
    attendance_percent = int((attended_classes / total_classes * 100)) if total_classes > 0 else 0
    
    # Fee Status
    fee_records = FeeRecord.objects.filter(student=user).select_related('course')
    total_fees = sum(f.total_amount for f in fee_records)
    total_paid = sum(f.amount_paid for f in fee_records)
    balance_due = total_fees - total_paid
    
    # Batch & Instructor Info
    active_batch = user.assigned_batches.filter(is_active=True).select_related('instructor', 'course').first()
    
    # Notifications & Resources
    notifications = Notification.objects.filter(student=user).order_by('-created_at')[:10]
    resources = Resource.objects.filter(lesson__module__course__enrolled_students__student=user).distinct()
    
    # Overall Completion Stats
    overall_progress = int((all_completed_lessons / all_total_lessons * 100)) if all_total_lessons > 0 else 0
    estimated_completion = timezone.now() + timedelta(days=(all_total_lessons - all_completed_lessons) * 2) if all_total_lessons > all_completed_lessons else None

    # Certificates — driven by Certificate records the admin has created for this student
    # Build a quick progress lookup from course_data
    progress_by_course = {data['course'].id: data['progress'] for data in course_data}

    raw_certs = Certificate.objects.filter(student=user).select_related('course')
    certificates = list(raw_certs)                    # keep legacy list for other template parts
    certificate_items = []
    for cert in raw_certs:
        progress = progress_by_course.get(cert.course.id, 0)
        certificate_items.append({
            'course': cert.course,
            'progress': progress,
            'cert': cert,
            'is_unlocked': cert.is_approved,
            'has_file': bool(cert.certificate_file),
        })

    # Assignments
    assignments = Assignment.objects.filter(lesson__module__course__enrolled_students__student=user).distinct()
    for assignment in assignments:
        submission = Submission.objects.filter(assignment=assignment, student=user).first()
        assignment.status = submission.status if submission else 'pending'
        assignment.submission = submission

    # Announcements & Events
    from django.db.models import Q
    announcements = Announcement.objects.filter(Q(expires_at__gt=timezone.now()) | Q(expires_at__isnull=True)).order_by('-created_at')[:5]
    upcoming_events = Event.objects.filter(start_time__gte=timezone.now()).order_by('start_time')[:10]
    
    # Activity Streak
    today = timezone.now().date()
    activities = UserActivity.objects.filter(user=user, date__lte=today).order_by('-date')
    streak = 0
    current_date = today
    for activity in activities:
        if activity.date == current_date:
            streak += 1
            current_date -= timedelta(days=1)
        elif activity.date < current_date:
            break
    
    # Weekly Stats
    weekly_stats = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        day_lessons = LessonProgress.objects.filter(student=user, watched_at__date=date, is_completed=True).count()
        weekly_stats.append({'day': date.strftime('%a'), 'count': day_lessons})

    return {
        'enrollments': course_data,
        'all_dashboard_courses': all_dashboard_courses,
        'total_enrolled': enrollments.count(),
        'total_lessons_completed': total_lessons_completed,
        'total_hours_watched': round(total_hours_watched, 1),
        'streak': streak,
        'weekly_stats': weekly_stats,
        'assignments': assignments,
        'events': upcoming_events,
        'announcements': announcements,
        'certificates': certificates,
        'certificate_items': certificate_items,
        'overall_progress': overall_progress,
        'attendance_stats': {
            'total': total_classes,
            'attended': attended_classes,
            'percent': attendance_percent,
            'records': attendance_records[:10],
            'warning': attendance_percent < 75 if total_classes > 5 else False
        },
        'fee_stats': {
            'total': total_fees,
            'paid': total_paid,
            'balance': balance_due,
            'records': fee_records
        },
        'active_batch': active_batch,
        'resources': resources,
        'notifications': notifications,
        'estimated_completion': estimated_completion,
        'quiz_score': 85, # Mock
    }

@login_required
def dashboard_home(request):
    if request.user.is_staff:
        from django.shortcuts import redirect
        return redirect('dashboard:admin_dashboard')
    try:
        context = get_student_dashboard_data(request.user)
        return render(request, 'dashboard/home.html', context)
    except Exception:
        logger.exception("Error loading student dashboard for user %s", request.user.pk)
        return render(request, 'dashboard/home.html', {'error': 'An error occurred loading your dashboard. Please try again.'})

@login_required
def my_courses(request):
    try:
        context = get_student_dashboard_data(request.user)
        return render(request, 'dashboard/my_courses.html', context)
    except Exception:
        logger.exception("Error loading my_courses for user %s", request.user.pk)
        return render(request, 'dashboard/my_courses.html', {'error': 'An error occurred. Please try again.'})

@login_required
def settings_view(request):
    try:
        user = request.user
        success_message = None

        if request.method == 'POST' and 'update_profile' in request.POST:
            full_name = request.POST.get('full_name', '').strip()
            bio = request.POST.get('bio', '').strip()
            phone = request.POST.get('phone_number', '').strip()

            # Validate inputs
            if len(full_name) < 2:
                messages.error(request, "Full name must be at least 2 characters.")
                return redirect('dashboard:settings')
            if len(full_name) > 255:
                messages.error(request, "Full name is too long.")
                return redirect('dashboard:settings')
            if phone and not _PHONE_RE.match(phone):
                messages.error(request, "Phone number must be exactly 10 digits.")
                return redirect('dashboard:settings')

            # Validate profile picture if provided
            if request.FILES.get('profile_picture'):
                pic = request.FILES['profile_picture']
                ext = pic.name.rsplit('.', 1)[-1].lower() if '.' in pic.name else ''
                if ext not in _ALLOWED_IMAGE_EXTENSIONS:
                    messages.error(request, "Only image files (JPG, PNG, GIF, WebP) are allowed.")
                    return redirect('dashboard:settings')
                if pic.size > _MAX_IMAGE_SIZE:
                    messages.error(request, "Image must be under 5 MB.")
                    return redirect('dashboard:settings')
                user.profile_picture = pic

            user.full_name = full_name
            user.bio = bio[:1000]  # Enforce max length without hard error
            if phone:
                user.phone_number = phone
            user.save()
            success_message = "Profile updated successfully!"

        context = get_student_dashboard_data(user)
        context['success_message'] = success_message
        return render(request, 'dashboard/settings.html', context)
    except Exception:
        logger.exception("Error in settings_view for user %s", request.user.pk)
        return render(request, 'dashboard/settings.html', {'error': 'An error occurred. Please try again.'})

@login_required
def ai_tutor(request):
    if request.method == 'POST':
        import json
        from django.http import JsonResponse
        try:
            data = json.loads(request.body)
            user_msg = data.get('message', '').lower()
            
            # Simple Rule-based / Mock AI response
            response = "I'm your Edufix AI Tutor. I can help with Video Editing and Photoshop questions. "
            if 'video' in user_msg or 'edit' in user_msg:
                response = "For Video Editing, remember to always organize your footage before starting the cut. Have you checked out our Premiere Pro Masterclass?"
            elif 'photoshop' in user_msg or 'design' in user_msg:
                response = "In Photoshop, using non-destructive layers is key to a professional workflow. Our Poster Designing course covers this in detail."
            elif 'hello' in user_msg or 'hi' in user_msg:
                response = "Hello! I'm your AI Tutor. How can I help you with your creative journey today?"
            else:
                response = "That's a great question! While I'm learning more, I'd suggest checking the specific module in your course or asking in the community forum."
            
            return JsonResponse({'response': response})
        except:
            return JsonResponse({'response': "I encountered an error. Please try again later."}, status=400)

    context = get_student_dashboard_data(request.user)
    return render(request, 'dashboard/ai_tutor.html', context)

@login_required
def assignments_view(request):
    try:
        context = get_student_dashboard_data(request.user)
        return render(request, 'dashboard/assignments.html', context)
    except Exception:
        logger.exception("Error loading assignments for user %s", request.user.pk)
        return render(request, 'dashboard/assignments.html', {'error': 'An error occurred. Please try again.'})

@login_required
def certificates_view(request):
    try:
        user = request.user
        # Build progress lookup for all enrolled courses
        enrollments = Enrollment.objects.filter(student=user).select_related('course')
        progress_by_course = {}
        for enrollment in enrollments:
            course = enrollment.course
            course_lessons = Lesson.objects.filter(module__course=course)
            total = course_lessons.count()
            completed = LessonProgress.objects.filter(
                student=user, lesson__in=course_lessons, is_completed=True
            ).count()
            progress_by_course[course.id] = int((completed / total * 100)) if total > 0 else 0

        # Get all certificates the admin has assigned to this student
        raw_certs = Certificate.objects.filter(student=user).select_related('course')
        certificate_items = []
        for cert in raw_certs:
            progress = progress_by_course.get(cert.course.id, 0)
            certificate_items.append({
                'course': cert.course,
                'progress': progress,
                'cert': cert,
                'is_unlocked': cert.is_approved,
                'has_file': bool(cert.certificate_file),
            })

        context = {
            'certificate_items': certificate_items,
            'overall_progress': 0,
        }
        return render(request, 'dashboard/certificates.html', context)
    except Exception:
        logger.exception("Error loading certificates for user %s", request.user.pk)
        return render(request, 'dashboard/certificates.html', {'error': 'An error occurred. Please try again.', 'certificate_items': []})

from management.models import Batch, Attendance, FeeRecord, PlacementOutcome, AssetInventory, Lead, SupportTicket

@staff_member_required
def admin_dashboard(request):
    # 1. Students & Enrollment
    total_students = User.objects.filter(is_staff=False).count()
    new_admissions_this_month = Enrollment.objects.filter(enrolled_at__month=timezone.now().month).count()
    active_students = Enrollment.objects.filter(course__status='published').values('student').distinct().count()
    
    # Dropout rate / Inactive (Mock logic: didn't login in last 30 days)
    last_30_days = timezone.now() - timedelta(days=30)
    inactive_students = User.objects.filter(is_staff=False, last_login__lt=last_30_days).count()
    dropout_rate = round((inactive_students / total_students * 100), 1) if total_students > 0 else 0
    
    # 2. Courses & Batches
    courses = Course.objects.annotate(
        student_count=Count('enrolled_students'),
        completion_count=Count('certificates')
    )
    batches = Batch.objects.filter(is_active=True).annotate(
        filled_seats=Count('students')
    )
    all_batches = (
        Batch.objects
        .select_related('course', 'instructor')
        .prefetch_related('students')
        .annotate(filled_seats=Count('students'))
        .order_by('-start_date')
    )
    batch_stats = {
        'total': Batch.objects.count(),
        'active': Batch.objects.filter(status='active').count(),
        'upcoming': Batch.objects.filter(status='upcoming').count(),
        'completed': Batch.objects.filter(status='completed').count(),
    }
    upcoming_batches = Batch.objects.filter(start_date__gte=timezone.now().date()).order_by('start_date')[:5]
    
    # 3. Attendance (Quick Stats)
    today_attendance = Attendance.objects.filter(date=timezone.now().date())
    low_attendance_count = 0 # Normally calculated per student percentage
    
    # 4. Fees & Revenue
    total_revenue = FeeRecord.objects.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_due = FeeRecord.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    pending_fees = total_due - total_revenue
    overdue_count = FeeRecord.objects.filter(due_date__lt=timezone.now().date(), is_fully_paid=False).count()
    
    # 5. Assignments
    total_submissions = Submission.objects.count()
    pending_submissions = Submission.objects.filter(status='pending').count()
    
    # 6. Instructors
    instructors = User.objects.filter(is_instructor=True).annotate(
        active_batches=Count('conducted_batches', filter=Q(conducted_batches__is_active=True))
    )
    
    # 7. Certifications
    total_certs = Certificate.objects.count()
    certs_this_month = Certificate.objects.filter(issued_at__month=timezone.now().month).count()
    
    # 8. Placements
    total_placed = PlacementOutcome.objects.count()
    placement_rate = round((total_placed / total_students * 100), 1) if total_students > 0 else 0
    
    # 9. Resources
    assets = AssetInventory.objects.all()
    
    # 10. Notifications (Fee due, etc.)
    alerts = []
    if overdue_count > 0:
        alerts.append({'type': 'fee', 'msg': f'{overdue_count} students have overdue fees'})
    
    context = {
        'now': timezone.now(),
        'total_students': total_students,
        'new_admissions': new_admissions_this_month,
        'active_students': active_students,
        'inactive_students': inactive_students,
        'dropout_rate': dropout_rate,
        
        'courses': courses,
        'batches': batches,
        'all_batches': all_batches,
        'batch_stats': batch_stats,
        'upcoming_batches': upcoming_batches,
        
        'total_revenue': total_revenue,
        'pending_fees': pending_fees,
        'overdue_count': overdue_count,
        
        'total_submissions': total_submissions,
        'pending_submissions': pending_submissions,
        
        'instructors': instructors,
        
        'total_certs': total_certs,
        'certs_this_month': certs_this_month,
        
        'total_placed': total_placed,
        'placement_rate': placement_rate,
        
        'assets': assets,
        'alerts': alerts,
        'recent_enrollments': Enrollment.objects.select_related('student', 'course').order_by('-enrolled_at')[:5],
        'last_30_days': last_30_days,
        'all_students': User.objects.filter(is_staff=False).prefetch_related(
            'enrollments__course', 
            'assigned_batches', 
            'fee_records'
        ).annotate(
            course_count=Count('enrollments', distinct=True),
            pending_fee_count=Count('fee_records', filter=Q(fee_records__is_fully_paid=False)),
            total_fee_count=Count('fee_records')
        ).order_by('-date_joined'),
        'all_fee_records': FeeRecord.objects.all().select_related('student', 'course').order_by('-due_date'),
        'pending_submissions_list': Submission.objects.filter(status='pending').select_related('student', 'assignment__lesson__module__course').order_by('-submitted_at')[:50],
        'all_submissions': Submission.objects.select_related('student', 'assignment').order_by('-submitted_at')[:300],
        'all_placements': PlacementOutcome.objects.all().select_related('student').order_by('-placement_date'),
        'all_assets': AssetInventory.objects.all().order_by('category', 'name'),
        'recent_activities': sorted(
            [{'type': 'enrollment', 'user': e.student.username, 'meta': e.course.title, 'time': e.enrolled_at} for e in Enrollment.objects.select_related('student', 'course').order_by('-enrolled_at')[:5]] +
            [{'type': 'certificate', 'user': c.student.username, 'meta': c.course.title, 'time': c.issued_at} for c in Certificate.objects.select_related('student', 'course').order_by('-issued_at')[:5]] +
            [{'type': 'submission', 'user': s.student.username, 'meta': s.assignment.title, 'time': s.submitted_at} for s in Submission.objects.select_related('student', 'assignment').order_by('-submitted_at')[:5]],
            key=lambda x: x['time'], reverse=True
        )[:10],
        'all_announcements': Announcement.objects.all().order_by('-created_at'),
        'upcoming_events_all': Event.objects.filter(start_time__gte=timezone.now()).order_by('start_time'),
        'recent_questions': Question.objects.select_related('student', 'lesson').order_by('-created_at')[:10],
        'recent_discussions': Discussion.objects.select_related('user', 'course').order_by('-created_at')[:10],
        'all_certificates': Certificate.objects.select_related('student', 'course').order_by('-issued_at'),
        'all_notifications': Notification.objects.all().select_related('student').order_by('-created_at')[:20],
        'all_course_resources': Resource.objects.all().select_related('lesson__module__course').order_by('lesson__module__course'),
        'all_leads': Lead.objects.all().order_by('-created_at'),
        'all_tickets': SupportTicket.objects.select_related('student').order_by('-created_at'),
        'all_assignments': Assignment.objects.select_related('lesson__module__course').annotate(
            total_subs=Count('submissions', distinct=True),
            pending_subs=Count('submissions', filter=Q(submissions__status='pending'), distinct=True),
        ).order_by('-deadline'),
        'all_modules': Module.objects.select_related('course').order_by('course__title', 'order_index'),
        'courses_with_modules': Course.objects.prefetch_related('modules').order_by('title'),
        'all_categories': Category.objects.all(),
        'all_lessons': Lesson.objects.select_related('module__course').order_by('module__course__title', 'order_index'),
    }
    return render(request, 'dashboard/admin_home.html', context)

@staff_member_required
def upload_class_view(request):
    from django.shortcuts import redirect
    from django.contrib import messages
    if request.method == 'POST':
        module_id = request.POST.get('module_id')
        title = request.POST.get('title')
        video_url = request.POST.get('video_url')
        
        if module_id and title and video_url:
            try:
                module = Module.objects.get(id=module_id)
                # Determine next order index
                last_lesson = module.lessons.order_by('-order_index').first()
                next_order = last_lesson.order_index + 1 if last_lesson else 0
                
                Lesson.objects.create(
                    module=module,
                    title=title,
                    video_url=video_url,
                    order_index=next_order
                )
                messages.success(request, f"Class '{title}' uploaded successfully to {module.course.title}!")
            except Module.DoesNotExist:
                messages.error(request, "Selected module does not exist.")
            except Exception:
                logger.exception("Error uploading class")
                messages.error(request, "An error occurred while uploading the class. Please try again.")
        else:
            messages.error(request, "Please fill in all required fields.")
            
    return redirect('dashboard:admin_dashboard')

@staff_member_required
def create_course_view(request):
    from django.shortcuts import redirect
    from django.contrib import messages
    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category_id')
        price = request.POST.get('price', 0)
        duration = request.POST.get('duration', 0)
        description = request.POST.get('description')
        thumbnail = request.FILES.get('thumbnail')
        
        if title and category_id and description:
            try:
                category = Category.objects.get(id=category_id)
                course = Course.objects.create(
                    title=title,
                    category=category,
                    price=price,
                    duration=duration,
                    description=description,
                    instructor=request.user,
                    status='draft'
                )
                if thumbnail:
                    course.thumbnail = thumbnail
                    course.save()
                messages.success(request, f"Course '{title}' created successfully as Draft!")
            except Exception:
                logger.exception("Error creating course")
                messages.error(request, "An error occurred while creating the course. Please try again.")
        else:
            messages.error(request, "Please fill in all required fields.")
            
    return redirect('dashboard:admin_dashboard')

@staff_member_required
def create_assignment_view(request):
    from django.shortcuts import redirect
    from django.contrib import messages
    if request.method == 'POST':
        title = request.POST.get('title')
        lesson_id = request.POST.get('lesson_id')
        deadline = request.POST.get('deadline')
        description = request.POST.get('description')
        allowed_types = request.POST.get('allowed_types', 'PDF, ZIP, JPG')
        
        if title and lesson_id and deadline and description:
            try:
                lesson = Lesson.objects.get(id=lesson_id)
                Assignment.objects.create(
                    title=title,
                    lesson=lesson,
                    deadline=deadline,
                    description=description,
                    allowed_types=allowed_types
                )
                messages.success(request, f"Assignment '{title}' created successfully!")
            except Exception:
                logger.exception("Error creating assignment")
                messages.error(request, "An error occurred while creating the assignment. Please try again.")
        else:
            messages.error(request, "Please fill in all required fields.")
            
    return redirect('dashboard:admin_dashboard')


def _redirect_admin_leads_tab():
    return redirect(f"{reverse('dashboard:admin_dashboard')}?tab=leads")


@staff_member_required
@require_POST
def lead_status_view(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)
    status = request.POST.get("status", "")
    valid = {k for k, _ in Lead.STATUS_CHOICES}
    if status not in valid:
        messages.error(request, "Invalid status.")
        return _redirect_admin_leads_tab()
    lead.status = status
    lead.save(update_fields=["status"])
    messages.success(request, f'Status updated for "{lead.name}".')
    return _redirect_admin_leads_tab()


@staff_member_required
@require_POST
def lead_update_view(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)
    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()
    if not name or not email:
        messages.error(request, "Name and email are required.")
        return _redirect_admin_leads_tab()
    lead.name = name
    lead.email = email
    lead.phone = request.POST.get("phone", "").strip()
    lead.source = (request.POST.get("source") or lead.source or "Website").strip()
    lead.notes = (request.POST.get("notes") or "").strip()
    st = request.POST.get("status", lead.status)
    if st in dict(Lead.STATUS_CHOICES):
        lead.status = st
    course_id = request.POST.get("course_id")
    if course_id:
        lead.course_interested = Course.objects.filter(pk=course_id).first()
    else:
        lead.course_interested = None
    lead.save()
    messages.success(request, f'Lead "{lead.name}" saved.')
    return _redirect_admin_leads_tab()


@staff_member_required
@require_POST
def lead_create_view(request):
    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()
    if not name or not email:
        messages.error(request, "Name and email are required.")
        return _redirect_admin_leads_tab()
    phone = request.POST.get("phone", "").strip()
    source = (request.POST.get("source") or "Website").strip()
    notes = (request.POST.get("notes") or "").strip()
    st = request.POST.get("status", "new")
    if st not in dict(Lead.STATUS_CHOICES):
        st = "new"
    course = None
    cid = request.POST.get("course_id")
    if cid:
        course = Course.objects.filter(pk=cid).first()
    Lead.objects.create(
        name=name,
        email=email,
        phone=phone,
        source=source or "Website",
        course_interested=course,
        status=st,
        notes=notes,
    )
    messages.success(request, "New enquiry added.")
    return _redirect_admin_leads_tab()


def _redirect_admin_students_tab():
    return redirect(f"{reverse('dashboard:admin_dashboard')}?tab=students")


@staff_member_required
def export_students_csv(request):
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="edufix_students.csv"'
    writer = csv.writer(response)
    writer.writerow(
        ["Username", "Email", "Full name", "Phone", "Date joined", "Active", "Enrollments", "Last login"]
    )
    students = (
        User.objects.filter(is_staff=False)
        .order_by("-date_joined")
        .prefetch_related("enrollments")
    )
    for u in students:
        writer.writerow(
            [
                u.username,
                u.email,
                getattr(u, "full_name", "") or "",
                getattr(u, "phone_number", "") or "",
                u.date_joined.strftime("%Y-%m-%d") if u.date_joined else "",
                "yes" if u.is_active else "no",
                u.enrollments.count(),
                u.last_login.strftime("%Y-%m-%d %H:%M") if u.last_login else "",
            ]
        )
    return response


@staff_member_required
@require_POST
def student_toggle_active_view(request, user_id):
    if request.user.pk == user_id:
        messages.error(request, "You cannot activate or deactivate your own account from this list.")
        return _redirect_admin_students_tab()
    student = get_object_or_404(User, pk=user_id, is_staff=False)
    student.is_active = not student.is_active
    student.save(update_fields=["is_active"])
    state = "activated" if student.is_active else "deactivated"
    messages.success(request, f"Account {student.username} has been {state}.")
    return _redirect_admin_students_tab()


def _redirect_admin_batches_tab():
    return redirect(f"{reverse('dashboard:admin_dashboard')}?tab=batches")


def _redirect_admin_portfolio_tab():
    return redirect(f"{reverse('dashboard:admin_dashboard')}?tab=portfolio")


def _redirect_admin_certs_tab():
    return redirect(f"{reverse('dashboard:admin_dashboard')}?tab=certs")


@staff_member_required
@require_POST
def submission_review_view(request, submission_id):
    sub = get_object_or_404(Submission, id=submission_id)
    action = request.POST.get('action', '')
    feedback = request.POST.get('feedback', '').strip()
    redirect_tab = request.POST.get('redirect_tab', 'portfolio')
    if action == 'approve':
        sub.status = 'approved'
        sub.feedback = feedback
    elif action == 'revision':
        sub.status = 'needs_revision'
        sub.feedback = feedback
    else:
        messages.error(request, "Unknown review action.")
        return redirect(f"{reverse('dashboard:admin_dashboard')}?tab={redirect_tab}")
    sub.save(update_fields=['status', 'feedback'])
    messages.success(request, f"Submission by {sub.student.username} marked as '{sub.get_status_display()}'.")
    return redirect(f"{reverse('dashboard:admin_dashboard')}?tab={redirect_tab}")


@staff_member_required
@require_POST
def certificate_issue_view(request):
    import uuid
    student_id = request.POST.get('student_id')
    course_id = request.POST.get('course_id')
    if not (student_id and course_id):
        messages.error(request, "Student and course are required.")
        return _redirect_admin_certs_tab()
    try:
        student = User.objects.get(id=student_id, is_staff=False)
        course = Course.objects.get(id=course_id)
        existing = Certificate.objects.filter(student=student, course=course).first()
        if existing:
            if existing.is_approved:
                messages.warning(request, f"Certificate already approved for {student.username} — {course.title}.")
            else:
                existing.is_approved = True
                existing.save(update_fields=['is_approved'])
                messages.success(request, f"Certificate approved for {student.username} in '{course.title}'!")
        else:
            cert_uid = f"CERT-{uuid.uuid4().hex[:8].upper()}"
            Certificate.objects.create(student=student, course=course, certificate_uid=cert_uid, is_approved=True)
            messages.success(request, f"Certificate approved and issued to {student.username} for '{course.title}'!")
    except User.DoesNotExist:
        messages.error(request, "Student not found.")
    except Course.DoesNotExist:
        messages.error(request, "Course not found.")
    except Exception:
        logger.exception("Error issuing certificate")
        messages.error(request, "An error occurred while issuing the certificate. Please try again.")
    return _redirect_admin_certs_tab()


@staff_member_required
@require_POST
def certificate_approve_view(request, cert_uid):
    cert = get_object_or_404(Certificate, certificate_uid=cert_uid)
    if cert.is_approved:
        messages.warning(request, f"Certificate {cert_uid} is already approved.")
    else:
        cert.is_approved = True
        cert.save(update_fields=['is_approved'])
        messages.success(request, f"Certificate approved for {cert.student.username} — {cert.course.title}.")
    return _redirect_admin_certs_tab()


@staff_member_required
@require_POST
def batch_create_view(request):
    name = request.POST.get('name', '').strip()
    course_id = request.POST.get('course')
    instructor_id = request.POST.get('instructor') or None
    start_date = request.POST.get('start_date') or None
    end_date = request.POST.get('end_date') or None
    schedule = request.POST.get('schedule', '').strip()
    total_seats = request.POST.get('total_seats', '0')
    batch_code = request.POST.get('batch_code', '').strip()
    status = request.POST.get('status', 'upcoming')
    mode = request.POST.get('mode', 'offline')
    location = request.POST.get('location', '').strip()
    online_meeting_url = request.POST.get('online_meeting_url', '').strip()
    total_classes = int(request.POST.get('total_classes', 0) or 0)
    completed_classes = int(request.POST.get('completed_classes', 0) or 0)
    is_active = request.POST.get('is_active') == '1'

    if not (name and course_id and start_date and total_seats):
        messages.error(request, "Batch name, course, start date, and total seats are required.")
        return _redirect_admin_batches_tab()
    try:
        course = Course.objects.get(id=course_id)
        instructor = User.objects.get(id=instructor_id) if instructor_id else None
        Batch.objects.create(
            name=name,
            batch_code=batch_code,
            course=course,
            instructor=instructor,
            start_date=start_date,
            end_date=end_date,
            schedule=schedule,
            total_seats=int(total_seats),
            status=status if status in dict(Batch.STATUS_CHOICES) else 'upcoming',
            mode=mode if mode in dict(Batch.MODE_CHOICES) else 'offline',
            location=location,
            online_meeting_url=online_meeting_url,
            total_classes=total_classes,
            completed_classes=completed_classes,
            is_active=is_active,
        )
        messages.success(request, f"Batch '{name}' created successfully!")
    except Exception:
        logger.exception("Error creating batch")
        messages.error(request, "An error occurred while creating the batch. Please try again.")
    return _redirect_admin_batches_tab()


@staff_member_required
@require_POST
def batch_edit_view(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    name = request.POST.get('name', '').strip()
    course_id = request.POST.get('course')
    instructor_id = request.POST.get('instructor') or None
    start_date = request.POST.get('start_date') or None
    end_date = request.POST.get('end_date') or None

    if not (name and course_id and start_date):
        messages.error(request, "Batch name, course, and start date are required.")
        return _redirect_admin_batches_tab()
    try:
        batch.name = name
        batch.batch_code = request.POST.get('batch_code', '').strip()
        batch.course = Course.objects.get(id=course_id)
        batch.instructor = User.objects.get(id=instructor_id) if instructor_id else None
        batch.start_date = start_date
        batch.end_date = end_date
        batch.schedule = request.POST.get('schedule', '').strip()
        ts = request.POST.get('total_seats', '0')
        batch.total_seats = int(ts) if ts else batch.total_seats
        status = request.POST.get('status', batch.status)
        batch.status = status if status in dict(Batch.STATUS_CHOICES) else batch.status
        mode = request.POST.get('mode', batch.mode)
        batch.mode = mode if mode in dict(Batch.MODE_CHOICES) else batch.mode
        batch.location = request.POST.get('location', '').strip()
        batch.online_meeting_url = request.POST.get('online_meeting_url', '').strip()
        batch.total_classes = int(request.POST.get('total_classes', 0) or 0)
        batch.completed_classes = int(request.POST.get('completed_classes', 0) or 0)
        batch.is_active = request.POST.get('is_active') == '1'
        batch.save()
        messages.success(request, f"Batch '{batch.name}' updated successfully!")
    except Exception:
        logger.exception("Error updating batch %s", batch_id)
        messages.error(request, "An error occurred while updating the batch. Please try again.")
    return _redirect_admin_batches_tab()


@staff_member_required
@require_POST
def batch_delete_view(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    name = batch.name
    try:
        batch.delete()
        messages.success(request, f"Batch '{name}' deleted successfully.")
    except Exception:
        logger.exception("Error deleting batch %s", batch_id)
        messages.error(request, "An error occurred while deleting the batch. Please try again.")
    return _redirect_admin_batches_tab()


@staff_member_required
@require_POST
def batch_assign_students_view(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    student_ids = request.POST.getlist('student_ids')
    try:
        if student_ids:
            students = User.objects.filter(id__in=student_ids, is_staff=False)
            batch.students.set(students)
        else:
            batch.students.clear()
        messages.success(request, f"Students assigned to '{batch.name}' updated.")
    except Exception:
        logger.exception("Error assigning students to batch %s", batch_id)
        messages.error(request, "An error occurred while assigning students. Please try again.")
    return _redirect_admin_batches_tab()
