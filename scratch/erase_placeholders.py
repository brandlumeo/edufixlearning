from PIL import Image

def create_cleaned_template():
    src_path = r"C:\Users\M S I\.gemini\antigravity-ide\brain\633bc64a-e32b-4860-b6a8-cf406bf8dc50\media__1782792182488.jpg"
    img = Image.open(src_path)
    # Convert to RGB to ensure we can modify pixels easily
    img = img.convert("RGB")
    
    # 1. Erase "Your Name" placeholder
    # X: 310 to 710, Y: 412 to 442
    for x in range(310, 710):
        for y in range(412, 442):
            img.putpixel((x, y), (255, 255, 255))
            
    # 2. Erase ".../.../......" date placeholder
    # X: 290 to 450, Y: 645 to 660
    for x in range(290, 450):
        for y in range(645, 660):
            img.putpixel((x, y), (255, 255, 255))
            
    # Save to the target locations
    dest1 = r"c:\Users\M S I\Desktop\edufixlearn\static\images\mobile_editing_template.jpg"
    dest2 = r"c:\Users\M S I\Desktop\edufixlearn\media\certificate_templates\mobile_editing_template.jpg"
    
    import os
    os.makedirs(os.path.dirname(dest1), exist_ok=True)
    os.makedirs(os.path.dirname(dest2), exist_ok=True)
    
    img.save(dest1, quality=95)
    img.save(dest2, quality=95)
    print(f"Saved cleaned template to:\n  {dest1}\n  {dest2}")

if __name__ == "__main__":
    create_cleaned_template()
