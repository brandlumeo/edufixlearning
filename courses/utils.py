import os
import logging
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from django.conf import settings
import uuid

logger = logging.getLogger(__name__)


def _wrap_text(text, max_chars_per_line):
    """Simple word-wrap returning a list of lines."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if len(test) <= max_chars_per_line:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _find_static_image(filename):
    """
    Returns the absolute path of a static image, checking both:
      1. STATICFILES_DIRS source folder  → works locally (DEBUG=True)
      2. STATIC_ROOT collected folder    → works in production (DEBUG=False)
    In production, collectstatic moves files to STATIC_ROOT (staticfiles/),
    so the source static/ folder may be absent or empty on the server.
    """
    # Source static directories (development / local)
    for static_dir in getattr(settings, 'STATICFILES_DIRS', []):
        candidate = os.path.join(str(static_dir), 'images', filename)
        if os.path.exists(candidate):
            logger.debug("Found static image at source path: %s", candidate)
            return candidate
    # Collected static root (production after `collectstatic`)
    static_root = getattr(settings, 'STATIC_ROOT', None)
    if static_root:
        candidate = os.path.join(str(static_root), 'images', filename)
        if os.path.exists(candidate):
            logger.debug("Found static image at STATIC_ROOT: %s", candidate)
            return candidate
    logger.warning("Static image not found: %s (checked STATICFILES_DIRS and STATIC_ROOT)", filename)
    return None


def generate_certificate_pdf(student_name, course_name, issue_date, template_file=None):
    """
    Generate a certificate PDF using the Edufix template image as background.

    Priority for template:
    1. `template_file` argument (uploaded course/student template from DB)
    2. static/images/edufix_blank_template.jpg  (the Edufix branded blank template)
    3. static/images/default_certificate_template.jpg (legacy fallback)
    4. Plain white PDF (last resort — always works, no external files needed)
    """
    uid = str(uuid.uuid4())[:8].upper()

    # ── Page size: A4 landscape ──────────────────────────────────────────────
    page_w, page_h = landscape(A4)   # 841.89 x 595.28 pts

    # DEBUG: Force plain white fallback to bypass potential Pillow/ImageReader Segfault on cPanel
    logger.info("Generating plain-white fallback certificate for student=%s", student_name)
    plain_buf = BytesIO()
    p = canvas.Canvas(plain_buf, pagesize=landscape(A4))
    
    # Heading
    p.setFont("Helvetica-Bold", 38)
    p.drawCentredString(page_w / 2, page_h - 120, "CERTIFICATE")
    p.setFont("Helvetica", 14)
    p.drawCentredString(page_w / 2, page_h / 2, f"Student: {student_name}")
    p.drawCentredString(page_w / 2, page_h / 2 - 30, f"Course: {course_name}")
    
    p.showPage()
    p.save()
    plain_buf.seek(0)
    return plain_buf, uid

    # ── Resolve background template ──────────────────────────────────────────
    if not template_file:
        blank_path   = _find_static_image('edufix_blank_template.jpg')
        default_path = _find_static_image('default_certificate_template.jpg')
        if blank_path:
            template_file = blank_path
        elif default_path:
            template_file = default_path

    # ── Check if template is a PDF (merge overlay) ───────────────────────────
    is_pdf_template = False
    if template_file:
        name_str = template_file.name if hasattr(template_file, 'name') else str(template_file)
        is_pdf_template = name_str.lower().endswith('.pdf')

    # ────────────────────────────────────────────────────────────────────────
    # PDF TEMPLATE PATH
    # ────────────────────────────────────────────────────────────────────────
    if template_file and is_pdf_template:
        try:
            import pypdf
            overlay_buf = BytesIO()
            p = canvas.Canvas(overlay_buf, pagesize=landscape(A4))
            _draw_edufix_text(p, page_w, page_h, student_name, course_name, issue_date, uid)
            p.showPage()
            p.save()
            overlay_buf.seek(0)

            if hasattr(template_file, 'seek'):
                template_file.seek(0)
            template_pdf = pypdf.PdfReader(template_file)
            overlay_pdf  = pypdf.PdfReader(overlay_buf)

            tpl_page = template_pdf.pages[0]
            ovl_page = overlay_pdf.pages[0]
            tpl_page.merge_page(ovl_page)

            writer = pypdf.PdfWriter()
            writer.add_page(tpl_page)
            final_buf = BytesIO()
            writer.write(final_buf)
            final_buf.seek(0)
            return final_buf, uid
        except Exception as exc:
            logger.warning("PDF template merge failed, falling through: %s", exc)
            # fall through to image path

    # ────────────────────────────────────────────────────────────────────────
    # IMAGE TEMPLATE PATH  (JPEG / PNG — the normal Edufix case)
    # Each path uses its OWN fresh BytesIO so a failure here cannot corrupt
    # the buffer used by the plain fallback below.
    # ────────────────────────────────────────────────────────────────────────
    if template_file and not is_pdf_template:
        try:
            img_bytes = None

            if hasattr(template_file, 'read'):
                # Django FieldFile — verify the file actually exists on disk
                # before trying to read it (production media files may be absent)
                storage = getattr(template_file, 'storage', None)
                field_name = getattr(template_file, 'name', None)
                if storage and field_name and storage.exists(field_name):
                    template_file.seek(0)
                    img_bytes = template_file.read()
                else:
                    logger.warning(
                        "Certificate template file missing in storage: %s — using fallback",
                        field_name
                    )
            else:
                # Plain filesystem path (from _find_static_image)
                path_str = str(template_file)
                if os.path.exists(path_str):
                    with open(path_str, 'rb') as fh:
                        img_bytes = fh.read()
                else:
                    logger.warning("Certificate template path not found: %s", path_str)

            if img_bytes:
                img_buf = BytesIO()          # fresh buffer for this path
                p = canvas.Canvas(img_buf, pagesize=landscape(A4))
                img_reader = ImageReader(BytesIO(img_bytes))
                p.drawImage(img_reader, 0, 0, width=page_w, height=page_h,
                            preserveAspectRatio=False)
                _draw_edufix_text(p, page_w, page_h, student_name, course_name, issue_date, uid)
                p.showPage()
                p.save()
                img_buf.seek(0)
                return img_buf, uid
            # img_bytes is None → fall through to plain fallback
        except Exception as exc:
            logger.warning("Image template rendering failed, falling through: %s", exc)
            # fall through to plain fallback

    # ────────────────────────────────────────────────────────────────────────
    # PLAIN WHITE FALLBACK  (no external files — always works in production)
    # Uses its own fresh BytesIO — completely isolated from above paths.
    # ────────────────────────────────────────────────────────────────────────
    logger.info("Generating plain-white fallback certificate for student=%s", student_name)
    plain_buf = BytesIO()
    p = canvas.Canvas(plain_buf, pagesize=landscape(A4))

    # Purple border
    p.setFillColor(HexColor('#ffffff'))
    p.rect(0, 0, page_w, page_h, fill=1)
    p.setStrokeColor(HexColor('#5b2d8e'))
    p.setLineWidth(6)
    p.rect(15, 15, page_w - 30, page_h - 30)
    p.setLineWidth(2)
    p.rect(22, 22, page_w - 44, page_h - 44)

    # Heading
    p.setFillColor(HexColor('#5b2d8e'))
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(page_w / 2, page_h - 70, "EDUFIX LEARNING")
    p.setFont("Helvetica-Bold", 38)
    p.drawCentredString(page_w / 2, page_h - 120, "CERTIFICATE")
    p.setFillColor(HexColor('#f59e0b'))
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(page_w / 2, page_h - 150, "OF APPRECIATION")

    p.setFillColor(HexColor('#f59e0b'))
    p.setFont("Helvetica-Bold", 11)
    p.drawCentredString(page_w / 2, page_h / 2 + 70, "THIS CERTIFICATE IS PRESENTED TO")
    p.line(page_w / 2 - 180, page_h / 2 + 64, page_w / 2 + 180, page_h / 2 + 64)

    p.setFillColor(HexColor('#1a1a1a'))
    p.setFont("Helvetica-Bold", 34)
    display_name = student_name if len(student_name) <= 35 else student_name[:33] + '\u2026'
    p.drawCentredString(page_w / 2, page_h / 2 + 20, display_name)

    p.setStrokeColor(HexColor('#f59e0b'))
    p.setLineWidth(1.5)
    p.line(page_w / 2 - 180, page_h / 2 + 12, page_w / 2 + 180, page_h / 2 + 12)

    p.setFillColor(HexColor('#333333'))
    p.setFont("Helvetica", 12)
    body = (f"This certificate recognizes the successful completion of "
            f"Edufix Learning\u2019s {course_name}, empowering creative skills "
            f"through AI tools and advanced mobile editing techniques.")
    lines = _wrap_text(body, 65)
    y_b = page_h / 2 - 30
    for line in lines:
        p.drawCentredString(page_w / 2, y_b, line)
        y_b -= 18

    p.setFillColor(HexColor('#666666'))
    p.setFont("Helvetica", 10)
    p.drawString(200, 80, f"Date: {issue_date}")
    p.drawCentredString(page_w / 2, 50, f"Verification ID: EDUFIX-{uid}")

    p.showPage()
    p.save()
    plain_buf.seek(0)
    return plain_buf, uid



# ─────────────────────────────────────────────────────────────────────────────
# TEXT PLACEMENT — calibrated for the Edufix blank certificate template
# (1600 x 1130 px image rendered as A4 landscape: 841.89 x 595.28 pts)
#
# The blank template has:
#   - Edufix logo at top (already on image, no need to draw)
#   - Empty center for all text content
#   - Geometric colored panels on left and right sides
#
# PDF coordinate system: (0,0) = bottom-left, Y increases upward
# Image pixel Y → PDF Y:  pdf_y = page_h - (pixel_y / img_h * page_h)
#
# Key positions in the blank template (centre text area):
#   CERTIFICATE large title    → top of blank area, y ~250-330px → pdf_y ~440
#   OF APPRECIATION subtitle   → y ~335-400px → pdf_y ~390
#   THIS CERT IS PRESENTED TO → y ~430px → pdf_y ~370
#   Name                       → y ~510px → pdf_y ~323
#   Body paragraph             → y ~640-760px → pdf_y ~240-175
#   Date                       → y ~870px → pdf_y ~120
# ─────────────────────────────────────────────────────────────────────────────
def _draw_edufix_text(p, page_w, page_h, student_name, course_name, issue_date, uid):
    cx = page_w / 2   # horizontal centre ≈ 420.95 pts

    # ── CERTIFICATE (large purple heading) ───────────────────────────────────
    p.setFillColor(HexColor('#5b2d8e'))
    p.setFont("Helvetica-Bold", 44)
    p.drawCentredString(cx, 430, "CERTIFICATE")

    # ── OF APPRECIATION (amber subtitle) ─────────────────────────────────────
    p.setFillColor(HexColor('#f59e0b'))
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(cx, 393, "OF APPRECIATION")

    # ── THIS CERTIFICATE IS PRESENTED TO ─────────────────────────────────────
    p.setFillColor(HexColor('#f59e0b'))
    p.setFont("Helvetica-Bold", 11)
    p.drawCentredString(cx, 358, "THIS CERTIFICATE IS PRESENTED TO")

    # Thin amber line below label
    p.setStrokeColor(HexColor('#f59e0b'))
    p.setLineWidth(1)
    p.line(cx - 190, 352, cx + 190, 352)

    # ── Student Name ─────────────────────────────────────────────────────────
    p.setFillColor(HexColor('#1a1a1a'))
    p.setFont("Helvetica-Bold", 32)
    # Reduce font size for very long names
    display_name = student_name if len(student_name) <= 32 else student_name[:30] + '\u2026'
    p.drawCentredString(cx, 313, display_name)

    # Thin amber line below name
    p.setStrokeColor(HexColor('#f59e0b'))
    p.setLineWidth(1.5)
    p.line(cx - 190, 305, cx + 190, 305)

    # ── Body paragraph (course description) ──────────────────────────────────
    p.setFillColor(HexColor('#444444'))
    p.setFont("Helvetica", 12)
    body = (
        f"This certificate recognizes the successful completion of "
        f"Edufix Learning\u2019s {course_name}, "
        f"empowering creative skills through AI tools and "
        f"advanced mobile editing techniques."
    )
    lines = _wrap_text(body, 58)
    y_body = 272
    line_h = 17
    for line in lines:
        p.drawCentredString(cx, y_body, line)
        y_body -= line_h

    # ── DATE section (bottom-left, matching Edufix template position) ─────────
    p.setFillColor(HexColor('#888888'))
    p.setFont("Helvetica-Bold", 8)
    p.drawCentredString(cx - 130, 120, "DATE")
    p.setStrokeColor(HexColor('#888888'))
    p.setLineWidth(0.5)
    p.line(cx - 185, 116, cx - 75, 116)
    p.setFont("Helvetica", 9)
    p.drawCentredString(cx - 130, 104, issue_date)

    # ── SIGNATURE section (bottom-right, matching Edufix template) ───────────
    p.setFont("Helvetica-Bold", 8)
    p.setFillColor(HexColor('#888888'))
    p.drawCentredString(cx + 130, 120, "SIGNATURE")
    p.setStrokeColor(HexColor('#888888'))
    p.line(cx + 75, 116, cx + 185, 116)
    p.setFont("Helvetica", 9)
    p.drawCentredString(cx + 130, 104, "Founder")

    # ── Verification UID (very bottom center) ────────────────────────────────
    p.setFillColor(HexColor('#aaaaaa'))
    p.setFont("Helvetica", 7)
    p.drawCentredString(cx, 60, f"Verification ID: EDUFIX-{uid}")
