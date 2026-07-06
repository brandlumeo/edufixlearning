from PIL import Image
import numpy as np

def crop_tighter():
    src = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg"
    img = Image.open(src)
    
    # Let's crop starting from Y=596 instead of 578 to completely avoid "techniques."
    # The signature circle is around Y=596 to Y=632.
    # The text "RASAL FARHAN" is around Y=635 to Y=648.
    # "FOUNDER & CEO" is around Y=650 to Y=660.
    sig_box = (585, 595, 800, 660)
    sig_crop = img.crop(sig_box)
    
    # Save raw tighter crop for reference
    sig_crop.save(r"c:\Users\M S I\Desktop\edufixlearn\scratch\sig_tighter_raw.png")
    
    # Convert to RGBA and make white background transparent
    sig_rgba = sig_crop.convert("RGBA")
    np_arr = np.array(sig_rgba)
    r, g, b, a = np_arr[:,:,0], np_arr[:,:,1], np_arr[:,:,2], np_arr[:,:,3]
    
    # Make background transparent (white color range)
    mask = (r > 220) & (g > 220) & (b > 220)
    np_arr[mask] = [255, 255, 255, 0]
    
    result = Image.fromarray(np_arr, 'RGBA')
    out_path = r"c:\Users\M S I\Desktop\edufixlearn\static\images\rasal_farhan_signature.png"
    result.save(out_path, "PNG")
    
    import shutil
    shutil.copy(out_path, r"c:\Users\M S I\Desktop\edufixlearn\media\certificates\rasal_farhan_signature.png")
    result.save(r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\sig_tighter_transparent.png")
    print("New tight signature cropped and saved successfully!")

if __name__ == '__main__':
    crop_tighter()
