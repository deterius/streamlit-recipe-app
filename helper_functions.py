import re
from uuid import uuid4
import os
import uuid
from PIL import Image

def compute_unit_cost(unit, cost, volume_str):
    try:
        if unit == "kg":
            return cost / 1000
        elif unit == "斤":
            return cost / 500
        elif unit == "L":
            return cost / 1000
        elif unit in ["g", "ml"]:
            return cost
        elif unit in ["盒", "瓶", "包"] and volume_str:
            volume = float(volume_str)
            return cost / volume
        return None
    except:
        return None
    
    
def save_uploaded_file(uploaded_file, filename_hint=None):
    upload_dir = "uploaded_images"
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(uploaded_file.name)[-1].lower()
    
    # Sanitize the filename hint
    if filename_hint:
        safe_name = "".join(c for c in filename_hint if c.isalnum() or c in (' ', '_')).rstrip()
        unique_filename = f"{safe_name}{ext}"
    else:
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
    file_path = os.path.join(upload_dir, unique_filename)

    # Save and resize
    img = Image.open(uploaded_file)
    img.thumbnail((1024, 1024))  # Adjust size as needed
    img.save(file_path)

    return unique_filename