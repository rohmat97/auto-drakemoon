"""
Slice Kimoon Master monster images into 4 slices for detection in bot automation.

Usage:
    py slice_kimoon.py <img1_path> <img2_path> <img3_path>
"""

import os
import sys
from PIL import Image

KIMOON_DIR = os.path.join(os.path.dirname(__file__), 'kimoon')
NUM_SLICES = 4


def slice_images(src_paths):
    """Slice each source image into 4 slices (horizontal and vertical) and save as BMP."""
    os.makedirs(KIMOON_DIR, exist_ok=True)

    # Save base full images
    for idx, path in enumerate(src_paths, start=1):
        img = Image.open(path).convert('RGB')
        base_path = os.path.join(KIMOON_DIR, f'kimoonmaster_base{idx}.bmp')
        img.save(base_path, 'BMP')
        print(f'Saved base image {idx}: {base_path} ({img.size[0]}x{img.size[1]})')

    # Horizontal slices (1..12)
    h_idx = 1
    for img_i, src in enumerate(src_paths, start=1):
        img = Image.open(src).convert('RGB')
        w, h = img.size
        slice_h = h // NUM_SLICES
        for s in range(NUM_SLICES):
            top = s * slice_h
            bottom = (s + 1) * slice_h if s < NUM_SLICES - 1 else h
            crop = img.crop((0, top, w, bottom))
            crop.save(os.path.join(KIMOON_DIR, f'kimoonmaster{h_idx}.bmp'), 'BMP')
            crop.save(os.path.join(KIMOON_DIR, f'kimoonmaster_h{h_idx}.bmp'), 'BMP')
            print(f'  Saved horizontal slice {h_idx}: kimoonmaster{h_idx}.bmp ({crop.size[0]}x{crop.size[1]})')
            h_idx += 1

    # Vertical slices (13..24, and _v1.._v12)
    v_idx = 13
    v_rel = 1
    for img_i, src in enumerate(src_paths, start=1):
        img = Image.open(src).convert('RGB')
        w, h = img.size
        slice_w = w // NUM_SLICES
        for s in range(NUM_SLICES):
            left = s * slice_w
            right = (s + 1) * slice_w if s < NUM_SLICES - 1 else w
            crop = img.crop((left, 0, right, h))
            crop.save(os.path.join(KIMOON_DIR, f'kimoonmaster{v_idx}.bmp'), 'BMP')
            crop.save(os.path.join(KIMOON_DIR, f'kimoonmaster_v{v_rel}.bmp'), 'BMP')
            print(f'  Saved vertical slice {v_idx} (v{v_rel}): kimoonmaster{v_idx}.bmp ({crop.size[0]}x{crop.size[1]})')
            v_idx += 1
            v_rel += 1


def main():
    if len(sys.argv) < 2:
        print('Usage: py slice_kimoon.py <img1> [img2] [img3] ...')
        sys.exit(1)
    slice_images(sys.argv[1:])
    print('\nDone slicing kimoon assets!')


if __name__ == '__main__':
    main()

