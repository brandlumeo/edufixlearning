try:
    import fitz # PyMuPDF
    print("fitz is installed")
except ImportError:
    print("fitz is NOT installed")
    
try:
    import pdf2image
    print("pdf2image is installed")
except ImportError:
    print("pdf2image is NOT installed")
