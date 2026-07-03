# find_formation_coords.py
import cv2
import numpy as np
import os
import glob

def find_template(target_path, template_path):
    target = cv2.imread(target_path)
    template = cv2.imread(template_path)
    if target is None or template is None:
        return None
        
    h, w = template.shape[:2]
    res = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.95
    loc = np.where(res >= threshold)
    
    matches = []
    for pt in zip(*loc[::-1]):
        matches.append((pt[0], pt[1], pt[0] + w, pt[1] + h))
    return matches

def main():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resource_dir = os.path.join(project_dir, 'Resource')
    template_path = os.path.join(resource_dir, '080808.bmp')
    
    print(f"Scanning for template: {template_path}")
    if not os.path.exists(template_path):
        print("Template file 080808.bmp not found!")
        return

    # Find all BMP images in Resource directory
    bmp_files = glob.glob(os.path.join(resource_dir, '*.bmp'))
    for bmp_file in bmp_files:
        if os.path.basename(bmp_file) == '080808.bmp':
            continue
        # Skip small assets
        if os.path.getsize(bmp_file) < 500000:
            continue
            
        print(f"\nChecking: {os.path.basename(bmp_file)}")
        matches = find_template(bmp_file, template_path)
        if matches:
            for m in matches[:5]: # Print first few matches
                print(f"  Found match at: {m}")
        else:
            print("  No match found.")

if __name__ == '__main__':
    main()
