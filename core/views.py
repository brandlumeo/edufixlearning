from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from courses.models import Course

import json
from django.http import JsonResponse

try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    _openai_available = False

def index(request):
    featured_courses = Course.objects.filter(status='published')
    context = {
        'featured_courses': featured_courses,
    }
    return render(request, 'core/index.html', context)

def about(request):
    return render(request, 'core/about.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # Send email to academyedufix@gmail.com
        subject = f"New Contact Inquiry from {name}"
        message_body = f"Name: {name}\nEmail: {email}\nMessage:\n{message}"
        from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@edufixacademy.com'
        recipient_list = ['academyedufix@gmail.com']
        
        try:
            send_mail(subject, message_body, from_email, recipient_list)
            messages.success(request, f"Thank you {name}, we've received your message and will get back to you soon!")
        except Exception as e:
            messages.error(request, "There was an error sending your message. Please try again later.")
            
        return redirect('core:contact')
    return render(request, 'core/contact.html')

EDUFIX_SYSTEM_PROMPT = """You are the official AI assistant for Edufix Learning Academy — a creative skills training institute.

Your role:
- Help students and prospects with questions about courses, enrollment, fees, schedules, and learning paths
- Clarify doubts about course content (Video Editing, Photoshop, Graphic Design, etc.)
- Provide guidance on assignments, software tools, and creative techniques
- Be friendly, encouraging, and professional

About Edufix Academy:
- Specializes in creative courses: Video Editing (Premiere Pro, After Effects), Photoshop, Graphic Design, and related skills
- Offers both online and offline learning
- Students can enroll through the website or contact the admin team
- For billing, certificate, or account-specific issues, advise users to contact the Edufix support team directly

Rules:
- If a question is outside your knowledge or too specific (e.g., personal account issues, payment disputes), say: "For this, please reach out to our support team — they'll be happy to help you directly."
- Keep answers concise and helpful
- Do not make up course prices or schedules unless stated above; instead say "please check the course page or contact us for the latest details"
- Always be encouraging about the user's learning journey"""


def chatbot_response(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            if not user_message:
                return JsonResponse({'response': "Please type a message so I can help you!"})

            api_key = getattr(settings, 'OPENAI_API_KEY', '')

            if _openai_available and api_key:
                try:
                    client = OpenAI(api_key=api_key)
                    completion = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": EDUFIX_SYSTEM_PROMPT},
                            {"role": "user", "content": user_message},
                        ],
                        max_tokens=400,
                        temperature=0.7,
                    )
                    response = completion.choices[0].message.content.strip()
                    return JsonResponse({'response': response})
                except Exception:
                    pass  # fall through to keyword fallback

            # Keyword fallback when OpenAI is not configured
            msg = user_message.lower()
            if any(w in msg for w in ['hello', 'hi', 'hey']):
                response = "Hello! I'm the Edufix AI Assistant. Ask me anything about our courses, enrollment, or creative skills — I'm here to help!"
            elif 'video editing' in msg or 'premiere' in msg or 'after effects' in msg:
                response = "Our Video Editing course covers Adobe Premiere Pro and After Effects — from basic cuts to advanced motion graphics. Would you like to know more about the curriculum or enrollment?"
            elif 'photoshop' in msg:
                response = "Our Photoshop course covers photo retouching, compositing, and digital art. It's great for beginners and intermediate learners alike. Check the course page for the latest fee details!"
            elif 'graphic design' in msg or 'design' in msg:
                response = "We offer creative design courses covering Photoshop, Illustrator, and more. Great for anyone looking to build a design career!"
            elif 'enroll' in msg or 'admission' in msg or 'join' in msg:
                response = "You can enroll by visiting our Courses page and clicking Enroll, or contact our team directly at academyedufix@gmail.com for assistance."
            elif 'fee' in msg or 'price' in msg or 'cost' in msg:
                response = "Course fees vary by program. Please check the individual course page for the latest pricing, or contact our support team for any special offers."
            elif 'certificate' in msg:
                response = "Yes! Edufix Academy provides certificates upon successful course completion. Contact our support team for details about certification requirements."
            elif 'schedule' in msg or 'timing' in msg or 'batch' in msg:
                response = "Batch schedules vary by course. Please contact our team or check your dashboard for upcoming batch timings."
            elif 'support' in msg or 'help' in msg or 'contact' in msg or 'team' in msg:
                response = "For direct support, please reach out to our team at academyedufix@gmail.com or use the Contact page. We're here to help!"
            elif 'mission' in msg or 'vision' in msg or 'about' in msg:
                response = "Edufix Academy's mission is to provide industry-grade creative education. We empower learners with practical skills for real-world careers in creative fields."
            else:
                response = "That's a great question! I may not have the specific answer right now. For detailed help, please contact our support team at academyedufix@gmail.com — they'll be happy to assist you directly."

            return JsonResponse({'response': response})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)
