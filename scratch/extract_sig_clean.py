from PIL import Image
import numpy as np

def extract_signature_clean():
    src = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg"
    img = Image.open(src)
    w, h = img.size
    
    # Just the signature circle + RASAL FARHAN text, not the body text above
    # Bottom-right area: X: 560-810, Y: 575-665
    sig_box = (555, 570, 815, 665)
    sig_crop = img.crop(sig_box)
    sig_crop.save(r"c:\Users\M S I\Desktop\edufixlearn\scratch\sig_clean.png")
    print(f"Signature crop saved: {sig_crop.size}")
    
    # Make the white background transparent
    sig_rgba = sig_crop.convert("RGBA")
    pixels = list(sig_rgba.getdata())
    new_pixels = []
    for r, g, b, a in pixels:
        if r > 225 and g > 225 and b > 225:
            new_pixels.append((r, g, b, 0))  # transparent
        else:
            new_pixels.append((r, g, b, a))
    sig_rgba.putdata(new_pixels)
    
    out_path = r"c:\Users\M S I\Desktop\edufixlearn\static\images\rasal_farhan_signature.png"
    sig_rgba.save(out_path, "PNG")
    
    import shutil
    shutil.copy(out_path, r"c:\Users\M S I\Desktop\edufixlearn\media\certificates\rasal_farhan_signature.png")
    print(f"Clean signature saved to static/images and media/certificates")

if __name__ == "__main__":
    extract_signature_clean()
