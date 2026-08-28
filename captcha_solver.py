# captcha_solver.py — Automated solver for Gersang / Drakemoon captcha
import sys
import os

# Ensure safe console output for Windows cp1252
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import cv2
import numpy as np
import ddddocr
from collections import Counter

# Global OCR instances (cached for fast inference)
_OCR_BETA = None
_OCR_STD = None

def get_ocr_instances():
    global _OCR_BETA, _OCR_STD
    if _OCR_STD is None:
        try:
            _OCR_BETA = ddddocr.DdddOcr(beta=True, show_ad=False)
        except Exception:
            _OCR_BETA = None
        _OCR_STD = ddddocr.DdddOcr(show_ad=False)
    return _OCR_BETA, _OCR_STD


def auto_crop_captcha_box(img):
    """
    If the image includes surrounding game overworld/grass,
    auto-detect and crop to the inner light/white captcha rectangle.
    """
    if img is None:
        return None

    h, w = img.shape[:2]
    # Check if borders have dark/colored background
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bright = (gray > 175).astype(np.uint8) * 255
    contours, _ = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    best_box = None
    max_area = 0
    for cnt in contours:
        bx, by, bw, bh = cv2.boundingRect(cnt)
        area = bw * bh
        # The captcha box is wide and tall (at least 50% of image area if present)
        if bw > 80 and bh > 30 and area > max_area:
            best_box = (bx, by, bw, bh)
            max_area = area

    if best_box and (max_area / (w * h) > 0.35):
        bx, by, bw, bh = best_box
        # Avoid cropping if it's already the exact captcha box
        if bw >= w - 10 and bh >= h - 10:
            return img
        # Crop with a slight inset to discard border noise
        pad_x = min(3, bx)
        pad_y = min(3, by)
        return img[by + pad_y : by + bh - pad_y, bx + pad_x : bx + bw - pad_x]

    return img


def preprocess_captcha(image_input, s_thresh=35, min_area=12):
    """
    Filters out background ghost characters, diagonal lines, and translucent shapes
    by taking advantage of color saturation differences.
    """
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
    elif isinstance(image_input, np.ndarray):
        img = image_input
    else:
        return None

    if img is None:
        return None

    # Auto-crop outer game UI borders if present
    img = auto_crop_captcha_box(img)

    # Convert to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    _, s, _ = cv2.split(hsv)

    # Color difference from pure grayscale: max(R,G,B) - min(R,G,B)
    b, g, r = cv2.split(img.astype(np.int32))
    color_diff = np.maximum(np.maximum(np.abs(r - g), np.abs(g - b)), np.abs(b - r))

    # Mask: keeps pixels with color saturation or chromatic difference
    mask = ((s > s_thresh) | (color_diff > s_thresh)).astype(np.uint8) * 255

    # Remove components touching bottom boundary (e.g. mouse cursor tip) or tiny noise
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    h, w = mask.shape
    cleaned_mask = np.zeros_like(mask)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        cy = stats[i, cv2.CC_STAT_TOP]
        ch = stats[i, cv2.CC_STAT_HEIGHT]
        # Ignore small noise blobs or bottom cursor artifact
        if area >= min_area:
            # If the blob is at the very bottom border and small height, skip
            if (cy + ch >= h - 1) and (ch < 12):
                continue
            cleaned_mask[labels == i] = 255

    # Produce black text on white background (optimal for OCR)
    cleaned_img = 255 - cleaned_mask
    return cleaned_img


def solve_captcha(image_input, debug=False):
    """
    Recognize 5-character captcha code from image file path or numpy array (BGR).
    Returns recognized uppercase alphanumeric string (e.g. 'GBX1N' or '6IEP8').
    """
    ocr_beta, ocr_std = get_ocr_instances()

    char_mapping = {
        '工': 'I',
        '口': 'O',
        '日': 'B',
        '一': '1',
        'ｌ': '1',
        '｜': '1',
        ' ': ''
    }

    candidates = []

    # Multi-threshold voting ensemble for maximum accuracy
    for thresh in [28, 33, 38, 43]:
        cleaned = preprocess_captcha(image_input, s_thresh=thresh)
        if cleaned is None:
            continue

        _, buf = cv2.imencode('.png', cleaned)
        img_bytes = buf.tobytes()

        results = []
        if ocr_beta:
            try:
                results.append(ocr_beta.classification(img_bytes))
            except Exception:
                pass
        try:
            results.append(ocr_std.classification(img_bytes))
        except Exception:
            pass

        for r in results:
            if not r:
                continue
            for k, v in char_mapping.items():
                r = r.replace(k, v)
            cleaned_str = ''.join([c.upper() for c in r if c.isalnum()])
            if len(cleaned_str) == 5:
                candidates.append((cleaned_str, 3))  # Exact 5-char length bonus
            elif len(cleaned_str) > 0:
                candidates.append((cleaned_str, 1))

    if debug:
        safe_candidates = [(repr(t), w) for t, w in candidates]
        print('Captcha candidates:', candidates)

    if not candidates:
        return ''

    counts = Counter()
    for text, weight in candidates:
        counts[text] += weight

    best_match = counts.most_common(1)[0][0]
    return best_match


if __name__ == '__main__':
    test_file = sys.argv[1] if len(sys.argv) > 1 else 'Resource/train1.bmp'
    print(f'Testing solver on: {test_file}')
    result = solve_captcha(test_file, debug=True)
    print(f'Solved Captcha: {result}')

