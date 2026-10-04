"""
Slice wide map source images into 5 vertical slices each.

Usage:
    python slice_wide_maps.py <image1_path> <image2_path>

Example:
    python slice_wide_maps.py source1.png source2.png

This will:
  1. Remove all existing wide_map* files from the tomb/ folder
  2. Slice each source image into 5 vertical slices
  3. Save as BMP: tomb/wide_map{N}.bmp + tomb/wide_map{N}_{1-5}.bmp
"""

import glob
import os
import sys

from PIL import Image

TOMB_DIR = os.path.join(os.path.dirname(__file__), 'tomb')
NUM_SLICES = 5


def clean_old_assets():
    """Remove all existing wide_map* files from tomb/."""
    removed = 0
    for f in glob.glob(os.path.join(TOMB_DIR, 'wide_map*')):
        os.remove(f)
        removed += 1
    print(f'Removed {removed} old wide_map files.')


def slice_image(src_path, map_index):
    """Slice a source image into 5 vertical slices and save as BMP."""
    img = Image.open(src_path).convert('RGB')
    w, h = img.size
    slice_w = w // NUM_SLICES

    # Save base (full) image
    base_path = os.path.join(TOMB_DIR, f'wide_map{map_index}.bmp')
    img.save(base_path, 'BMP')
    print(f'  Saved {base_path} ({w}x{h})')

    # Save 5 vertical slices
    for s in range(NUM_SLICES):
        left = s * slice_w
        right = (s + 1) * slice_w if s < NUM_SLICES - 1 else w
        crop = img.crop((left, 0, right, h))
        slice_path = os.path.join(TOMB_DIR, f'wide_map{map_index}_{s + 1}.bmp')
        crop.save(slice_path, 'BMP')
        print(f'  Saved {slice_path} ({crop.size[0]}x{crop.size[1]})')


def main():
    if len(sys.argv) < 3:
        print('Usage: python slice_wide_maps.py <image1> <image2>')
        sys.exit(1)

    os.makedirs(TOMB_DIR, exist_ok=True)
    clean_old_assets()

    for i, src in enumerate(sys.argv[1:3], start=1):
        if not os.path.isfile(src):
            print(f'ERROR: File not found: {src}')
            sys.exit(1)
        print(f'Slicing {src} -> wide_map{i}')
        slice_image(src, i)

    print('\nDone! Generated files:')
    for f in sorted(glob.glob(os.path.join(TOMB_DIR, 'wide_map*'))):
        print(f'  {f}')


if __name__ == '__main__':
    main()
