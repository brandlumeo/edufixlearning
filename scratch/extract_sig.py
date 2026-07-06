from PIL import Image
import numpy as np

def extract_signature():
    src = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg"
    img = Image.open(src)
    w, h = img.size
    print(f"Source image size: {w}x{h}")
    
    # The signature + RASAL FARHAN text is roughly in the bottom center-right:
    # X: 560 to 810, Y: 540 to 660
    # Let's crop wider to be safe
    sig_box = (520, 520, 830, 670)
    sig_crop = img.crop(sig_box)
    sig_crop.save(r"c:\Users\M S I\Desktop\edufixlearn\scratch\sig_raw.png")
    print(f"Signature crop saved: {sig_box[2]-sig_box[0]} x {sig_box[3]-sig_box[1]} px")
    
    # Make the white background transparent (for PNG overlay)
    sig_rgba = sig_crop.convert("RGBA")
    data = sig_rgba.getdata()
    new_data = []
    for r, g, b, a in data:
        # If pixel is near-white, make it transparent
        if r > 230 and g > 230 and b > 230:
            new_data.append((r, g, b, 0))  # transparent
        else:
            new_data.append((r, g, b, a))
    sig_rgba.putdata(new_data)
    
    out_path = r"c:\Users\M S I\Desktop\edufixlearn\static\images\rasal_farhan_signature.png"
    sig_rgba.save(out_path, "PNG")
    print(f"Transparent signature saved to: {out_path}")
    
    # Also save to media for easy access
    import os
    media_out = r"c:\Users\M S I\Desktop\edufixlearn\media\certificates\rasal_farhan_signature.png"
    sig_rgba.save(media_out, "PNG")
    print(f"Also saved to: {media_out}")

if __name__ == "__main__":
    extract_signature()
