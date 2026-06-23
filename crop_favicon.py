from PIL import Image

img_path = r"C:\Users\M S I\Desktop\edufixlearn\static\images\favicon.png"
img = Image.open(img_path)

width, height = img.size
new_size = min(width, height)

left = (width - new_size) / 2
top = (height - new_size) / 2
right = (width + new_size) / 2
bottom = (height + new_size) / 2

# Crop the center of the image
img_cropped = img.crop((left, top, right, bottom))
img_cropped.save(img_path)
print("Cropped favicon successfully.")
