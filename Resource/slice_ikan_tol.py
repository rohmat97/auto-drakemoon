"""
Slice monster image into 4 slices for detection in opposite direction.

Usage:
    py slice_ikan_tol.py <source_image_path>

Example:
    py slice_ikan_tol.py media_image.png
"""

import os
import sys
from PIL import Image

IKAN_TOL_DIR = os.path.join(os.path.dirname(__file__), 'ikan_tol')
NUM_SLICES = 4


def slice_image(src_path):
    """Slice a source image into 4 vertical slices and 4 quadrants, then save as BMP."""
    os.makedirs(IKAN_TOL_DIR, exist_ok=True)
    img = Image.open(src_path).convert('RGB')
    w, h = img.size

    # Save full base image
    base_path = os.path.join(IKAN_TOL_DIR, 'ikan_tol.bmp')
    img.save(base_path, 'BMP')
    print(f'  Saved base: {base_path} ({w}x{h})')

    # Save 4 vertical slices
    slice_w = w // NUM_SLICES
    for s in range(NUM_SLICES):
        left = s * slice_w
        right = (s + 1) * slice_w if s < NUM_SLICES - 1 else w
        crop = img.crop((left, 0, right, h))
        slice_path = os.path.join(IKAN_TOL_DIR, f'ikan_tol_{s + 1}.bmp')
        crop.save(slice_path, 'BMP')
        print(f'  Saved vertical slice {s + 1}: {slice_path} ({crop.size[0]}x{crop.size[1]})')

    # Save 4 quadrant slices (2x2 grid)
    half_w, half_h = w // 2, h // 2
    quads = [
        (0, 0, half_w, half_h),
        (half_w, 0, w, half_h),
        (0, half_h, half_w, h),
        (half_w, half_h, w, h),
    ]
    for idx, box in enumerate(quads, start=1):
        q = img.crop(box)
        q_path = os.path.join(IKAN_TOL_DIR, f'ikan_tol_q{idx}.bmp')
        q.save(q_path, 'BMP')
        print(f'  Saved quad slice {idx}: {q_path} ({q.size[0]}x{q.size[1]})')


def main():
    if len(sys.argv) < 2:
        print('Usage: py slice_ikan_tol.py <source_image_path>')
        sys.exit(1)
    src = sys.argv[1]
    if not os.path.isfile(src):
        print(f'ERROR: File not found: {src}')
        sys.exit(1)
    slice_image(src)
    print('\nDone!')


if __name__ == '__main__':
    main()
