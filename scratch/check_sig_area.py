from PIL import Image
import numpy as np

def check_signature():
    path = r"c:\Users\M S I\Desktop\edufixlearn\media\certificate_templates\mobile_editing_template.jpg"
    img = Image.open(path)
    w, h = img.size
    
    # Crop the bottom right area (where the signature is)
    # X: 550 to 800, Y: 530 to 670
    sig_crop = img.crop((550, 530, 800, 670))
    sig_crop.save(r"c:\Users\M S I\Desktop\edufixlearn\scratch\sig_check.png")
    print("Saved scratch/sig_check.png")
    
    # Convert to numpy array and check if there are dark/blue pixels
    arr = np.array(sig_crop)
    # Check if there are pixels with low values (dark ink)
    gray = sig_crop.convert('L')
    arr_gray = np.array(gray)
    min_val = np.min(arr_gray)
    mean_val = np.mean(arr_gray)
    print(f"Signature area stats: min={min_val}, mean={mean_val:.2f}")

if __name__ == "__main__":
    check_signature()
