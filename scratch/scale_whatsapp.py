from PIL import Image
import os

def scale_whatsapp_img():
    path = r"c:\Users\M S I\Desktop\edufixlearn\media\certificates\WhatsApp_Image_2026-06-16_at_9.30.25_AM.jpeg"
    if os.path.exists(path):
        img = Image.open(path)
        img_small = img.resize((700, 500))
        out = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\whatsapp_small.png"
        img_small.save(out, "PNG")
        print(f"WhatsApp image size: {img.size}, successfully scaled and saved!")
    else:
        print("WhatsApp image does not exist!")

if __name__ == '__main__':
    scale_whatsapp_img()
