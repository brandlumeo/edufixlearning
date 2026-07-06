import os

def find_all_images():
    workspace = r"c:\Users\M S I\Desktop\edufixlearn"
    extensions = ('.jpg', '.png', '.jpeg', '.gif')
    for root, dirs, files in os.walk(workspace):
        # Skip some standard directories to keep it clean
        if any(x in root for x in ['venv', '.git', '.gemini', 'staticfiles', 'node_modules']):
            continue
        for file in files:
            if file.lower().endswith(extensions):
                rel_path = os.path.relpath(os.path.join(root, file), workspace)
                size = os.path.getsize(os.path.join(root, file))
                print(f"{rel_path}: {size} bytes")

if __name__ == '__main__':
    find_all_images()
