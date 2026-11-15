"""Arena calibration, character sprite detection, and initial gold coin detection."""

from typing import List, Optional, Tuple
import cv2
import numpy as np

try:
    from .config import DEFAULT_CONFIG, TrackerConfig
except ImportError:
    from config import DEFAULT_CONFIG, TrackerConfig

BBox = Tuple[int, int, int, int]  # (x, y, w, h)


def _clamp_roi(roi: BBox, frame_shape: Tuple[int, ...]) -> BBox:
    """Clamp (x, y, w, h) ROI within frame boundaries."""
    frame_h, frame_w = frame_shape[:2]
    x, y, w, h = roi
    x = max(0, min(x, frame_w - 1))
    y = max(0, min(y, frame_h - 1))
    w = max(1, min(w, frame_w - x))
    h = max(1, min(h, frame_h - y))
    return (x, y, w, h)


def detect_arena_roi(
    frame: np.ndarray, cfg: TrackerConfig = DEFAULT_CONFIG
) -> Optional[BBox]:
    """
    Auto-detect the wooden-framed grass arena by segmenting the green grass field.
    Returns (x, y, w, h) padded upward for jump arcs/coin, or None if not found.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(
        hsv,
        np.array(cfg.arena_green_lower, dtype=np.uint8),
        np.array(cfg.arena_green_upper, dtype=np.uint8),
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < cfg.min_arena_area:
        return None

    x, y, w, h = cv2.boundingRect(largest)
    # Include headroom above the grass arena for high jumps and the floating coin
    padded = (x, max(0, y - cfg.arena_top_padding), w, h + cfg.arena_top_padding)
    return _clamp_roi(padded, frame.shape)


def select_arena_roi_manually(frame: np.ndarray) -> BBox:
    """Allow the user to draw the Arena ROI interactively via cv2.selectROI."""
    roi = cv2.selectROI("Select Arena ROI (Press ENTER/SPACE)", frame, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow("Select Arena ROI (Press ENTER/SPACE)")
    x, y, w, h = (int(v) for v in roi)
    if w <= 0 or h <= 0:
        h_f, w_f = frame.shape[:2]
        return (0, 0, w_f, h_f)
    return _clamp_roi((x, y, w, h), frame.shape)


def detect_character_blobs(
    frame: np.ndarray,
    arena_roi: BBox,
    cfg: TrackerConfig = DEFAULT_CONFIG,
) -> List[BBox]:
    """
    Detect pink-haired 2D character sprites inside `arena_roi`.
    Returns bounding boxes sorted left-to-right by center X.
    """
    ax, ay, aw, ah = _clamp_roi(arena_roi, frame.shape)
    crop = frame[ay : ay + ah, ax : ax + aw]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    mask1 = cv2.inRange(
        hsv,
        np.array(cfg.pink_hair_lower_1, dtype=np.uint8),
        np.array(cfg.pink_hair_upper_1, dtype=np.uint8),
    )
    mask2 = cv2.inRange(
        hsv,
        np.array(cfg.pink_hair_lower_2, dtype=np.uint8),
        np.array(cfg.pink_hair_upper_2, dtype=np.uint8),
    )
    mask = cv2.bitwise_or(mask1, mask2)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bboxes: List[BBox] = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < cfg.min_char_hair_area or area > cfg.max_char_hair_area:
            continue
        hx, hy, hw, hh = cv2.boundingRect(cnt)
        # Expand hair bbox to approximate full character sprite box
        cx = ax + hx + hw / 2.0
        full_w = max(hw, int(round(hw * cfg.char_width_scale)))
        full_h = max(hh, int(round(hh * cfg.char_height_scale)))
        full_x = int(round(cx - full_w / 2.0))
        full_y = int(round(ay + hy - hh * cfg.char_top_pad_scale))
        bboxes.append(_clamp_roi((full_x, full_y, full_w, full_h), frame.shape))

    # Sort left-to-right by center X
    bboxes.sort(key=lambda b: b[0] + b[2] / 2.0)
    return bboxes


def calibrate_starting_slots(
    frame: np.ndarray,
    arena_roi: BBox,
    cfg: TrackerConfig = DEFAULT_CONFIG,
) -> Tuple[List[float], List[BBox]]:
    """
    Detect the 5 starting characters and record their baseline X-positions (Slots 1-5).
    If fewer or more than `cfg.slot_count` blobs are detected, evenly spaces fallback slots
    across the arena width while preserving any detected character boxes.
    """
    bboxes = detect_character_blobs(frame, arena_roi, cfg)
    if len(bboxes) == cfg.slot_count:
        slot_xs = [b[0] + b[2] / 2.0 for b in bboxes]
        return slot_xs, bboxes

    # If extra noise blobs exist, keep the `slot_count` blobs closest to the median Y row
    if len(bboxes) > cfg.slot_count:
        ys = np.array([b[1] + b[3] / 2.0 for b in bboxes])
        median_y = float(np.median(ys))
        bboxes = sorted(bboxes, key=lambda b: abs((b[1] + b[3] / 2.0) - median_y))[: cfg.slot_count]
        bboxes.sort(key=lambda b: b[0] + b[2] / 2.0)
        slot_xs = [b[0] + b[2] / 2.0 for b in bboxes]
        return slot_xs, bboxes

    # Fallback: divide arena width evenly into `slot_count` baseline X positions
    ax, _, aw, _ = arena_roi
    step = aw / float(cfg.slot_count + 1)
    slot_xs = [ax + step * (i + 1) for i in range(cfg.slot_count)]
    return slot_xs, bboxes


def detect_initial_coin(
    frame: np.ndarray,
    arena_roi: BBox,
    char_bboxes: List[BBox],
    cfg: TrackerConfig = DEFAULT_CONFIG,
) -> Tuple[Optional[BBox], Optional[int]]:
    """
    Scan above the character row inside `arena_roi` for the gold medallion/coin.
    Maps the detected coin's center X to the nearest character below it.
    Returns (coin_bbox, target_char_index) or (None, None) if not visible.
    """
    if not char_bboxes:
        return None, None

    ax, ay, aw, _ = _clamp_roi(arena_roi, frame.shape)
    min_char_y = min(b[1] for b in char_bboxes)
    search_y1 = max(ay, min_char_y - cfg.coin_search_above_px)
    search_y2 = max(search_y1 + 10, min_char_y + 15)

    crop = frame[search_y1:search_y2, ax : ax + aw]
    if crop.size == 0:
        return None, None

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(
        hsv,
        np.array(cfg.gold_coin_lower, dtype=np.uint8),
        np.array(cfg.gold_coin_upper, dtype=np.uint8),
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best_cnt = None
    best_area = 0.0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if cfg.min_coin_area <= area <= cfg.max_coin_area and area > best_area:
            best_area = area
            best_cnt = cnt

    if best_cnt is None:
        return None, None

    cx_rel, cy_rel, cw, ch = cv2.boundingRect(best_cnt)
    coin_bbox = (ax + cx_rel, search_y1 + cy_rel, cw, ch)
    coin_center_x = coin_bbox[0] + coin_bbox[2] / 2.0

    # Map coin X to the nearest character below it
    target_idx = min(
        range(len(char_bboxes)),
        key=lambda i: abs((char_bboxes[i][0] + char_bboxes[i][2] / 2.0) - coin_center_x),
    )
    return coin_bbox, target_idx


def select_target_manually(
    frame: np.ndarray, char_bboxes: List[BBox]
) -> Tuple[BBox, Optional[int]]:
    """Manual fallback using cv2.selectROI when auto coin detection fails."""
    roi = cv2.selectROI(
        "Auto-detect failed: Select Target Character (ENTER/SPACE)",
        frame,
        fromCenter=False,
        showCrosshair=True,
    )
    cv2.destroyWindow("Auto-detect failed: Select Target Character (ENTER/SPACE)")
    x, y, w, h = (int(v) for v in roi)
    if w <= 0 or h <= 0:
        raise RuntimeError("No target character ROI was selected.")
    selected = _clamp_roi((x, y, w, h), frame.shape)
    if not char_bboxes:
        return selected, None
    sel_cx = selected[0] + selected[2] / 2.0
    nearest_idx = min(
        range(len(char_bboxes)),
        key=lambda i: abs((char_bboxes[i][0] + char_bboxes[i][2] / 2.0) - sel_cx),
    )
    return selected, nearest_idx
