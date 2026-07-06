from PIL import Image
import numpy as np

def find_dark_regions():
    img = Image.open(r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg")
    w, h = img.size
    gray = img.convert('L')
    arr = np.array(gray)
    
    # "Your Name" is centered horizontally (x from 0.3*w to 0.7*w)
    # and vertically (y from 0.4*h to 0.7*h)
    # Let's find rows in this region where there are dark pixels (value < 100)
    print("Searching for 'Your Name' placeholder...")
    ys = []
    for y in range(int(h*0.4), int(h*0.7)):
        row = arr[y, int(w*0.3):int(w*0.7)]
        if np.min(row) < 100:
            ys.append(y)
            
    if ys:
        print(f"Dark pixels found in Y-range: {ys[0]} to {ys[-1]} (out of {h} pixels)")
        # Now find the X-range for these Ys
        xs = []
        for x in range(int(w*0.3), int(w*0.7)):
            col = arr[ys[0]:ys[-1]+1, x]
            if np.min(col) < 100:
                xs.append(x)
        if xs:
            print(f"X-range for 'Your Name': {xs[0]} to {xs[-1]} (out of {w} pixels)")
            
            # Map pixel coordinates to ReportLab points (841.89 x 595.28)
            # ReportLab Y = page_h - (pixel_y / img_h * page_h)
            page_w, page_h = 841.89, 595.28
            rl_x_start = xs[0] / w * page_w
            rl_x_end = xs[-1] / w * page_w
            rl_y_start = page_h - (ys[-1] / h * page_h)
            rl_y_end = page_h - (ys[0] / h * page_h)
            print(f"ReportLab coordinates: X=[{rl_x_start:.2f}, {rl_x_end:.2f}], Y=[{rl_y_start:.2f}, {rl_y_end:.2f}]")
    
    # "DATE .../.../......" placeholder is in the bottom left
    # let's look in x: 0.2*w to 0.45*w, y: 0.75*h to 0.95*h
    print("\nSearching for Date placeholder...")
    ys_date = []
    for y in range(int(h*0.75), int(h*0.95)):
        row = arr[y, int(w*0.2):int(w*0.45)]
        if np.min(row) < 100:
            ys_date.append(y)
            
    if ys_date:
        print(f"Dark pixels found in Y-range: {ys_date[0]} to {ys_date[-1]}")
        xs_date = []
        for x in range(int(w*0.2), int(w*0.45)):
            col = arr[ys_date[0]:ys_date[-1]+1, x]
            if np.min(col) < 100:
                xs_date.append(x)
        if xs_date:
            print(f"X-range for Date: {xs_date[0]} to {xs_date[-1]}")
            page_w, page_h = 841.89, 595.28
            rl_x_start = xs_date[0] / w * page_w
            rl_x_end = xs_date[-1] / w * page_w
            rl_y_start = page_h - (ys_date[-1] / h * page_h)
            rl_y_end = page_h - (ys_date[0] / h * page_h)
            print(f"ReportLab coordinates for Date: X=[{rl_x_start:.2f}, {rl_x_end:.2f}], Y=[{rl_y_start:.2f}, {rl_y_end:.2f}]")

if __name__ == "__main__":
    find_dark_regions()
