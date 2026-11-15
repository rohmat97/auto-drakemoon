"""Visualization helpers for bounding boxes, trajectory trails, and slot labels."""

from typing import List, Optional, Tuple
import cv2
import numpy as np

try:
    from .config import DEFAULT_CONFIG, TrackerConfig
    from .detector import BBox
except ImportError:
    from config import DEFAULT_CONFIG, TrackerConfig
    from detector import BBox


def format_slot_label(slot_num: int, cfg: TrackerConfig = DEFAULT_CONFIG) -> str:
    """Format a 1-indexed slot number into a readable rank string."""
    idx = max(0, min(slot_num - 1, len(cfg.slot_labels) - 1))
    return f"Slot {slot_num} ({cfg.slot_labels[idx]})"


def draw_arena_roi(frame: np.ndarray, arena_roi: BBox) -> None:
    """Draw the calibrated Arena ROI rectangle."""
    x, y, w, h = arena_roi
    cv2.rectangle(frame, (x, y), (x + w, y + h), (200, 180, 60), 2)
    cv2.putText(
        frame,
        "ARENA ROI",
        (x + 6, max(18, y - 6)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (200, 180, 60),
        1,
        cv2.LINE_AA,
    )


def draw_slot_markers(
    frame: np.ndarray, slot_xs: List[float], arena_roi: BBox
) -> None:
    """Draw baseline slot numbers (1 to 5) along the bottom of the arena."""
    _, ay, _, ah = arena_roi
    label_y = min(frame.shape[0] - 8, ay + ah - 8)
    for idx, sx in enumerate(slot_xs, start=1):
        ix = int(round(sx))
        cv2.line(frame, (ix, ay + ah - 22), (ix, ay + ah), (180, 180, 180), 1)
        cv2.putText(
            frame,
            f"S{idx}",
            (ix - 10, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (220, 220, 220),
            1,
            cv2.LINE_AA,
        )


def draw_trajectory(
    frame: np.ndarray,
    trajectory: List[Tuple[int, int]],
    color: Tuple[int, int, int] = (0, 255, 255),
) -> None:
    """Draw the motion trail line along the tracked character's path."""
    if len(trajectory) < 2:
        return
    for i in range(1, len(trajectory)):
        thickness = max(1, int(round(1 + 2 * (i / len(trajectory)))))
        cv2.line(frame, trajectory[i - 1], trajectory[i], color, thickness, cv2.LINE_AA)


def draw_tracked_target(
    frame: np.ndarray,
    bbox: Optional[BBox],
    label: str = "COIN",
    color: Tuple[int, int, int] = (0, 255, 0),
) -> None:
    """Draw a green bounding box and 'COIN' label on the tracked character."""
    if bbox is None:
        return
    x, y, w, h = bbox
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
    tag_y1 = max(0, y - th - 8)
    tag_y2 = max(th + 8, y)
    cv2.rectangle(frame, (x, tag_y1), (x + tw + 10, tag_y2), color, -1)
    cv2.putText(
        frame,
        label,
        (x + 5, tag_y2 - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 0, 0),
        2,
        cv2.LINE_AA,
    )


def draw_final_banner(
    frame: np.ndarray, slot_num: int, cfg: TrackerConfig = DEFAULT_CONFIG
) -> None:
    """Draw the final predicted slot banner at the top of the frame."""
    banner = f"FINAL RESULT: {format_slot_label(slot_num, cfg)}"
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 42), (20, 20, 20), -1)
    cv2.putText(
        frame,
        banner,
        (16, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 255, 120),
        2,
        cv2.LINE_AA,
    )
