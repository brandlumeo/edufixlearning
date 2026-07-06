from PIL import Image
import numpy as np
import os

def crop_both_signatures():
    src = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg"
    img = Image.open(src)
    
    # 1. Circle Only (Handwriting circle only)
    # Circle is roughly X: 590 to 670, Y: 575 to 630 on 1024x723 image
    # Let's crop tightly around it:
    circle_box = (590, 572, 665, 626)
    circle_crop = img.crop(circle_box)
    
    # Convert and make transparent
    circle_rgba = circle_crop.convert("RGBA")
    np_arr1 = np.array(circle_rgba)
    r1, g1, b1 = np_arr1[:,:,0], np_arr1[:,:,1], np_arr1[:,:,2]
    mask1 = (r1 > 220) & (g1 > 220) & (b1 > 220)
    np_arr1[mask1] = [255, 255, 255, 0]
    circle_result = Image.fromarray(np_arr1, 'RGBA')
    
    circle_path = r"c:\Users\M S I\Desktop\edufixlearn\static\images\rasal_handwritten_circle.png"
    circle_result.save(circle_path, "PNG")
    
    # 2. Full Block (Circle + RASAL FARHAN + FOUNDER & CEO)
    # Box including everything, starting Y below the body text but high enough
    # Y starts at 572 (above circle) to 665 (below FOUNDER & CEO)
    # X from 555 to 705
    full_box = (555, 572, 705, 665)
    full_crop = img.crop(full_box)
    
    full_rgba = full_crop.convert("RGBA")
    np_arr2 = np.array(full_rgba)
    r2, g2, b2 = np_arr2[:,:,0], np_arr2[:,:,1], np_arr2[:,:,2]
    mask2 = (r2 > 220) & (g2 > 220) & (b2 > 220)
    np_arr2[mask2] = [255, 255, 255, 0]
    full_result = Image.fromarray(np_arr2, 'RGBA')
    
    full_path = r"c:\Users\M S I\Desktop\edufixlearn\static\images\rasal_full_sig_block.png"
    full_result.save(full_path, "PNG")
    
    # Copy both to media as well
    import shutil
    shutil.copy(circle_path, r"c:\Users\M S I\Desktop\edufixlearn\media\certificates\rasal_handwritten_circle.png")
    shutil.copy(full_path, r"c:\Users\M S I\Desktop\edufixlearn\media\certificates\rasal_full_sig_block.png")
    
    # Save copy to brain artifacts for verification
    shutil.copy(circle_path, r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\circle_preview.png")
    shutil.copy(full_path, r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\full_sig_preview.png")
    
    print("Successfully cropped and saved both signature types!")

if __name__ == '__main__':
    crop_both_signatures()
