import pypdf

def inspect_pdf(path):
    print(f"\nInspecting elements in {path}:")
    reader = pypdf.PdfReader(path)
    page = reader.pages[0]
    
    # Extract text with coordinates if possible, or just raw text
    text = page.extract_text()
    print("Raw text content:")
    print(repr(text))
    
    # We can also check if there is an image resource (the background template)
    xobjects = page.images
    print(f"Number of embedded images: {len(xobjects)}")
    for i, img in enumerate(xobjects):
        print(f"  Image {i}: name={img.name}, size={len(img.data)} bytes")

if __name__ == "__main__":
    inspect_pdf("scratch/test_new_calibrated.pdf")
    inspect_pdf("scratch/test_other_course.pdf")
