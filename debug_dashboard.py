import os
import django
import traceback
from django.test import RequestFactory

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edufix_lms.settings')
django.setup()

from dashboard.views import dashboard_home, admin_dashboard, my_courses, settings_view, ai_tutor, assignments_view
from users.models import User

def test_dashboard():
    factory = RequestFactory()
    for user in User.objects.all():
        print(f"Testing Dashboard for: {user.email}")
        try:
            if user.is_staff:
                request = factory.get('/dashboard/admin-analytics/')
                request.user = user
                response = admin_dashboard(request)
                _ = response.content
                print(f"Result for {user.email} (Admin): SUCCESS")
            else:
                for url, view_func in [
                    ('/dashboard/', dashboard_home),
                    ('/dashboard/my-courses/', my_courses),
                    ('/dashboard/settings/', settings_view),
                    ('/dashboard/ai-tutor/', ai_tutor),
                    ('/dashboard/assignments/', assignments_view),
                ]:
                    request = factory.get(url)
                    request.user = user
                    response = view_func(request)
                    _ = response.content
                print(f"Result for {user.email} (Student all views): SUCCESS")
        except Exception as e:
            print(f"Result for {user.email}: FAILED")
            print(traceback.format_exc())

if __name__ == "__main__":
    test_dashboard()
