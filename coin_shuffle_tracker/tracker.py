"""CSRT + multi-character momentum-continuity tracking with crossover guard."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import cv2
import numpy as np

try:
    from .config import DEFAULT_CONFIG, TrackerConfig
    from .detector import BBox, detect_character_blobs
except ImportError:
    from config import DEFAULT_CONFIG, TrackerConfig
    from detector import BBox, detect_character_blobs

try:
    from scipy.optimize import linear_sum_assignment  # type: ignore

    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


def create_csrt_tracker() -> Tuple[object, str]:
    """Create OpenCV CSRT tracker, falling back to legacy CSRT or MIL if needed."""
    if hasattr(cv2, "TrackerCSRT_create"):
        return cv2.TrackerCSRT_create(), "CSRT"
    if hasattr(cv2, "legacy") and hasattr(cv2.legacy, "TrackerCSRT_create"):
        return cv2.legacy.TrackerCSRT_create(), "CSRT (legacy)"
    if hasattr(cv2, "TrackerMIL_create"):
        return cv2.TrackerMIL_create(), "MIL (fallback)"
    raise RuntimeError("No supported OpenCV object tracker found. Install opencv-contrib-python.")


def _bbox_center(bbox: BBox) -> Tuple[float, float]:
    return (bbox[0] + bbox[2] / 2.0, bbox[1] + bbox[3] / 2.0)


def _solve_assignment(cost_matrix: np.ndarray) -> List[Tuple[int, int]]:
    """
    Minimum-cost 1-to-1 assignment between tracks (rows) and detections (cols).
    Uses scipy.optimize.linear_sum_assignment when available, else greedy min-cost.
    """
    if cost_matrix.size == 0:
        return []
    if _HAS_SCIPY:
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        return list(zip(row_ind.tolist(), col_ind.tolist()))

    # Pure-NumPy greedy fallback when scipy is not installed
    n_rows, n_cols = cost_matrix.shape
    pairs: List[Tuple[int, int]] = []
    used_rows = set()
    used_cols = set()
    flat_indices = np.argsort(cost_matrix, axis=None)
    for idx in flat_indices:
        r = int(idx // n_cols)
        c = int(idx % n_cols)
        if r in used_rows or c in used_cols:
            continue
        pairs.append((r, c))
        used_rows.add(r)
        used_cols.add(c)
        if len(used_rows) == n_rows or len(used_cols) == n_cols:
            break
    return pairs


@dataclass
class CharacterTrack:
    """State of a single character sprite across frames."""

    track_id: int
    bbox: BBox
    cx: float
    cy: float
    vx: float = 0.0
    vy: float = 0.0
    missed_frames: int = 0

    def predict(self) -> Tuple[float, float]:
        return (self.cx + self.vx, self.cy + self.vy)


@dataclass
class ShuffleTracker:
    """
    Tracks the coin-holding target character through jumps and crossovers.
    Combines OpenCV CSRT with 5-character momentum-continuity assignment so
    overlapping identical sprites do not steal the tracker lock.
    """

    arena_roi: BBox
    slot_x_positions: List[float]
    cfg: TrackerConfig = field(default_factory=TrackerConfig)
    fps: float = 30.0

    _csrt: Optional[object] = field(default=None, init=False)
    tracker_backend: str = field(default="", init=False)
    target_track_id: int = field(default=0, init=False)
    target_bbox: Optional[BBox] = field(default=None, init=False)
    tracks: Dict[int, CharacterTrack] = field(default_factory=dict, init=False)
    trajectory: List[Tuple[int, int]] = field(default_factory=list, init=False)
    stationary_frames: int = field(default=0, init=False)
    init_center: Optional[Tuple[float, float]] = field(default=None, init=False)
    has_moved: bool = field(default=False, init=False)
    settled: bool = field(default=False, init=False)

    def initialize(
        self,
        frame: np.ndarray,
        target_bbox: BBox,
        all_bboxes: List[BBox],
        target_index: Optional[int] = None,
    ) -> None:
        """Initialize primary CSRT tracker and all character momentum tracks."""
        self._csrt, self.tracker_backend = create_csrt_tracker()
        self._csrt.init(frame, target_bbox)
        self.target_bbox = target_bbox

        tcx, tcy = _bbox_center(target_bbox)
        self.init_center = (tcx, tcy)
        self.trajectory = [(int(round(tcx)), int(round(tcy)))]

        self.tracks.clear()
        if all_bboxes:
            for idx, bbox in enumerate(all_bboxes):
                cx, cy = _bbox_center(bbox)
                self.tracks[idx] = CharacterTrack(track_id=idx, bbox=bbox, cx=cx, cy=cy)
            if target_index is not None and target_index in self.tracks:
                self.target_track_id = target_index
            else:
                self.target_track_id = min(
                    self.tracks.keys(),
                    key=lambda tid: math.hypot(self.tracks[tid].cx - tcx, self.tracks[tid].cy - tcy),
                )
        else:
            self.tracks[0] = CharacterTrack(track_id=0, bbox=target_bbox, cx=tcx, cy=tcy)
            self.target_track_id = 0

    def _update_multi_tracks(self, detections: List[BBox]) -> None:
        """Assign detected pink-hair character blobs to existing tracks using momentum prediction."""
        if not self.tracks:
            return

        track_ids = sorted(self.tracks.keys())
        if not detections:
            for tid in track_ids:
                t = self.tracks[tid]
                px, py = t.predict()
                t.cx, t.cy = px, py
                t.bbox = (
                    int(round(px - t.bbox[2] / 2.0)),
                    int(round(py - t.bbox[3] / 2.0)),
                    t.bbox[2],
                    t.bbox[3],
                )
                t.missed_frames += 1
            return

        det_centers = [_bbox_center(b) for b in detections]
        cost = np.zeros((len(track_ids), len(detections)), dtype=np.float32)
        for r, tid in enumerate(track_ids):
            px, py = self.tracks[tid].predict()
            for c, (dcx, dcy) in enumerate(det_centers):
                cost[r, c] = math.hypot(dcx - px, dcy - py)

        matched_tracks = set()
        alpha = self.cfg.velocity_smoothing
        for r, c in _solve_assignment(cost):
            if cost[r, c] > self.cfg.max_match_distance:
                continue
            tid = track_ids[r]
            t = self.tracks[tid]
            new_cx, new_cy = det_centers[c]
            inst_vx = new_cx - t.cx
            inst_vy = new_cy - t.cy
            t.vx = alpha * inst_vx + (1.0 - alpha) * t.vx
            t.vy = alpha * inst_vy + (1.0 - alpha) * t.vy
            t.cx = new_cx
            t.cy = new_cy
            t.bbox = detections[c]
            t.missed_frames = 0
            matched_tracks.add(tid)

        # Coast unmatched tracks (e.g. temporarily occluded during a crossover jump)
        for tid in track_ids:
            if tid not in matched_tracks:
                t = self.tracks[tid]
                px, py = t.predict()
                t.cx, t.cy = px, py
                t.vx *= 0.85
                t.vy *= 0.85
                t.bbox = (
                    int(round(px - t.bbox[2] / 2.0)),
                    int(round(py - t.bbox[3] / 2.0)),
                    t.bbox[2],
                    t.bbox[3],
                )
                t.missed_frames += 1

    def update(self, frame: np.ndarray) -> Tuple[bool, Optional[BBox]]:
        """
        Advance tracking by one frame.
        Returns (ok, current_target_bbox).
        """
        if self._csrt is None or self.target_bbox is None:
            return False, None

        prev_cx, prev_cy = _bbox_center(self.target_bbox)

        # 1. Update primary CSRT tracker
        ok, raw_box = self._csrt.update(frame)
        csrt_bbox: Optional[BBox] = None
        if ok:
            x, y, w, h = (int(round(v)) for v in raw_box)
            if w > 0 and h > 0:
                csrt_bbox = (x, y, w, h)

        # 2. Update 5-character momentum tracks for crossover/occlusion protection
        detections = detect_character_blobs(frame, self.arena_roi, self.cfg)
        self._update_multi_tracks(detections)
        target_track = self.tracks.get(self.target_track_id)

        # 3. Crossover guard: re-anchor CSRT if it drifted onto a crossing sprite or failed
        if target_track is not None and target_track.missed_frames == 0:
            if csrt_bbox is None:
                csrt_bbox = target_track.bbox
                self._csrt, _ = create_csrt_tracker()
                self._csrt.init(frame, csrt_bbox)
            else:
                ccx, ccy = _bbox_center(csrt_bbox)
                drift = math.hypot(ccx - target_track.cx, ccy - target_track.cy)
                if drift > self.cfg.reanchor_distance:
                    csrt_bbox = target_track.bbox
                    self._csrt, _ = create_csrt_tracker()
                    self._csrt.init(frame, csrt_bbox)
        elif csrt_bbox is None and target_track is not None:
            csrt_bbox = target_track.bbox

        if csrt_bbox is None:
            return False, None

        self.target_bbox = csrt_bbox
        cur_cx, cur_cy = _bbox_center(csrt_bbox)
        self.trajectory.append((int(round(cur_cx)), int(round(cur_cy))))
        if len(self.trajectory) > self.cfg.trail_max_len:
            self.trajectory = self.trajectory[-self.cfg.trail_max_len :]

        # 4. Check if all movement has settled for >0.5s AFTER shuffling began
        step_dist = math.hypot(cur_cx - prev_cx, cur_cy - prev_cy)
        max_track_speed = max(
            (math.hypot(t.vx, t.vy) for t in self.tracks.values()), default=step_dist
        )
        disp_from_start = (
            math.hypot(cur_cx - self.init_center[0], cur_cy - self.init_center[1])
            if self.init_center is not None
            else 0.0
        )
        if not self.has_moved and (disp_from_start > 15.0 or max_track_speed > 4.0):
            self.has_moved = True

        if self.has_moved:
            if step_dist <= self.cfg.settle_velocity_threshold and max_track_speed <= self.cfg.settle_velocity_threshold:
                self.stationary_frames += 1
            else:
                self.stationary_frames = 0

        required_settle_frames = max(1, int(round(self.cfg.settle_seconds * self.fps)))
        if self.has_moved and self.stationary_frames >= required_settle_frames:
            self.settled = True

        return True, self.target_bbox

    def resolve_final_slot(self) -> int:
        """
        Determine the final 1-indexed slot (1 to 5, left to right) of the target character.
        Uses sorted final X-positions of all 5 tracked characters when available,
        falling back to nearest calibrated baseline slot X-position.
        """
        if self.target_bbox is None:
            return 1

        final_cx, _ = _bbox_center(self.target_bbox)

        # Prefer ranking across all 5 active character tracks left-to-right
        if len(self.tracks) == self.cfg.slot_count:
            ordered_ids = sorted(self.tracks.keys(), key=lambda tid: self.tracks[tid].cx)
            if self.target_track_id in ordered_ids:
                return ordered_ids.index(self.target_track_id) + 1

        # Fallback: compare against calibrated baseline slot X-positions
        nearest_idx = min(
            range(len(self.slot_x_positions)),
            key=lambda i: abs(self.slot_x_positions[i] - final_cx),
        )
        return nearest_idx + 1
