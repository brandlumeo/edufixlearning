import os
import sys
import django

# Set up Django environment
sys.path.append(r'c:\Users\M S I\Desktop\edufixlearn')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edufix_lms.settings')
django.setup()

from courses.models import Course, CertificateTemplate

def update_database():
    target_course_title = "10 Days AI-Integrated Mobile Video Editing"
    try:
        course = Course.objects.get(title=target_course_title)
        print(f"Found course: {course.title} (ID: {course.id})")
        
        # 1. Update Course.certificate_template
        course.certificate_template = "certificate_templates/mobile_editing_template.jpg"
        course.save()
        print("Updated Course.certificate_template to 'certificate_templates/mobile_editing_template.jpg'")
        
        # 2. Update/Create CertificateTemplate model
        ct, created = CertificateTemplate.objects.get_or_create(course=course)
        ct.certificate_template = "certificate_templates/mobile_editing_template.jpg"
        ct.save()
        print(f"Updated CertificateTemplate (Created new: {created}) to 'certificate_templates/mobile_editing_template.jpg'")
        
    except Course.DoesNotExist:
        print(f"Error: Course '{target_course_title}' not found in database!")
    except Exception as e:
        print("Error during update:", e)

if __name__ == "__main__":
    update_database()
