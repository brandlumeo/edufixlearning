import os
import sys
import django

# Set up Django environment
sys.path.append(r'c:\Users\M S I\Desktop\edufixlearn')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edufix_lms.settings')
django.setup()

from courses.models import Course, CertificateTemplate
from courses.utils import generate_certificate_pdf

def verify_certificates():
    # Test case 1: The course we updated
    course_updated = Course.objects.get(title="10 Days AI-Integrated Mobile Video Editing")
    print(f"Testing for course: {course_updated.title}")
    
    # Resolve template_file using the same logic as the view
    template_file = None
    try:
        ct_model = course_updated.certificate_template_model
        template_file = ct_model.certificate_template
    except Exception:
        pass
    if not template_file:
        template_file = getattr(course_updated, 'certificate_template', None)
        
    print(f"Resolved template_file path from DB: {template_file}")
    
    buf, uid = generate_certificate_pdf(
        student_name="John Doe",
        course_name=course_updated.title,
        issue_date="30 June 2026",
        template_file=template_file
    )
    with open("scratch/test_new_calibrated.pdf", "wb") as f:
        f.write(buf.getvalue())
    print("Generated scratch/test_new_calibrated.pdf with uid:", uid)
    
    # Test case 2: Another course using the blank template to ensure non-regression
    other_course = Course.objects.get(title="Master Metalist")
    print(f"\nTesting for other course: {other_course.title}")
    
    template_file_other = None
    try:
        ct_model_other = other_course.certificate_template_model
        template_file_other = ct_model_other.certificate_template
    except Exception:
        pass
    if not template_file_other:
        template_file_other = getattr(other_course, 'certificate_template', None)
        
    print(f"Resolved template_file path from DB: {template_file_other}")
    
    buf_other, uid_other = generate_certificate_pdf(
        student_name="Alice Smith",
        course_name=other_course.title,
        issue_date="30 June 2026",
        template_file=template_file_other
    )
    with open("scratch/test_other_course.pdf", "wb") as f:
        f.write(buf_other.getvalue())
    print("Generated scratch/test_other_course.pdf with uid:", uid_other)

if __name__ == "__main__":
    verify_certificates()
