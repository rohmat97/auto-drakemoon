"""CLI entry point for the 2D Minigame Coin Shuffle Tracker."""

import argparse
import os
import sys
from typing import Iterator, Optional, Tuple
import cv2
import numpy as np

# Ensure sibling imports work when invoked as `python coin_shuffle_tracker/main.py` or `python main.py`
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from config import DEFAULT_CONFIG, TrackerConfig
from detector import (
    BBox,
    calibrate_starting_slots,
    detect_arena_roi,
    detect_character_blobs,
    detect_initial_coin,
    select_arena_roi_manually,
    select_target_manually,
)
from tracker import ShuffleTracker
from utils import (
    draw_arena_roi,
    draw_final_banner,
    draw_slot_markers,
    draw_tracked_target,
    draw_trajectory,
    format_slot_label,
)


def _iter_video_frames(video_path: str) -> Tuple[Iterator[np.ndarray], float, Tuple[int, int]]:
    """Open a video file and yield BGR frames along with FPS and (width, height)."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video file: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def _gen() -> Iterator[np.ndarray]:
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                yield frame
        finally:
            cap.release()

    return _gen(), fps, (width, height)


def _iter_screen_frames(region: Optional[BBox] = None) -> Tuple[Iterator[np.ndarray], float, Tuple[int, int]]:
    """Live screen capture generator using mss or PIL.ImageGrab."""
    try:
        import mss  # type: ignore

        sct = mss.mss()
        monitor = (
            {"left": region[0], "top": region[1], "width": region[2], "height": region[3]}
            if region
            else sct.monitors[1]
        )
        width, height = monitor["width"], monitor["height"]

        def _gen_mss() -> Iterator[np.ndarray]:
            while True:
                raw = np.array(sct.grab(monitor))
                yield cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)

        return _gen_mss(), 20.0, (width, height)
    except ImportError:
        from PIL import ImageGrab

        bbox = (
            (region[0], region[1], region[0] + region[2], region[1] + region[3])
            if region
            else None
        )
        sample = np.array(ImageGrab.grab(bbox=bbox))
        height, width = sample.shape[:2]

        def _gen_pil() -> Iterator[np.ndarray]:
            while True:
                img = np.array(ImageGrab.grab(bbox=bbox))
                yield cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        return _gen_pil(), 15.0, (width, height)


def _parse_roi(roi_str: str) -> BBox:
    parts = [int(p.strip()) for p in roi_str.split(",")]
    if len(parts) != 4:
        raise ValueError("--roi must be formatted as x,y,w,h")
    return (parts[0], parts[1], parts[2], parts[3])


def run_pipeline(
    video_path: Optional[str] = None,
    output_path: Optional[str] = None,
    manual_roi: Optional[BBox] = None,
    select_roi: bool = False,
    show_preview: bool = True,
    cfg: TrackerConfig = DEFAULT_CONFIG,
) -> int:
    """
    Execute the 4-phase Coin Shuffle Tracker pipeline and return the final 1-indexed slot (1-5).
    """
    if video_path:
        frames, fps, (frame_w, frame_h) = _iter_video_frames(video_path)
    else:
        frames, fps, (frame_w, frame_h) = _iter_screen_frames(manual_roi)

    writer: Optional[cv2.VideoWriter] = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps, (frame_w, frame_h))

    arena_roi: Optional[BBox] = manual_roi or cfg.arena_roi
    slot_xs = []
    tracker: Optional[ShuffleTracker] = None
    last_annotated: Optional[np.ndarray] = None
    coin_wait_frames = 0

    try:
        for frame_idx, frame in enumerate(frames):
            vis = frame.copy()

            # Phase 1: Arena & Starting Slot Calibration
            if arena_roi is None:
                if select_roi:
                    arena_roi = select_arena_roi_manually(frame)
                else:
                    arena_roi = detect_arena_roi(frame, cfg)
                    if arena_roi is None:
                        arena_roi = (0, 0, frame_w, frame_h)
                        print("[Phase 1] Auto arena detection missed; using full frame ROI.")
                    else:
                        print(f"[Phase 1] Auto-detected Arena ROI: {arena_roi}")

            if not slot_xs:
                slot_xs, start_bboxes = calibrate_starting_slots(frame, arena_roi, cfg)
                print(
                    f"[Phase 1] Calibrated {len(slot_xs)} slots: "
                    + ", ".join(f"S{i+1}={x:.1f}" for i, x in enumerate(slot_xs))
                )

            # Phase 2: Initial Coin Detection
            if tracker is None:
                cur_bboxes = detect_character_blobs(frame, arena_roi, cfg)
                coin_bbox, target_idx = detect_initial_coin(frame, arena_roi, cur_bboxes, cfg)

                if coin_bbox is not None and target_idx is not None:
                    target_bbox = cur_bboxes[target_idx]
                    tracker = ShuffleTracker(
                        arena_roi=arena_roi,
                        slot_x_positions=slot_xs,
                        cfg=cfg,
                        fps=fps,
                    )
                    tracker.initialize(frame, target_bbox, cur_bboxes, target_idx)
                    print(
                        f"[Phase 2] Coin detected at frame {frame_idx} -> "
                        f"Locked onto {format_slot_label(target_idx + 1, cfg)} "
                        f"(Backend: {tracker.tracker_backend})"
                    )
                else:
                    coin_wait_frames += 1
                    if show_preview and coin_wait_frames > int(fps * 4):
                        target_bbox, manual_idx = select_target_manually(frame, cur_bboxes)
                        tracker = ShuffleTracker(
                            arena_roi=arena_roi,
                            slot_x_positions=slot_xs,
                            cfg=cfg,
                            fps=fps,
                        )
                        tracker.initialize(frame, target_bbox, cur_bboxes, manual_idx)
                        print(f"[Phase 2] Manual target locked (Backend: {tracker.tracker_backend}).")
            else:
                # Phase 3: Track target character through jumps & swaps
                tracker.update(frame)

            # Visual overlay
            draw_arena_roi(vis, arena_roi)
            draw_slot_markers(vis, slot_xs, arena_roi)
            if tracker is not None:
                draw_trajectory(vis, tracker.trajectory)
                draw_tracked_target(vis, tracker.target_bbox, label="COIN")

            last_annotated = vis
            if writer is not None:
                writer.write(vis)

            if show_preview:
                cv2.imshow("Coin Shuffle Tracker", vis)
                key = cv2.waitKey(max(1, int(round(1000.0 / fps)))) & 0xFF
                if key in (27, ord("q")):
                    break

        if tracker is None:
            raise RuntimeError(
                "Coin was never detected in the video. Try --select-roi or adjusting HSV thresholds in config.py."
            )

        # Phase 4: Final Slot Resolution & Output Banner
        final_slot = tracker.resolve_final_slot()
        result_text = format_slot_label(final_slot, cfg)
        print("=" * 60)
        print(f"FINAL RESULT: {result_text}")
        print("=" * 60)

        if last_annotated is not None:
            draw_final_banner(last_annotated, final_slot, cfg)
            if writer is not None:
                # Hold final result banner for 1 second in output video
                for _ in range(max(1, int(round(fps)))):
                    writer.write(last_annotated)
            if show_preview:
                cv2.imshow("Coin Shuffle Tracker", last_annotated)
                cv2.waitKey(2000)

        return final_slot
    finally:
        if writer is not None:
            writer.release()
        if show_preview:
            cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser(description="2D Minigame Coin Shuffle Tracker")
    parser.add_argument("--video", type=str, default=None, help="Path to input video file")
    parser.add_argument("--output", type=str, default=None, help="Optional path to save debug video")
    parser.add_argument("--roi", type=str, default=None, help="Manual Arena ROI as x,y,w,h")
    parser.add_argument("--select-roi", action="store_true", help="Interactively select Arena ROI")
    parser.add_argument("--no-preview", action="store_true", help="Disable live OpenCV preview window")
    args = parser.parse_args()

    manual_roi = _parse_roi(args.roi) if args.roi else None
    run_pipeline(
        video_path=args.video,
        output_path=args.output,
        manual_roi=manual_roi,
        select_roi=args.select_roi,
        show_preview=not args.no_preview,
    )


if __name__ == "__main__":
    main()
