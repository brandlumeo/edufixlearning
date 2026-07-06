import os

def check_certificates():
    cert_dir = r"c:\Users\M S I\Desktop\edufixlearn\media\certificates"
    if os.path.exists(cert_dir):
        files = os.listdir(cert_dir)
        print("Certificates in media/certificates:")
        for f in files:
            path = os.path.join(cert_dir, f)
            print(f"  {f}: size={os.path.getsize(path)} bytes")
    else:
        print("No media/certificates directory")

if __name__ == "__main__":
    check_certificates()
