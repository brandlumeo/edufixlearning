from PIL import Image
import numpy as np

def crop_exact_circle_only():
    src = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg"
    img = Image.open(src)
    
    # 1. Circle only: Y from 592 to 630, X from 590 to 670
    circle_box = (590, 592, 670, 629)
    circle_only = img.crop(circle_box)
    circle_rgba = circle_only.convert("RGBA")
    np_arr = np.array(circle_rgba)
    r, g, b = np_arr[:,:,0], np_arr[:,:,1], np_arr[:,:,2]
    # Make background transparent
    mask = (r > 220) & (g > 220) & (b > 220)
    np_arr[mask] = [255, 255, 255, 0]
    result_circle = Image.fromarray(np_arr, 'RGBA')
    
    circle_path = r"c:\Users\M S I\Desktop\edufixlearn\static\images\rasal_handwritten_circle.png"
    result_circle.save(circle_path, "PNG")
    
    # Copy
    import shutil
    shutil.copy(circle_path, r"c:\Users\M S I\Desktop\edufixlearn\media\certificates\rasal_handwritten_circle.png")
    shutil.copy(circle_path, r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\circle_preview.png")
    print("Exact signature circle extracted!")

if __name__ == '__main__':
    crop_exact_circle_only()
