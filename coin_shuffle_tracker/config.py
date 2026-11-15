"""Tunable configuration constants for the 2D Minigame Coin Shuffle Tracker."""

from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class TrackerConfig:
    """Configuration for arena detection, HSV masks, tracking, and slot resolution."""

    slot_count: int = 5

    # Optional manual Arena ROI override: (x, y, w, h). None triggers auto-detection.
    arena_roi: Optional[Tuple[int, int, int, int]] = None

    # Grass arena HSV range (OpenCV H: 0-179, S: 0-255, V: 0-255)
    arena_green_lower: Tuple[int, int, int] = (35, 45, 45)
    arena_green_upper: Tuple[int, int, int] = (90, 255, 255)
    min_arena_area: int = 20000
    arena_top_padding: int = 40  # Extra headroom above grass for jump arcs & coin

    # Pink-haired 2D character sprite HSV ranges (wraps around H=0/179)
    pink_hair_lower_1: Tuple[int, int, int] = (140, 60, 80)
    pink_hair_upper_1: Tuple[int, int, int] = (179, 255, 255)
    pink_hair_lower_2: Tuple[int, int, int] = (0, 60, 120)
    pink_hair_upper_2: Tuple[int, int, int] = (8, 200, 255)
    min_char_hair_area: int = 60
    max_char_hair_area: int = 8000

    # Expansion multipliers to turn a detected hair blob into a full character bbox
    char_width_scale: float = 1.6
    char_height_scale: float = 2.6
    char_top_pad_scale: float = 0.2

    # Gold medallion/coin HSV range (bright gold/yellow)
    gold_coin_lower: Tuple[int, int, int] = (15, 110, 140)
    gold_coin_upper: Tuple[int, int, int] = (38, 255, 255)
    min_coin_area: int = 40
    max_coin_area: int = 5000
    coin_search_above_px: int = 90  # Vertical band above character heads to look for coin

    # Tracking & crossover guard parameters
    velocity_smoothing: float = 0.55  # Exponential moving average factor for velocity
    max_match_distance: float = 85.0  # Max px distance for frame-to-frame centroid matching
    reanchor_distance: float = 28.0  # Re-anchor CSRT if it drifts further than this from target track
    settle_seconds: float = 0.5  # Duration of near-zero motion before declaring shuffle finished
    settle_velocity_threshold: float = 2.0  # Pixels/frame considered stationary

    # Visualization settings
    trail_max_len: int = 120
    slot_labels: Tuple[str, ...] = field(
        default=(
            "1st Place (Leftmost)",
            "2nd Place",
            "3rd Place (Middle)",
            "4th Place",
            "5th Place (Rightmost / Last)",
        )
    )


DEFAULT_CONFIG = TrackerConfig()
