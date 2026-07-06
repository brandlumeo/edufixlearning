from PIL import Image
import os

def scale_and_save():
    path = r"c:\Users\M S I\Desktop\edufixlearn\static\images\ai-video-editing.png"
    img = Image.open(path)
    img_small = img.resize((732, 512))
    out = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\ai_video_editing_small.png"
    img_small.save(out, "PNG")
    print("Saved scaled image successfully!")

if __name__ == '__main__':
    scale_and_save()
