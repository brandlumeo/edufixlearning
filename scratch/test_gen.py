import os
import sys
import django

# Set up Django environment
sys.path.append(r'c:\Users\M S I\Desktop\edufixlearn')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edufix_lms.settings')
django.setup()

from courses.utils import generate_certificate_pdf

def test_generation():
    # Test generation with no custom template (uses static fallback)
    buf, uid = generate_certificate_pdf(
        student_name="John Doe",
        course_name="10 Days AI-Integrated Mobile Video Editing",
        issue_date="30 June 2026"
    )
    with open("scratch/test_original.pdf", "wb") as f:
        f.write(buf.getvalue())
    print("Generated scratch/test_original.pdf with uid:", uid)

if __name__ == "__main__":
    os.makedirs("scratch", exist_ok=True)
    test_generation()
