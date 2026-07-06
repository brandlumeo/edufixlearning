from PIL import Image
import numpy as np

def extract_signature_v2():
    """Extract ONLY the handwritten signature + RASAL FARHAN + FOUNDER & CEO
    with a tighter crop to avoid any body text leaking in."""
    src = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg"
    img = Image.open(src)
    w, h = img.size
    
    # Tighter crop: skip the body text at the top
    # The signature circle starts at about Y=580, text "RASAL FARHAN" at Y=630
    # "FOUNDER & CEO" ends about Y=655
    # X: 600-790
    sig_box = (600, 578, 790, 658)
    sig_crop = img.crop(sig_box)
    
    # Convert to RGBA and make white pixels transparent
    sig_rgba = sig_crop.convert("RGBA")
    np_arr = np.array(sig_rgba)
    r, g, b, a = np_arr[:,:,0], np_arr[:,:,1], np_arr[:,:,2], np_arr[:,:,3]
    
    # More aggressive white removal
    mask = (r > 220) & (g > 220) & (b > 220)
    np_arr[mask] = [255, 255, 255, 0]
    
    result = Image.fromarray(np_arr, 'RGBA')
    
    # Save
    out_path = r"c:\Users\M S I\Desktop\edufixlearn\static\images\rasal_farhan_signature.png"
    result.save(out_path, "PNG")
    
    import shutil
    shutil.copy(out_path, r"c:\Users\M S I\Desktop\edufixlearn\media\certificates\rasal_farhan_signature.png")
    
    # Also save a preview copy
    sig_crop.save(r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\sig_final.png")
    result.save(r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\sig_final_transparent.png")
    
    print(f"Final signature crop: {result.size}")
    print("Saved to static/images and media/certificates")

if __name__ == "__main__":
    extract_signature_v2()
