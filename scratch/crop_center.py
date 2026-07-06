from PIL import Image
import numpy as np

def crop_and_analyze():
    img_path = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg"
    img = Image.open(img_path)
    w, h = img.size
    
    # Crop the name area
    # In pixel coordinates, h=723, w=1024
    # "Your Name" is roughly around center (y: 380 to 460, x: 300 to 724)
    name_crop = img.crop((280, 350, 740, 480))
    name_crop.save(r"c:\Users\M S I\Desktop\edufixlearn\scratch\name_crop.png")
    print("Saved scratch/name_crop.png")
    
    # Let's inspect the vertical profile of this cropped area (grayscale values)
    gray = name_crop.convert('L')
    arr = np.array(gray)
    crop_h, crop_w = arr.shape
    
    # Calculate average intensity for each row
    for y in range(crop_h):
        min_val = np.min(arr[y, :])
        mean_val = np.mean(arr[y, :])
        # A horizontal line will have low values across a wide width or a sharp drop
        # Let's print row statistics to locate lines and text
        print(f"Row {y + 350}: min={min_val}, mean={mean_val:.1f}")

if __name__ == "__main__":
    crop_and_analyze()
