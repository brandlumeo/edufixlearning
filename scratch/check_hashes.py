import hashlib

def get_hash(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()

print("edufix_blank_template.jpg:", get_hash(r"c:\Users\M S I\Desktop\edufixlearn\static\images\edufix_blank_template.jpg"))
print("default_certificate_template.jpg:", get_hash(r"c:\Users\M S I\Desktop\edufixlearn\static\images\default_certificate_template.jpg"))
print("media/certificate_templates/edufix_blank_template.jpg:", get_hash(r"c:\Users\M S I\Desktop\edufixlearn\media\certificate_templates\edufix_blank_template.jpg"))
print("media/certificate_templates/default_edufix_template.jpg:", get_hash(r"c:\Users\M S I\Desktop\edufixlearn\media\certificate_templates\default_edufix_template.jpg"))
