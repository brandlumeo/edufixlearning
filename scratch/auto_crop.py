from PIL import Image
import numpy as np

def auto_detect_and_crop():
    src = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg"
    img = Image.open(src)
    w, h = img.size
    
    # Crop a region around the signature: X from 570 to 680, Y from 570 to 670
    region_box = (570, 570, 680, 670)
    crop_reg = img.crop(region_box)
    
    # Find blue/dark pixels in this cropped region
    # Background is white (near 255). Let's convert to grayscale
    gray = crop_reg.convert("L")
    arr = np.array(gray)
    
    # Anything with gray value < 200 is part of the signature/writing
    ys, xs = np.where(arr < 200)
    
    # We want to exclude any text at the very top (which would have y near 0 in cropped region)
    # The text "techniques." ends above the signature circle.
    # Let's inspect the y coordinates that have dark pixels.
    # Signature circle is a large clump of dark pixels.
    # Let's find the y starting index that belongs to the circle.
    # Typically, the text "techniques." will be in the top 15 pixels of the crop.
    # Let's filter out pixels where Y (in regional coordinates) < 22 to ignore the "techniques." text.
    valid_indices = ys >= 22
    circle_ys = ys[valid_indices]
    circle_xs = xs[valid_indices]
    
    min_y_reg = int(np.min(circle_ys))
    max_y_reg = int(np.max(circle_ys))
    min_x_reg = int(np.min(circle_xs))
    max_x_reg = int(np.max(circle_xs))
    
    # Map back to global coordinates:
    circle_box_global = (
        region_box[0] + min_x_reg - 2,
        region_box[1] + min_y_reg - 2,
        region_box[0] + max_x_reg + 2,
        region_box[1] + max_y_reg + 2
    )
    
    print("Auto-detected circle box:", circle_box_global)
    
    circle_only = img.crop(circle_box_global)
    circle_rgba = circle_only.convert("RGBA")
    np_arr = np.array(circle_rgba)
    r, g, b = np_arr[:,:,0], np_arr[:,:,1], np_arr[:,:,2]
    # Make background transparent
    mask = (r > 220) & (g > 220) & (b > 220)
    np_arr[mask] = [255, 255, 255, 0]
    
    result_circle = Image.fromarray(np_arr, 'RGBA')
    circle_path = r"c:\Users\M S I\Desktop\edufixlearn\static\images\rasal_handwritten_circle.png"
    result_circle.save(circle_path, "PNG")
    
    # Also save to media
    import shutil
    shutil.copy(circle_path, r"c:\Users\M S I\Desktop\edufixlearn\media\certificates\rasal_handwritten_circle.png")
    shutil.copy(circle_path, r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\circle_preview.png")
    
    # 2. For the Full Signature Block, we can use global Y from (region_box[1] + min_y_reg) to 670
    # and X from 555 to 705
    full_sig_box = (555, region_box[1] + min_y_reg - 2, 705, 670)
    print("Full signature box:", full_sig_box)
    full_only = img.crop(full_sig_box)
    full_rgba = full_only.convert("RGBA")
    np_arr2 = np.array(full_rgba)
    r2, g2, b2 = np_arr2[:,:,0], np_arr2[:,:,1], np_arr2[:,:,2]
    mask2 = (r2 > 220) & (g2 > 220) & (b2 > 220)
    np_arr2[mask2] = [255, 255, 255, 0]
    
    result_full = Image.fromarray(np_arr2, 'RGBA')
    full_path = r"c:\Users\M S I\Desktop\edufixlearn\static\images\rasal_full_sig_block.png"
    result_full.save(full_path, "PNG")
    
    shutil.copy(full_path, r"c:\Users\M S I\Desktop\edufixlearn\media\certificates\rasal_full_sig_block.png")
    shutil.copy(full_path, r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\full_sig_preview.png")
    
    print("Auto-detection and crop completed perfectly!")

if __name__ == '__main__':
    auto_detect_and_crop()
