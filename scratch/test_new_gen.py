import os
import sys
import django

# Set up Django environment
sys.path.append(r'c:\Users\M S I\Desktop\edufixlearn')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edufix_lms.settings')
django.setup()

from courses.utils import generate_certificate_pdf

def test_generation():
    new_template_path = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg"
    
    # Generate certificate using the new template image
    buf, uid = generate_certificate_pdf(
        student_name="John Doe",
        course_name="10 Days AI-Integrated Mobile Video Editing",
        issue_date="30 June 2026",
        template_file=new_template_path
    )
    with open("scratch/test_new.pdf", "wb") as f:
        f.write(buf.getvalue())
    print("Generated scratch/test_new.pdf with uid:", uid)

if __name__ == "__main__":
    os.makedirs("scratch", exist_ok=True)
    test_generation()
