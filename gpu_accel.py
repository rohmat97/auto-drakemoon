# gpu_accel.py — OpenCL GPU acceleration helper (AMD Radeon RX 6600 / OpenCV UMat)

import os
from typing import List, Optional, Tuple
import cv2
import numpy as np

_GPU_INITIALIZED = False
_GPU_ACTIVE = False
_GPU_DEVICE_NAME = "CPU"


def init_gpu_opencl(device_spec: str = "AMD:GPU:0") -> Tuple[bool, str]:
    """
    Initialize OpenCV OpenCL (T-API / UMat) targeting the discrete GPU
    (defaults to AMD:GPU:0 -> AMD Radeon RX 6600 on this machine).
    Safe to call multiple times; falls back cleanly to CPU if OpenCL is unavailable.
    """
    global _GPU_INITIALIZED, _GPU_ACTIVE, _GPU_DEVICE_NAME
    if _GPU_INITIALIZED:
        return _GPU_ACTIVE, _GPU_DEVICE_NAME

    if not os.environ.get("OPENCV_OPENCL_DEVICE"):
        os.environ["OPENCV_OPENCL_DEVICE"] = device_spec

    try:
        if cv2.ocl.haveOpenCL():
            cv2.ocl.setUseOpenCL(True)
            if cv2.ocl.useOpenCL():
                dev = cv2.ocl.Device.getDefault()
                _GPU_ACTIVE = True
                _GPU_DEVICE_NAME = f"{dev.vendorName()} {dev.name()}"
                # Limit OpenCV CPU worker threads so compute stays focused on the GPU
                cv2.setNumThreads(1)
                print(f"[GPU] ✅ OpenCL enabled on {_GPU_DEVICE_NAME} (CPU threads capped to 1)")
            else:
                _GPU_ACTIVE = False
                _GPU_DEVICE_NAME = "CPU (OpenCL disabled)"
        else:
            _GPU_ACTIVE = False
            _GPU_DEVICE_NAME = "CPU (no OpenCL)"
    except Exception as e:
        _GPU_ACTIVE = False
        _GPU_DEVICE_NAME = f"CPU (OpenCL error: {e})"
        print(f"[GPU] ⚠️ OpenCL init warning: {e}")

    _GPU_INITIALIZED = True
    return _GPU_ACTIVE, _GPU_DEVICE_NAME


class GpuTemplateMatcher:
    """
    Loads a pipe-separated DaMo template list (e.g. 'dark_gujimo\\main1.bmp|...')
    into GPU memory (cv2.UMat grayscale) once, and runs concentric zone matching
    on the GPU with a single frame capture per scan.
    """

    def __init__(self, resource_path: str, templates_pipe: str, threshold: float = 0.80):
        self.resource_path = resource_path
        self.threshold = threshold
        self.templates: List[Tuple[str, object, int, int]] = []  # (name, UMat, w, h)
        self._gpu_active, self._device_name = init_gpu_opencl()
        self._load_templates(templates_pipe)

    def _load_templates(self, templates_pipe: str) -> None:
        self.templates.clear()
        for rel in templates_pipe.split("|"):
            rel = rel.strip()
            if not rel:
                continue
            full_path = os.path.join(self.resource_path, rel)
            if not os.path.exists(full_path):
                continue
            img = cv2.imread(full_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            th, tw = img.shape[:2]
            tpl_mat = cv2.UMat(img) if self._gpu_active else img
            self.templates.append((rel, tpl_mat, tw, th))

    def warmup(self) -> None:
        """Prime OpenCL kernels once at startup so the first real scan is instant."""
        if not self.templates:
            return
        dummy = np.zeros((200, 320), dtype=np.uint8)
        u_dummy = cv2.UMat(dummy) if self._gpu_active else dummy
        for _, tpl_mat, tw, th in self.templates:
            if tw <= 320 and th <= 200:
                cv2.minMaxLoc(cv2.matchTemplate(u_dummy, tpl_mat, cv2.TM_CCOEFF_NORMED))
                break

    def find_in_frame(
        self,
        frame_gray: np.ndarray,
        zones: List[Tuple[int, int, int, int]],
        threshold: Optional[float] = None,
    ) -> Tuple[int, int]:
        """
        Match loaded templates against `frame_gray` across concentric `zones`
        on the GPU. Returns (x, y) center of first match above threshold, or (0, 0).
        """
        if not self.templates or frame_gray is None:
            return 0, 0
        thr = self.threshold if threshold is None else threshold
        fh, fw = frame_gray.shape[:2]
        # Upload full frame to GPU ONCE and slice zones directly in GPU memory
        u_full = cv2.UMat(frame_gray) if self._gpu_active else frame_gray

        for zx1, zy1, zx2, zy2 in zones:
            x1 = max(0, min(zx1, fw - 1))
            y1 = max(0, min(zy1, fh - 1))
            x2 = max(x1 + 1, min(zx2, fw))
            y2 = max(y1 + 1, min(zy2, fh))
            rw, rh = x2 - x1, y2 - y1
            u_roi = cv2.UMat(u_full, (y1, y2), (x1, x2)) if self._gpu_active else frame_gray[y1:y2, x1:x2]

            for _, tpl_mat, tw, th in self.templates:
                if tw > rw or th > rh:
                    continue
                res = cv2.matchTemplate(u_roi, tpl_mat, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                if max_val >= thr:
                    return x1 + max_loc[0] + tw // 2, y1 + max_loc[1] + th // 2

        return 0, 0

    def find_with_dm(
        self,
        dm,
        zones: List[Tuple[int, int, int, int]],
        temp_path: str,
        threshold: Optional[float] = None,
    ) -> Tuple[int, int]:
        """Capture once via DaMo and run GPU template matching across `zones`."""
        if not self.templates:
            return 0, 0
        dm.Capture(0, 0, 1024, 768, temp_path)
        if not os.path.exists(temp_path):
            return 0, 0
        frame_gray = cv2.imread(temp_path, cv2.IMREAD_GRAYSCALE)
        if frame_gray is None:
            return 0, 0
        return self.find_in_frame(frame_gray, zones, threshold=threshold)


_MATCHER_CACHE = {}


def find_monster_gpu(
    dm,
    monster_images: str,
    zones: List[Tuple[int, int, int, int]],
    threshold: float = 0.80,
    fallback_sim: float = 0.8,
    is_in_battle_func=None,
) -> Tuple[int, int]:
    """
    Global reusable GPU monster search (OpenCL UMat on AMD RX 6600) with
    automatic fallback to dm.FindPic. Caches GpuTemplateMatcher per
    (resource_path, monster_images) so callers need zero boilerplate.
    """
    try:
        res_path = dm.getPath()
        cache_key = (res_path, monster_images, threshold)
        matcher = _MATCHER_CACHE.get(cache_key)
        if matcher is None:
            matcher = GpuTemplateMatcher(res_path, monster_images, threshold=threshold)
            matcher.warmup()
            _MATCHER_CACHE[cache_key] = matcher
        if matcher.templates:
            if is_in_battle_func is not None and is_in_battle_func():
                return 0, 0
            temp_path = os.path.join(res_path, f"temp_gpu_scan_{os.getpid()}.bmp")
            return matcher.find_with_dm(dm, zones, temp_path, threshold=threshold)
    except Exception as e:
        print(f"[GPU] ⚠️ Falling back to dm.FindPic for monster search: {e}")

    for zx1, zy1, zx2, zy2 in zones:
        if is_in_battle_func is not None and is_in_battle_func():
            return 0, 0
        (_, x, y) = dm.FindPic(zx1, zy1, zx2, zy2, monster_images, "050505", fallback_sim, 0)
        if x > 0:
            return x, y
    return 0, 0


def to_umat(arr: np.ndarray):
    """Wrap a NumPy array in cv2.UMat when OpenCL GPU is active."""
    active, _ = init_gpu_opencl()
    return cv2.UMat(arr) if active else arr


def find_pic_gpu(
    dm,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    templates_pipe: str,
    threshold: float = 0.78,
    fallback_sim: float = 0.70,
) -> Tuple[int, int]:
    """
    Single-region GPU template match (OpenCL UMat) with automatic dm.FindPic fallback.
    Returns (x, y) center on match, or (-1, -1) if not found.
    """
    mx, my = find_monster_gpu(
        dm,
        templates_pipe,
        [(x1, y1, x2, y2)],
        threshold=threshold,
        fallback_sim=fallback_sim,
    )
    if mx > 0 and my > 0:
        return mx, my
    return -1, -1
