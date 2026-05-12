import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from django.conf import settings
import uuid

def generate_certificate_pdf(student_name, course_name, issue_date):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Background Color (Dark Purple themed)
    p.setFillColor(HexColor('#05000a'))
    p.rect(0, 0, width, height, fill=1)

    # Border
    p.setStrokeColor(HexColor('#ffd700')) # Gold
    p.setLineWidth(5)
    p.rect(20, 20, width-40, height-40)

    # Title
    p.setFillColor(HexColor('#ffd700'))
    p.setFont("Helvetica-Bold", 60)
    p.drawCentredString(width/2, height - 150, "CERTIFICATE")
    
    p.setFont("Helvetica", 20)
    p.drawCentredString(width/2, height - 200, "OF COMPLETION")

    # Body
    p.setFillColor(HexColor('#ffffff'))
    p.setFont("Helvetica", 25)
    p.drawCentredString(width/2, height/2 + 30, "This is to certify that")
    
    p.setFont("Helvetica-Bold", 45)
    p.setFillColor(HexColor('#ffd700'))
    p.drawCentredString(width/2, height/2 - 40, student_name.upper())

    p.setFillColor(HexColor('#ffffff'))
    p.setFont("Helvetica", 25)
    p.drawCentredString(width/2, height/2 - 100, f"has successfully completed the course")
    
    p.setFont("Helvetica-Bold", 35)
    p.drawCentredString(width/2, height/2 - 160, course_name)

    # Footer
    p.setFont("Helvetica", 15)
    p.drawCentredString(width/2, 100, f"Issued on {issue_date}")
    
    uid = str(uuid.uuid4())[:8].upper()
    p.setFont("Helvetica", 10)
    p.drawCentredString(width/2, 60, f"Verification ID: EDUFIX-{uid}")

    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer, uid
