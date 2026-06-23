import fitz
import sys

def extract_favicon():
    pdf_path = r"C:\Users\M S I\Downloads\EDFX FINAL.pdf"
    img_path = r"C:\Users\M S I\Desktop\edufixlearn\static\images\favicon.png"
    
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)  # first page
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        pix.save(img_path)
        print("Successfully extracted favicon to", img_path)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    extract_favicon()
