from PIL import Image

def inspect_images():
    img1_path = r"c:\Users\M S I\Desktop\edufixlearn\static\images\edufix_blank_template.jpg"
    img2_path = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg"
    
    try:
        with Image.open(img1_path) as im1:
            print(f"Original template: {im1.format}, {im1.size}, {im1.mode}")
    except Exception as e:
        print("Error opening original:", e)
        
    try:
        with Image.open(img2_path) as im2:
            print(f"New uploaded image: {im2.format}, {im2.size}, {im2.mode}")
    except Exception as e:
        print("Error opening new:", e)

if __name__ == "__main__":
    inspect_images()
