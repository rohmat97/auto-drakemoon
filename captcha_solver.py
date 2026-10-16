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
_OCR_RAPID = None
_RAPID_INITIALIZED = False


def get_ocr_instances():
    global _OCR_BETA, _OCR_STD
    if _OCR_STD is None:
        try:
            _OCR_BETA = ddddocr.DdddOcr(beta=True, show_ad=False)
        except Exception:
            _OCR_BETA = None
        _OCR_STD = ddddocr.DdddOcr(show_ad=False)
    return _OCR_BETA, _OCR_STD


def get_rapid_instance():
    global _OCR_RAPID, _RAPID_INITIALIZED
    if not _RAPID_INITIALIZED:
        _RAPID_INITIALIZED = True
        try:
            from rapidocr_onnxruntime import RapidOCR
            _OCR_RAPID = RapidOCR()
        except Exception:
            _OCR_RAPID = None
    return _OCR_RAPID


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
    Filters out background ghost characters, diagonal lines, translucent shapes,
    and outer dialog frame borders by leveraging color saturation and component geometry.
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
    if img is None:
        return None

    # Convert to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    _, s, _ = cv2.split(hsv)

    # Color difference from pure grayscale: max(R,G,B) - min(R,G,B)
    b, g, r = cv2.split(img.astype(np.int32))
    color_diff = np.maximum(np.maximum(np.abs(r - g), np.abs(g - b)), np.abs(b - r))

    # Mask: keeps pixels with color saturation or chromatic difference
    mask = ((s > s_thresh) | (color_diff > s_thresh)).astype(np.uint8) * 255

    # Filter components to isolate actual captcha characters and strip outer borders / artifacts
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    h, w = mask.shape
    cleaned_mask = np.zeros_like(mask)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        cx = stats[i, cv2.CC_STAT_LEFT]
        cy = stats[i, cv2.CC_STAT_TOP]
        cw = stats[i, cv2.CC_STAT_WIDTH]
        ch = stats[i, cv2.CC_STAT_HEIGHT]

        # Ignore tiny noise blobs
        if area < min_area:
            continue

        # Ignore massive background components or whole-border frames
        if area > 800 or cw > w * 0.7 or ch > h * 0.7:
            continue

        touches_left = (cx <= 1)
        touches_top = (cy <= 1)
        touches_right = (cx + cw >= w - 1)
        touches_bottom = (cy + ch >= h - 1)
        touches_border = (touches_left or touches_top or touches_right or touches_bottom)
        borders_touched = sum([touches_left, touches_top, touches_right, touches_bottom])

        # Ignore components spanning multiple borders (outer dialog frame / wrapper)
        if borders_touched >= 2:
            continue

        # Ignore border edge slivers or tiny boundary noise
        if touches_border and (cw < 10 or ch < 10 or area < 35):
            continue

        # Ignore bottom/top boundary bleeds (e.g. text/cursor below or above captcha box)
        if touches_bottom and ch < 15:
            continue
        if touches_top and ch < 10:
            continue

        cleaned_mask[labels == i] = 255

    # Produce black text on white background (optimal for OCR)
    cleaned_img = 255 - cleaned_mask

    # Ensure a clean 2px pure white border so edge contact artifacts don't distort OCR
    cleaned_img[0:2, :] = 255
    cleaned_img[-2:, :] = 255
    cleaned_img[:, 0:2] = 255
    cleaned_img[:, -2:] = 255

    return cleaned_img


def solve_captcha(image_input, debug=False):
    """
    Recognize 5-character captcha code from image file path or numpy array (BGR).
    Returns recognized uppercase alphanumeric string (e.g. 'GBX1N' or '8TCZJ').
    """
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
    elif isinstance(image_input, np.ndarray):
        img = image_input
    else:
        return ''

    if img is None:
        return ''

    ocr_beta, ocr_std = get_ocr_instances()

    char_mapping = {
        '工': 'I',
        '上': 'I',
        '口': 'O',
        '日': 'B',
        '一': '1',
        'ｌ': '1',
        '｜': '1',
        '|': '1',
        '丨': '1',
        '了': 'J',
        '亅': 'J',
        '父': 'J',
        '丁': 'T',
        '下': 'T',
        '乙': 'Z',
        '匚': 'C',
        '乂': 'X',
        '&': '8',
        '只': '8',
        '七': '7',
        '+': 'X',
        ' ': ''
    }

    candidates = []

    # 1. Multi-threshold saturation voting ensemble (optimal for colored / watermarked captchas)
    for thresh in [28, 33, 38, 43]:
        cleaned = preprocess_captcha(img, s_thresh=thresh)
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
            cleaned_str = ''.join([c.upper() for c in r if c.isascii() and c.isalnum()])
            if len(cleaned_str) == 5:
                candidates.append((cleaned_str, 3))  # Exact 5-char length bonus
            elif len(cleaned_str) > 0:
                candidates.append((cleaned_str, 1))

    otsu = None
    # 2. Otsu binarization with border insets (optimal for tinted / high-contrast cards)
    for inset in [4, 6, 8]:
        h, w = img.shape[:2]
        if h > 2 * inset and w > 2 * inset:
            sub = img[inset:h-inset, inset:w-inset]
            gray = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY)
            _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            _, buf = cv2.imencode('.png', otsu)
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
                cleaned_str = ''.join([c.upper() for c in r if c.isascii() and c.isalnum()])
                if len(cleaned_str) == 5:
                    candidates.append((cleaned_str, 3))
                elif len(cleaned_str) > 0:
                    candidates.append((cleaned_str, 1))

    # 3. RapidOCR candidate integration (cross-model voting engine)
    rapid_engine = get_rapid_instance()
    if rapid_engine:
        try:
            for rapid_input in [img, otsu]:
                if rapid_input is None:
                    continue
                rapid_res, _ = rapid_engine(rapid_input)
                if rapid_res:
                    rapid_res.sort(key=lambda item: min([pt[0] for pt in item[0]]))
                    raw_text = ''.join([item[1] for item in rapid_res])
                    for k, v in char_mapping.items():
                        raw_text = raw_text.replace(k, v)
                    cleaned_str = ''.join([c.upper() for c in raw_text if c.isascii() and c.isalnum()])
                    if len(cleaned_str) == 5:
                        candidates.append((cleaned_str, 3))
                    elif len(cleaned_str) > 0:
                        candidates.append((cleaned_str, 1))
        except Exception:
            pass

    if debug:
        print('Captcha candidates:', candidates)

    if not candidates:
        return ''

    # Positional voting consensus across 5-char predictions
    five_char_candidates = [(text, weight) for text, weight in candidates if len(text) == 5]
    if five_char_candidates:
        consensus_chars = []
        for pos in range(5):
            pos_counts = Counter()
            for text, weight in five_char_candidates:
                pos_counts[text[pos]] += weight
            consensus_chars.append(pos_counts.most_common(1)[0][0])
        return ''.join(consensus_chars)

    # Fallback to standard weighted frequency count
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

