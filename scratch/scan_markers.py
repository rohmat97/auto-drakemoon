# scan_markers.py
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
    threshold = 0.8  # slightly lower threshold for color template match
    loc = np.where(res >= threshold)
    
    matches = []
    for pt in zip(*loc[::-1]):
        # Keep unique coordinates by filtering close matches
        if not any(abs(pt[0] - m[0]) < 10 and abs(pt[1] - m[1]) < 10 for m in matches):
            matches.append((pt[0], pt[1], pt[0] + w, pt[1] + h))
    return matches

def main():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resource_dir = os.path.join(project_dir, 'Resource')
    
    # Target files to check
    targets = [os.path.join(resource_dir, f) for f in ['debug_bind.bmp', 'debug_inventory.bmp', 'debug_loop.bmp']]
    
    # Template files to scan for
    patterns = ['starsw.bmp', 'starnw.bmp', 'starnww.bmp', 'stare.bmp', 'starn.bmp', 'starSE.bmp', 'starsee.bmp',
                'w_a.bmp', 's_a.bmp', 'e_a.bmp', 'north_a.bmp', 'battle.bmp', 'battle2.bmp']
                
    for target in targets:
        if not os.path.exists(target):
            continue
        print(f"\nChecking target image: {os.path.basename(target)}")
        
        for pattern_name in patterns:
            pat_path = os.path.join(resource_dir, pattern_name)
            if not os.path.exists(pat_path):
                continue
            matches = find_template(target, pat_path)
            if matches:
                print(f"  Pattern '{pattern_name}' found at:")
                for m in matches:
                    print(f"    Coords: (x1={m[0]}, y1={m[1]}, x2={m[2]}, y2={m[3]})")

if __name__ == '__main__':
    main()
