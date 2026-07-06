import numpy as np
from PIL import Image

def analyze_image(path):
    img = Image.open(path)
    w, h = img.size
    # Convert to grayscale numpy array
    gray = img.convert('L')
    arr = np.array(gray)
    
    # Check central region (e.g. from 20% to 80% width, 20% to 80% height)
    center = arr[int(h*0.2):int(h*0.8), int(w*0.2):int(w*0.8)]
    mean_val = np.mean(center)
    min_val = np.min(center)
    max_val = np.max(center)
    std_val = np.std(center)
    
    print(f"Image: {path}")
    print(f"  Size: {w}x{h}")
    print(f"  Center region stats: mean={mean_val:.2f}, min={min_val}, max={max_val}, std={std_val:.2f}")
    if std_val < 5:
        print("  Center is likely plain solid color (blank).")
    else:
        print("  Center has variation (contains text/graphics).")

if __name__ == "__main__":
    analyze_image(r"c:\Users\M S I\Desktop\edufixlearn\static\images\edufix_blank_template.jpg")
    analyze_image(r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg")
