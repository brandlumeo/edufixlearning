from PIL import Image
import os

def scale_cofounder():
    path = r"c:\Users\M S I\Desktop\edufixlearn\static\images\Cofounder.PNG"
    img = Image.open(path)
    img_small = img.resize((597, 800))
    out = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\cofounder_small.png"
    img_small.save(out, "PNG")
    print("Saved cofounder_small.png successfully!")

if __name__ == '__main__':
    scale_cofounder()
