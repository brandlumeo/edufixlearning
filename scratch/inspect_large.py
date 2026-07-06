from PIL import Image
import os

def inspect_large_images():
    images = ['ai-video-editing.png', 'Cofounder.PNG']
    for img_name in images:
        path = os.path.join(r"c:\Users\M S I\Desktop\edufixlearn\static\images", img_name)
        if os.path.exists(path):
            img = Image.open(path)
            print(f"{img_name}: size={img.size}, format={img.format}, mode={img.mode}")
        else:
            print(f"{img_name} does not exist")

if __name__ == '__main__':
    inspect_large_images()
