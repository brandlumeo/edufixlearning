from PIL import Image
import numpy as np

def compare_borders():
    img_orig = Image.open(r"c:\Users\M S I\Desktop\edufixlearn\static\images\edufix_blank_template.jpg")
    img_new = Image.open(r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg")
    
    # Resize new image to 1600x1130 for direct comparison
    img_new_res = img_new.resize((1600, 1130))
    
    # Let's check a small region on the left border (e.g. x: 0 to 100, y: 100 to 200)
    box = (0, 100, 100, 200)
    crop_orig = img_orig.crop(box)
    crop_new = img_new_res.crop(box)
    
    arr_orig = np.array(crop_orig)
    arr_new = np.array(crop_new)
    
    diff = np.abs(arr_orig.astype(float) - arr_new.astype(float))
    mean_diff = np.mean(diff)
    print(f"Mean pixel difference in left border (0, 100, 100, 200): {mean_diff:.2f}")

if __name__ == "__main__":
    compare_borders()
