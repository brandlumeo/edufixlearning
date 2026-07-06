import fitz  # PyMuPDF
import sys

def pdf_to_image(pdf_path, output_path):
    doc = fitz.open(pdf_path)
    page = doc[0]
    mat = fitz.Matrix(3, 3)  # 3x zoom = ~216 DPI
    pix = page.get_pixmap(matrix=mat)
    pix.save(output_path)
    print(f"Saved page image to {output_path}")
    doc.close()

if __name__ == "__main__":
    # Convert test PDFs to images for visual inspection
    pdf_to_image("scratch/test_new_calibrated.pdf", "scratch/preview_new.png")
    pdf_to_image("scratch/test_other_course.pdf", "scratch/preview_other.png")
