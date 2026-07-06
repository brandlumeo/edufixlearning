from PIL import Image
import numpy as np

def extract_signature_final():
    src = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg"
    img = Image.open(src)
    w, h = img.size
    
    # Just the handwritten signature circle only (above the RASAL FARHAN text line)
    # Tighten the crop: X: 595-775, Y: 573-625
    sig_box = (600, 572, 778, 622)
    sig_crop = img.crop(sig_box)
    sig_crop.save(r"c:\Users\M S I\Desktop\edufixlearn\scratch\sig_only.png")
    print(f"Signature only crop saved: {sig_crop.size}")
    
    # The full block: signature circle + RASAL FARHAN + FOUNDER & CEO
    # X: 555-810, Y: 570-660
    full_sig_box = (555, 568, 810, 660)
    full_sig_crop = img.crop(full_sig_box)
    
    # Make the white background transparent
    sig_rgba = full_sig_crop.convert("RGBA")
    np_arr = np.array(sig_rgba)
    # Make near-white pixels transparent
    r, g, b, a = np_arr[:,:,0], np_arr[:,:,1], np_arr[:,:,2], np_arr[:,:,3]
    mask = (r > 225) & (g > 225) & (b > 225)
    np_arr[mask] = [255, 255, 255, 0]  # transparent
    result = Image.fromarray(np_arr, 'RGBA')
    
    out_path = r"c:\Users\M S I\Desktop\edufixlearn\static\images\rasal_farhan_signature.png"
    result.save(out_path, "PNG")
    
    import shutil
    shutil.copy(out_path, r"c:\Users\M S I\Desktop\edufixlearn\media\certificates\rasal_farhan_signature.png")
    shutil.copy(out_path, r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\rasal_sig.png")
    print(f"Signature saved")

if __name__ == "__main__":
    extract_signature_final()
