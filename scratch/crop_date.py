from PIL import Image
import numpy as np

def crop_and_analyze_date():
    img_path = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg"
    img = Image.open(img_path)
    w, h = img.size
    
    # Date placeholder is around (x: 250 to 480, y: 620 to 680)
    # Let's crop it
    date_crop = img.crop((250, 600, 480, 680))
    date_crop.save(r"c:\Users\M S I\Desktop\edufixlearn\scratch\date_crop.png")
    print("Saved scratch/date_crop.png")
    
    gray = date_crop.convert('L')
    arr = np.array(gray)
    crop_h, crop_w = arr.shape
    
    for y in range(crop_h):
        min_val = np.min(arr[y, :])
        mean_val = np.mean(arr[y, :])
        print(f"Row {y + 600}: min={min_val}, mean={mean_val:.1f}")

if __name__ == "__main__":
    crop_and_analyze_date()
