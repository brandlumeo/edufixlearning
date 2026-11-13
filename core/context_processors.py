from django.utils.timesince import timesince
from django.db.models import Q

from courses.models import Enrollment


def recent_enrollments(request):
    # Sitewide "real students enrolling" social proof popup.
    # Only actual enrollment records are used here -- never fabricated names or times.
    # Covers every enrollment regardless of how it was paid (Razorpay or manual/WhatsApp-approved),
    # since Enrollment is created for a student+course either way.
    # Test/staff accounts are excluded so internal testing doesn't show up as "sales".
    TEST_NAME_FRAGMENTS = ['afthab', 'rasal']

    qs = (
        Enrollment.objects
        .select_related('student', 'course')
    )

    exclude_q = Q()
    for frag in TEST_NAME_FRAGMENTS:
        exclude_q |= Q(student__full_name__icontains=frag)
        exclude_q |= Q(student__username__icontains=frag)
        exclude_q |= Q(student__email__icontains=frag)
    qs = qs.exclude(exclude_q).order_by('-enrolled_at')[:200]

    popups = []
    for e in qs:
        name = getattr(e.student, 'full_name', '') or getattr(e.student, 'username', '') or 'A student'
        course_title = getattr(e.course, 'title', '')
        if not course_title:
            continue
        popups.append({
            'name': name,
            'course': course_title,
            'time_ago': timesince(e.enrolled_at) + ' ago',
        })

    return {'recent_enrollment_popups': popups}


def password_setup_prompt(request):
    """
    Expose the one-time 'create your password' popup flag to every
    template. Set on the session at passwordless signup; cleared once
    the user sets a real password or dismisses the prompt.
    """
    return {'needs_password_setup': request.session.get('needs_password_setup', False)}
