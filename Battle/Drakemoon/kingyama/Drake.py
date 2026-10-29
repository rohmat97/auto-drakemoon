# Drake.py — Main entrypoint and orchestrator (Fire Gwi / King Yama)

import gc
import os
import sys
import time
import threading
from tkinter import messagebox

# ---------------------------------------------------------------------------
# Path bootstrapping (ensure local and project modules can be imported)
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

import keyboard

from PyGameAuto.Dm import RegDm
from config import (
    DM_REG_KEY, DM_REG_CODE,
    FORMATION_REGIONS, MONSTER_DIRECTION_REGIONS, MONSTER_CHECKS,
)
from window_manager import move_game_window, bind_game_window
from session_scheduler import SessionScheduler, SessionConfig
import Battle.Drakemoon.kingyama.combat as combat_module
import Battle.Drakemoon.kingyama.combat2 as combat2_module
import Battle.Drakemoon.kingyama.combat3 as combat3_module
from Battle.Drakemoon.kingyama.combat import (
    check_revive, has_non_black_in_region, check_formation,
    execute_battle_strategy, initial_call, initiation_battle,
    execute_skill_loop, STRATEGIES as STRATEGIES_1,
)
from Battle.Drakemoon.kingyama.combat2 import (
    execute_battle_strategy2, STRATEGIES as STRATEGIES_2,
)
from Battle.Drakemoon.kingyama.combat3 import (
    execute_battle_strategy3, STRATEGIES as STRATEGIES_3,
)
import game_actions
from game_actions import (
    relogin,
    check_food as base_check_food,
    check_anti_cheat,
    check_pending_anti_cheat_relog,
    check_stamina as base_check_stamina,
    stop_battle,
    is_mercenary_dead,
    ensure_mercenaries_recovered,
    check_and_execute_opposite_monster,
    OPPOSITE_MONSTER_REGION,
    OPPOSITE_TARGET_POSITION,
    OPPOSITE_MONSTER_IMAGES,
    OPPOSITE_MONSTER_REGION_2,
    OPPOSITE_TARGET_POSITION_2,
    OPPOSITE_MONSTER_IMAGES_2,
)

# ---------------------------------------------------------------------------
# Constants & Key Mappings
# ---------------------------------------------------------------------------
KEY_ESC = 27
KEY_ENTER = 13
KEY_1 = 49

DIRECTION_KEYS = {
    'West': 39,   # Arrow Right
    'East': 37,   # Arrow Left
    'North': 40,  # Arrow Down
    'South': 38,  # Arrow Up
}

# Image patterns
MONSTER_IMAGES = '|'.join([rf'kingyama\koh{i}.bmp' for i in range(1, 43)])
DRAKE_IMAGES = '|'.join([rf'Character\drakemoon\drake{i}.bmp' for i in range(1, 12)])
EMERGENCY_EXIT_IMAGES = '|'.join([rf'kingyama\emergency_exit{i}.bmp' for i in range(1, 10)] + [r'kingyama\emergency_exit.bmp'])

# Concentric monster search regions: search center outward to corners
MONSTER_SEARCH_ZONES = [
    (352, 242, 672, 442),  # Zone 1: Center (immediate proximity to player)
    (222, 162, 802, 522),  # Zone 2: Mid-range
    (0, 0, 1024, 768),     # Zone 3: Full window (corners)
]

# Stamina / Food Bar Check Configuration
# Position: 99, 671, 115, 679 | Color: #76b936
STAMINA_CHECK_REGION = (99, 671, 115, 679)
STAMINA_GREEN_COLOR = '76b936'
STAMINA_FOOD_IMAGES = 'drake_food.bmp|food.bmp'

# Grinding Session & Break Guidelines Configuration
BATTLES_BEFORE_BREAK_MIN = 400
BATTLES_BEFORE_BREAK_MAX = 500
BATTLES_PER_BATCH_RELOG = 500
BATTLES_PER_FRESH_START = 20
BREAK_DURATION_MIN_SECONDS = 1 * 60   # 1 minute (60s)
BREAK_DURATION_MAX_SECONDS = 3 * 60  # 3 minutes (180s)


# ---------------------------------------------------------------------------
# State Management
# ---------------------------------------------------------------------------
class BotState:
    """Encapsulates runtime state for the automation bot."""

    def __init__(self):
        self.paused = False
        self.game_hwnd = 0
        self.last_monster_seen_time = time.time()
        self.no_monster_search_count = 0
        self.last_revive_check = 0.0
        # Performance & throttling caches
        self.last_stamina_check = 0.0
        self.last_anti_cheat_check = 0.0
        self.engage_fail_count = 0
        self.last_mercenary_check = 0.0
        self.cached_mercenary_status = (False, [])

    def is_paused(self) -> bool:
        return self.paused

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def toggle_pause(self) -> bool:
        self.paused = not self.paused
        return self.paused

    def invalidate_mercenary_cache(self) -> None:
        """Force the next mercenary health check to query the screen directly."""
        self.last_mercenary_check = 0.0
        self.cached_mercenary_status = (False, [])


state = BotState()


# ---------------------------------------------------------------------------
# Precomputed Combat Memory & Possibility Engine (Zero In-Battle Latency)
# ---------------------------------------------------------------------------
class CombatMemoryCache:
    """
    Precomputes, pre-renders, and memoizes combat parameters, possibility matrices,
    minimap coordinate grids, and asset caches before battle or monster engagement.
    Eliminates in-battle re-computation and disk I/O, serving all queries directly from RAM.
    """

    def __init__(self):
        self.warmed_up = False

        # 1. Precomputed formations: tuple of (direction_name, region1_tuple, region2_tuple)
        self.formations = tuple(
            (dir_name, tuple(regions[0]), tuple(regions[1]))
            for dir_name, regions in FORMATION_REGIONS.items()
        )

        # 2. Precomputed monster candidates per formation (filters out self-direction)
        self.monster_candidates = {
            direction: tuple(m for m in MONSTER_CHECKS.get(direction, []) if m != direction)
            for direction in FORMATION_REGIONS
        }

        # 3. Precomputed minimap pixel sampling points & thresholds for each direction
        # Step = 2, threshold = 0.015 (1.5%)
        self.minimap_grids = {}
        for m_dir, (x1, y1, x2, y2) in MONSTER_DIRECTION_REGIONS.items():
            pts = tuple((px, py) for py in range(y1, y2 + 1, 2) for px in range(x1, x2 + 1, 2))
            total_pts = len(pts)
            min_non_black = max(1, int(total_pts * 0.015))
            self.minimap_grids[m_dir] = (pts, min_non_black, total_pts)

        # 4. Precomputed Strategy Possibility Matrix
        # Key: (formation, monster_dir, wave_index) -> callable strategy function
        self.strategy_dispatch = {}
        strats_1 = getattr(combat_module, 'STRATEGIES', STRATEGIES_1)
        strats_2 = getattr(combat2_module, 'STRATEGIES', STRATEGIES_2)
        strats_3 = getattr(combat3_module, 'STRATEGIES', STRATEGIES_3)
        strat_default_1 = getattr(combat_module, 'execute_battle_strategy', execute_battle_strategy)
        strat_default_2 = getattr(combat2_module, 'execute_battle_strategy2', execute_battle_strategy2)
        strat_default_3 = getattr(combat3_module, 'execute_battle_strategy3', execute_battle_strategy3)

        for form in FORMATION_REGIONS:
            for m_dir in MONSTER_CHECKS.get(form, []):
                strat_1 = strats_1.get((form, m_dir)) or (lambda dm, f=form, m=m_dir: strat_default_1(dm, f, m))
                strat_2 = strats_2.get((form, m_dir)) or (lambda dm, f=form, m=m_dir: strat_default_2(dm, f, m))
                strat_3 = strats_3.get((form, m_dir)) or (lambda dm, f=form, m=m_dir: strat_default_3(dm, f, m))

                self.strategy_dispatch[(form, m_dir, 0)] = strat_1
                self.strategy_dispatch[(form, m_dir, 1)] = strat_2
                self.strategy_dispatch[(form, m_dir, 2)] = strat_3

        # Fast dark-color set for pixel activity checks
        self.dark_colors = frozenset({'000000', '080808', '050505', '070707', '0a0a0a', '0b0b0b'})

        # Cached asset strings to prevent repeated string formatting
        self.asset_strings = (
            MONSTER_IMAGES,
            DRAKE_IMAGES,
            EMERGENCY_EXIT_IMAGES,
            'battle.bmp|battle3.bmp',
            '080808.bmp',
            OPPOSITE_MONSTER_IMAGES,
            OPPOSITE_MONSTER_IMAGES_2,
            STAMINA_FOOD_IMAGES,
            'revivedrake.bmp',
        )

    def is_pixel_active_fast(self, color_hex: str, dark_threshold: int = 30) -> bool:
        if not color_hex or len(color_hex) < 6 or color_hex in self.dark_colors:
            return False
        try:
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            return r > dark_threshold or g > dark_threshold or b > dark_threshold
        except ValueError:
            return False

    def has_non_black_fast(self, dm, monster_dir: str) -> bool:
        """
        Ultra-fast minimap check using precomputed sampling points
        and early-exit as soon as the non-black threshold is satisfied.
        """
        grid_info = self.minimap_grids.get(monster_dir)
        if not grid_info:
            return False
        points, min_non_black, total_pts = grid_info

        non_black_count = 0
        get_color = dm.GetColor
        is_active = self.is_pixel_active_fast

        for px, py in points:
            c = get_color(px, py)
            if is_active(c):
                non_black_count += 1
                if non_black_count >= min_non_black:
                    return True
        return False

    def get_strategy(self, formation: str, monster_dir: str, wave_index: int):
        """Retrieve pre-resolved strategy callable directly from memory cache."""
        fn = self.strategy_dispatch.get((formation, monster_dir, wave_index))
        if fn is not None:
            return fn
        fn = self.strategy_dispatch.get((formation, monster_dir, 0))
        if fn is not None:
            return fn
        return lambda dm: execute_battle_strategy(dm, formation, monster_dir)

    def warmup(self, dm) -> None:
        """
        Pre-render and prime all functions, templates, and bitmaps into RAM and OS cache.
        Runs once at startup and ensures zero disk/parsing latency during combat.
        """
        print('[Combat Cache] ⚡ Pre-rendering and computing combat functions & possibility matrices into memory...')
        try:
            # 1. Warm up DaMo template cache by querying off-screen (0, 0, 1, 1) with each asset
            for asset in self.asset_strings:
                dm.FindPic(0, 0, 1, 1, asset, '050505', 0.9, 0)

            # 2. Warm up GetColor COM dispatch
            dm.GetColor(0, 0)

            self.warmed_up = True
            print(
                f'[Combat Cache] ✅ Memory cache ready: {len(self.formations)} formations, '
                f'{len(self.minimap_grids)} minimap regions, {len(self.strategy_dispatch)} strategy routes precomputed.'
            )
        except Exception as e:
            print(f'[Combat Cache] ⚠️ Warmup encountered warning: {e}')

    def prepare_before_engage(self, dm) -> None:
        """
        Instant pre-battle verification right before engaging a monster.
        Pre-heats battle screen check so transition detection has zero disk/decode latency.
        """
        if not self.warmed_up:
            self.warmup(dm)
        # Touch battle.bmp template in cache
        dm.FindPic(959, 666, 960, 667, 'battle.bmp|battle3.bmp', '050505', 0.75, 0)


combat_cache = CombatMemoryCache()


# ---------------------------------------------------------------------------
# Helper Routines
# ---------------------------------------------------------------------------
class BattleWatcher:
    """
    Intense background battle detector.
    Runs in its own dedicated thread with its OWN DM instance (COM STA).
    Monitors region (959, 666, 1016, 747) for 'battle.bmp|battle3.bmp' at high frequency
    (10-20ms interval, 50-100Hz) without blocking the main execution thread.
    Exposes instant global battle state so other functions never have to perform
    blocking FindPic calls or wait on slow loops.
    """

    def __init__(self, interval: float = 0.015):
        self.interval = interval
        self.in_battle = False
        self.running = False
        self.detected = threading.Event()
        self._stop = threading.Event()
        self._thread = None

    def start(self, hwnd, resource_path: str) -> None:
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, args=(hwnd, resource_path), daemon=True, name='BattleWatcher'
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def wait_for_battle(self, timeout: float = 1.0) -> bool:
        """Wait up to `timeout` seconds for battle mode to become active."""
        if self.in_battle:
            return True
        return self.detected.wait(timeout)

    def _run(self, hwnd, resource_path: str) -> None:
        import pythoncom
        pythoncom.CoInitialize()
        wdm = None
        try:
            wdm = RegDm.reg()
            wdm.reg(DM_REG_KEY, DM_REG_CODE)
            # Display-only binding: GDI read mode, no mouse/keyboard hooks
            if wdm.BindWindow(hwnd, 'gdi', 'normal', 'normal', 0) != 1:
                print('[BattleWatcher] ⚠️ Bind failed, falling back to synchronous battle checks.')
                return
            wdm.setPath(resource_path)
            self.running = True
            print('[BattleWatcher] ⚡ Intense background battle detection started (60Hz+).')

            while not self._stop.is_set():
                if not state.is_paused():
                    try:
                        (_, x, _) = wdm.FindPic(959, 666, 1016, 747, 'battle3.bmp', '050505', 0.5, 0)
                        active = (x > 0)
                        self.in_battle = active
                        if active:
                            self.detected.set()
                        else:
                            self.detected.clear()
                    except Exception:
                        pass
                self._stop.wait(self.interval)
        except Exception as e:
            print(f'[BattleWatcher] Error: {e}. Falling back to synchronous checks.')
        finally:
            self.running = False
            self.in_battle = False
            self.detected.clear()
            try:
                if wdm is not None:
                    wdm.UnBindWindow()
            except Exception:
                pass
            pythoncom.CoUninitialize()


battle_watcher = BattleWatcher(interval=0.015)


def is_in_battle(dm=None) -> bool:
    """
    Global battle state check.
    Returns True if the game is currently on the battle screen.
    Directly reads the high-frequency BattleWatcher with zero latency and zero COM overhead.
    Falls back to synchronous FindPic if the watcher is not active.
    """
    if battle_watcher.running:
        return battle_watcher.in_battle
    if dm is not None:
        try:
            (_, x, _) = dm.FindPic(959, 666, 1016, 747, 'battle.bmp|battle3.bmp', '050505', 0.75, 0)
            return x > 0
        except Exception:
            return False
    return False


# Wire global battle state to game_actions module so all sub-actions benefit from instant check
game_actions.is_in_battle = is_in_battle


def interruptible_sleep(seconds: float, step: float = 0.05) -> bool:
    """
    Sleep for `seconds`, but immediately return True if battle mode is detected.
    Returns True if battle mode interrupted the sleep, False if full duration elapsed.
    """
    end = time.time() + seconds
    while time.time() < end:
        if is_in_battle():
            return True
        time.sleep(min(step, max(0.001, end - time.time())))
    return is_in_battle()


def select_unit_1(dm, delay_ms: int = 25) -> None:
    """Press '1' twice to select the primary mercenary group."""
    dm.KeyPress(KEY_1)
    dm.Delay(delay_ms)
    dm.KeyPress(KEY_1)
    dm.Delay(delay_ms)


_last_stamina_eat_time = 0.0


def is_stamina_green(dm) -> bool:
    """
    Checks if region (99, 671, 115, 679) contains green color #76b936.
    Returns True if green is present, False if not green.
    """
    x1, y1, x2, y2 = STAMINA_CHECK_REGION
    # 1. DaMo native FindColor for 76b936 with color tolerance
    (_, fx, _) = dm.FindColor(x1, y1, x2, y2, f'{STAMINA_GREEN_COLOR}-202020', 0.8, 0)
    if fx > 0:
        return True

    # 2. Pixel sampling check in region (99, 671, 115, 679)
    get_color = dm.GetColor
    for px in range(x1, x2 + 1, 2):
        for py in (671, 678, 674, 675):
            c = get_color(px, py)
            if c:
                try:
                    r = int(c[0:2], 16)
                    g = int(c[2:4], 16)
                    b = int(c[4:6], 16)
                    if abs(r - 0x76) <= 35 and abs(g - 0xb9) <= 40 and abs(b - 0x36) <= 30:
                        return True
                    if g >= 85 and g > r + 15 and g > b + 20:
                        return True
                except ValueError:
                    pass

    return False


def eat_stamina(dm, times: int = 2) -> bool:
    """
    Consumes stamina/food by opening inventory ('i'), searching for
    food item (drake_food.bmp / food.bmp), right-clicking it `times` times,
    and then closing inventory ('i').
    Returns True if successfully eaten, False if food item not found.
    """
    if is_in_battle(dm):
        return False
    print(f'[Stamina] 🍱 Consuming stamina/food {times} times via inventory...')
    inv_open = False
    for _ in range(5):
        (_, bx, by) = dm.FindPic(0, 0, 1024, 768, 'break_inventory_bag.bmp|bag.bmp', '101010', 0.75, 0)
        if bx > 0:
            inv_open = True
            break
        dm.KeyPress(73)  # 'i' key
        dm.Delay(500)

    if not inv_open:
        print('[Stamina] ⚠️ Failed to open inventory!')
        return False

    print('[Stamina] Inventory opened. Searching for food item (drake_food.bmp / food.bmp)...')
    (_, fx, fy) = dm.FindPic(0, 0, 1024, 768, STAMINA_FOOD_IMAGES, '101010', 0.75, 0)
    if fx > 0:
        print(f'[Stamina] Food item detected at ({fx}, {fy}). Right-clicking {times} times...')
        dm.MoveTo(fx + 5, fy + 5)
        dm.Delay(150)
        for _ in range(times):
            dm.RightClick()
            dm.Delay(250)
        # Close inventory
        dm.KeyPress(73)  # 'i' key
        dm.Delay(400)
        print(f'[Stamina] ✅ Successfully consumed stamina item {times} times.')
        return True
    else:
        print(f'[Stamina] ⚠️ Food item ({STAMINA_FOOD_IMAGES}) not detected in inventory!')
        # Close inventory
        dm.KeyPress(73)  # 'i' key
        dm.Delay(400)
        return False


def check_food_or_stamina(dm) -> bool:
    """
    Checks if region (99, 671, 115, 679) is not green #76b936.
    If not green (or 0 stamina):
        Consumes stamina item 2 times via inventory.
    Also handles empty food dialog popup.
    Returns True if script should pause (food exhausted / stamina depleted), False otherwise.
    """
    global _last_stamina_eat_time

    # Do not perform inventory operations if currently in battle
    if is_in_battle(dm):
        return False

    # Check that overworld HUD is present (bread icon visible).
    # If not on overworld (battle screen, loading screen, transition), skip stamina checks.
    (_, x_bread, _) = dm.FindPic(43, 644, 101, 692, 'bread.bmp', '050505', 0.8, 0)
    if x_bread <= 0:
        return False

    # Check for empty food popup
    (_, x_empty, _) = dm.FindPic(450, 350, 680, 480, 'emptyfoodinter.bmp|emptyfooddrake.bmp', '050505', 0.8, 0)
    if x_empty > 0:
        print('[Stamina] ⚠️ Empty food popup detected! Pausing script...')
        state.pause()
        dm.UnBindWindow()
        messagebox.showwarning('Food Depleted', 'Food/Satiety depleted! Script paused.')
        return True

    # Check zero-stamina icon (nostamina.bmp)
    (_, x_no_stamina, _) = dm.FindPic(90, 695, 99, 703, 'nostamina.bmp', '050505', 1, 0)
    zero_stamina = (x_no_stamina >= 0)

    # Check if region (99, 671, 115, 679) contains green #76b936
    green_present = is_stamina_green(dm)

    if not green_present or zero_stamina:
        now = time.time()
        # Cooldown of 3 seconds to avoid consecutive rapid inventory toggles
        if now - _last_stamina_eat_time > 3.0:
            status_str = f'Region {STAMINA_CHECK_REGION} is NOT green (#{STAMINA_GREEN_COLOR})' if not zero_stamina else '0 stamina icon detected'
            print(f'[Stamina] 📉 {status_str}. Eating stamina 2 times...')
            success = eat_stamina(dm, times=8)
            _last_stamina_eat_time = time.time()

            if not success:
                print('[Stamina] ⛔ Food item missing from inventory! Pausing script...')
                state.pause()
                dm.UnBindWindow()
                messagebox.showwarning('No Food', 'Stamina depleted and food item not found in inventory! Pausing...')
                return True
            else:
                # Allow HUD to update and verify new state
                time.sleep(0.5)
                if is_stamina_green(dm):
                    print(f'[Stamina] 📈 Replenished! Green color #{STAMINA_GREEN_COLOR} restored at {STAMINA_CHECK_REGION}.')
                return False

    return False


def check_food(dm):
    """Check food/stamina bar and consume food if needed, pausing if food is exhausted."""
    return check_food_or_stamina(dm)


def check_stamina(dm):
    """Check food/stamina bar and consume food if needed, pausing if food is exhausted."""
    return check_food_or_stamina(dm)


def check_mercenary_dead_cached(dm, max_age: float = 0.4) -> tuple:
    """
    Checks mercenary status with a short-lived cache (default 0.4s).
    Drastically reduces disk I/O, cv2 image decodes, and numpy calculations
    when multiple routines inspect mercenary health in the same tick.
    """
    now = time.time()
    if now - state.last_mercenary_check < max_age:
        return state.cached_mercenary_status
    status = is_mercenary_dead(dm, DRAKE_IMAGES)
    state.last_mercenary_check = now
    state.cached_mercenary_status = status
    return status


def check_anti_cheat_throttled(dm, interval: float = 1.0, **kwargs) -> bool:
    """
    Throttles anti-cheat checking during overworld roaming or wait loops.
    Avoids running multiple fullscreen FindPic scans on every 150ms tick
    while maintaining sub-second detection latency.
    """
    if captcha_watcher.detected.is_set():
        return captcha_guard(dm)
    now = time.time()
    if now - state.last_anti_cheat_check < interval:
        return False
    state.last_anti_cheat_check = now
    return check_anti_cheat(dm, **kwargs)


def check_stamina_throttled(dm, interval: float = 1.5) -> bool:
    """
    Throttles stamina checks to avoid repeatedly testing colors and popups every 150ms.
    Stamina depletes over several minutes, so a 1.5s interval is completely safe and responsive.
    """
    now = time.time()
    if now - state.last_stamina_check < interval:
        return False
    state.last_stamina_check = now
    return check_food_or_stamina(dm)


class CaptchaWatcher:
    """
    Background captcha detector.
    Runs in its own thread with its OWN DM instance (DM is a COM object and
    cannot be shared across threads). It only *detects* the captcha dialog
    (display-only binding, no input) and raises a flag. The main thread then
    solves it, because solving needs exclusive mouse/keyboard control.
    """

    CAPTCHA_CHECKS = (
        (300, 150, 750, 350, r'anti_cheat\detect_captcha.bmp', 0.8),
        (0, 0, 1024, 768, r'anti_cheat\detect_captcha.bmp', 0.8),
        (350, 450, 550, 530, r'anti_cheat\ok.bmp', 0.75),
        (350, 415, 600, 560, r'anti_cheat\renewal.bmp', 0.7),
    )

    def __init__(self, interval: float = 0.5):
        self.interval = interval
        self.detected = threading.Event()
        self.running = False
        self._stop = threading.Event()
        self._thread = None

    def start(self, hwnd, resource_path: str) -> None:
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, args=(hwnd, resource_path), daemon=True, name='CaptchaWatcher'
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def _run(self, hwnd, resource_path: str) -> None:
        import pythoncom
        pythoncom.CoInitialize()
        wdm = None
        try:
            wdm = RegDm.reg()
            wdm.reg(DM_REG_KEY, DM_REG_CODE)
            # Display-only binding: no mouse/keyboard hooks, so it won't fight the main DM
            if wdm.BindWindow(hwnd, 'gdi', 'normal', 'normal', 0) != 1:
                print('[CaptchaWatcher] ⚠️ Bind failed, falling back to synchronous captcha checks.')
                return
            wdm.setPath(resource_path)
            self.running = True
            print('[CaptchaWatcher] ✅ Background captcha detection started.')

            while not self._stop.is_set():
                if not state.is_paused() and not self.detected.is_set():
                    for x1, y1, x2, y2, pic, sim in self.CAPTCHA_CHECKS:
                        (_, x, y) = wdm.FindPic(x1, y1, x2, y2, pic, '101010', sim, 0)
                        if x >= 0:
                            print(f'[CaptchaWatcher] 🚨 Captcha detected at ({x}, {y}) [{pic}]')
                            self.detected.set()
                            break
                self._stop.wait(self.interval)
        except Exception as e:
            print(f'[CaptchaWatcher] Error: {e}. Falling back to synchronous captcha checks.')
        finally:
            self.running = False
            try:
                if wdm is not None:
                    wdm.UnBindWindow()
            except Exception:
                pass
            pythoncom.CoUninitialize()


captcha_watcher = CaptchaWatcher(interval=0.5)


def captcha_guard(dm) -> bool:
    """
    Non-blocking captcha check. MUST be called before pressing ESC,
    otherwise ESC can close the captcha dialog before it is detected/solved.
    - If the background watcher is running: only reads its flag (instant).
      Solving only happens when the watcher has flagged a captcha.
    - If the watcher is not running: falls back to a synchronous check.
    Returns True if a captcha was detected and handled.
    """
    if captcha_watcher.running:
        if not captcha_watcher.detected.is_set():
            return False
        captcha_watcher.detected.clear()
    state.last_anti_cheat_check = time.time()
    return check_anti_cheat(dm)


def safe_stop_battle(dm, max_wait_sec: int = 15) -> bool:
    """
    Same as stop_battle, but checks for the captcha dialog between ESC presses
    so the captcha is solved instead of being dismissed by ESC.
    """
    end_time = time.time() + max_wait_sec
    while time.time() < end_time:
        captcha_guard(dm)
        if not is_in_battle():
            print('[Battle] ✅ Successfully exited battle.')
            return True
        stop_battle(dm, max_wait_sec=1)
    return not is_in_battle()


def emergency_exit_game_and_terminal(dm):
    """
    Forcefully terminates both the game application window (Gersang) and the terminal.
    Triggered when the emergency target image is detected during monster search or engagement.
    """
    print('\n' + '=' * 65)
    print('🚨 [EMERGENCY EXIT] Danger target detected on screen!')
    print('🚨 Force closing game window and terminal immediately...')
    print('=' * 65 + '\n')

    try:
        battle_watcher.stop()
        captcha_watcher.stop()
    except Exception:
        pass

    # 1. Unbind DaMo hook
    try:
        dm.UnBindWindow()
    except Exception:
        pass

    # 2. Terminate the game process
    killed = False
    if state.game_hwnd:
        try:
            import win32process
            _, pid = win32process.GetWindowThreadProcessId(state.game_hwnd)
            if pid > 0:
                print(f'🚨 Terminating game process (PID: {pid})...')
                os.system(f'taskkill /F /PID {pid} /T >nul 2>&1')
                killed = True
        except Exception as e:
            print(f'Error killing game by PID: {e}')

    if not killed:
        print('🚨 Terminating Gersang.exe by process name...')
        os.system('taskkill /F /IM Gersang.exe /T >nul 2>&1')

    # 3. Kill parent terminal and current Python process
    try:
        print('🚨 Terminating parent terminal...')
        os.kill(os.getppid(), 9)
    except Exception as e:
        print(f'Error killing parent terminal: {e}')

    sys.exit(0)


def check_emergency_exit_target(dm):
    """
    Checks if danger target is visible on screen.
    If detected, terminates game window and terminal immediately.
    """
    (_, ex, ey) = dm.FindPic(0, 0, 1024, 768, EMERGENCY_EXIT_IMAGES, '050505', 0.8, 0)
    if ex > 0:
        print(f'🚨 Danger target spotted at ({ex}, {ey})!')
        emergency_exit_game_and_terminal(dm)
        return True
    return False


# ---------------------------------------------------------------------------
# Overworld: find and engage a monster
# ---------------------------------------------------------------------------
def find_and_engage_monster(dm) -> bool:
    """
    Search for a monster on the overworld and attempt to enter battle.
    Returns True if battle was entered, False otherwise.
    """
    # If already in battle screen, immediately return True so main loop routes to handle_battle
    if is_in_battle():
        return True

    current_time = time.time()

    # Periodic check for main character revive prompt every 5 seconds
    if current_time - state.last_revive_check > 5.0:
        state.last_revive_check = current_time
        if check_revive(dm, state.is_paused):
            print('[Overworld] Main character revival sequence completed. Ready for exploration.')
            state.invalidate_mercenary_cache()
            return False

    # Check for danger target before searching
    check_emergency_exit_target(dm)

    # Check if any mercenary is dead before searching monsters (uses short-lived cache)
    is_dead, dead_slots = check_mercenary_dead_cached(dm, max_age=0.4)
    if is_dead:
        print(f'[Overworld] ⚠️ Dead mercenary detected ({dead_slots})! Halting monster search to revive first...')
        if not ensure_mercenaries_recovered(dm, DRAKE_IMAGES):
            print('[Overworld] ⛔ Dead mercenary could not be recovered yet! Standing by...')
        state.invalidate_mercenary_cache()
        return False

    if is_in_battle():
        return True

    # Search concentric zones from center outward
    x, y = 0, 0
    for zx1, zy1, zx2, zy2 in MONSTER_SEARCH_ZONES:
        if is_in_battle():
            return True
        (_, x, y) = dm.FindPic(zx1, zy1, zx2, zy2, MONSTER_IMAGES, '050505', 0.5, 0)
        if x > 0:
            break

    if x <= 0:
        if current_time - state.last_monster_seen_time > 5:
            state.no_monster_search_count += 1
            print(f'[Active] Searching for monsters on overworld... ({state.no_monster_search_count}/10)')
            state.last_monster_seen_time = current_time
            if state.no_monster_search_count >= 10:
                print('No monsters found 10 times, pressing ESC to dismiss any popups...')
                if captcha_guard(dm):
                    state.no_monster_search_count = 0
                    return False
                dm.KeyPress(KEY_ESC)
                dm.Delay(200)
                state.no_monster_search_count = 0
        time.sleep(0.005)  # Minimal yield to keep scan loop blazing fast at high CPU
        return is_in_battle()

    state.no_monster_search_count = 0
    state.last_monster_seen_time = time.time()
    print(f'Monster found at coords: ({x}, {y})')

    # Check for danger target before engaging
    check_emergency_exit_target(dm)

    # Ensure all mercenaries are alive before moving/clicking (uses short-lived cache)
    is_dead, dead_slots = check_mercenary_dead_cached(dm, max_age=0.4)
    if is_dead:
        print(f'[Overworld] ⚠️ Monster found, but dead mercenary detected ({dead_slots})! Aborting chase to revive first...')
        ensure_mercenaries_recovered(dm, DRAKE_IMAGES)
        state.invalidate_mercenary_cache()
        return False

    if is_in_battle():
        return True

    # Pre-render and prepare combat cache before engagement
    combat_cache.prepare_before_engage(dm)

    # Engage monster rapidly
    dm.MoveTo(x, y)
    dm.Delay(50)
    dm.RightClick()
    dm.Delay(100)

    print('Waiting to enter battle screen (intense watcher)...')
    # Instant detection via background watcher without blocking main loop or waiting on timeouts
    if battle_watcher.wait_for_battle(timeout=1.0):
        print('✅ Successfully entered battle screen')
        state.engage_fail_count = 0
        return True

    if is_in_battle():
        print('✅ Successfully entered battle screen')
        state.engage_fail_count = 0
        return True

    state.engage_fail_count += 1
    print(f'[Overworld] Battle not entered ({state.engage_fail_count}/5).')
    if state.engage_fail_count >= 5:
        print('[Overworld] ⚠️ Stuck engaging monster. Dismissing popups and moving cursor away to recover...')
        if captcha_guard(dm):
            state.engage_fail_count = 0
            return False
        state.engage_fail_count = 0

    return is_in_battle()


# ---------------------------------------------------------------------------
# Battle phase routines: find formation, find monsters, and execute battle
# ---------------------------------------------------------------------------
def find_formation(dm) -> str | None:
    """
    Step 1: Check formation using precomputed formation regions.
    Cross-verifies against minimap unit presence and resolves West/North overlap
    so dark terrain at bottom-left cannot misidentify North formation as West.
    Returns the detected direction ('East', 'South', 'North', 'West') or None.
    """
    matched = []
    for direction, r1, r2 in combat_cache.formations:
        if check_formation(dm, r1, r2):
            matched.append(direction)

    if not matched:
        return None

    # If both North and West matched (e.g. dark patch at bottom-left during North formation),
    # North's top-right region (935, 100, 1004, 238) guarantees the formation is North.
    if 'North' in matched and 'West' in matched:
        return 'North'

    # Cross-check with minimap: our own mercenaries always produce active pixels
    # in our formation's minimap region.
    for direction in matched:
        if combat_cache.has_non_black_fast(dm, direction):
            return direction

    # If minimap dots haven't rendered yet on this tick, when only 'West' matched
    # double-check that 'North' does not have our unit dots while 'West' is empty.
    if matched == ['West'] and combat_cache.has_non_black_fast(dm, 'North'):
        if check_formation(dm, *FORMATION_REGIONS['North']):
            return 'North'

    return matched[0]


def find_monsters(dm, direction: str, timeout: float = 1.0) -> list[str]:
    """
    Step 2: Scan minimap regions for monsters corresponding to the detected formation.
    Rule: A monster can NEVER be on the same side as our own formation.
    Uses precomputed coordinate grids and early-exit to eliminate recomputation.
    Returns a list of monster direction names found.
    """
    print(f'Scanning {direction} formation for monsters (memory cache)...')
    found_monsters = []
    candidates = combat_cache.monster_candidates.get(direction, ())
    start_time = time.time()
    while time.time() - start_time < timeout:
        for monster_dir in candidates:
            if combat_cache.has_non_black_fast(dm, monster_dir):
                if monster_dir not in found_monsters:
                    found_monsters.append(monster_dir)
                    print(f'Monster found at direction: {monster_dir} (cached scan)')
                if len(found_monsters) >= 2:
                    break
        if len(found_monsters) >= 2:
            break
        time.sleep(0.02)
    return found_monsters


def execute_battle(dm, direction: str, found_monsters: list[str]) -> bool:
    """
    Step 3: Execute initial battle commands and combat strategies for all detected monsters.
    Sends directional key, calls initial and initiation sequences, selects primary unit,
    and executes appropriate battle strategies sequentially from memory cache.
    Uses high-frequency active polling so battle exits the instant monsters are cleared.
    Returns True if strategies were executed.
    """
    if not found_monsters:
        return False

    duration = 15 if found_monsters else 10
    key_code = DIRECTION_KEYS.get(direction)
    if key_code is not None:
        dm.KeyDown(key_code)
        dm.Delay(300)
        dm.KeyUp(key_code)

    initial_call(dm)
    initiation_battle(dm)
    select_unit_1(dm, delay_ms=25)

    # Execute battle strategy for each found monster directly from memory cache
    print(f'Total monsters found: {len(found_monsters)} -> {found_monsters}')
    for i, monster_dir in enumerate(found_monsters):
        if not is_in_battle():
            print(f'[Battle] Battle finished before executing strategy [{i+1}/{len(found_monsters)}] ({monster_dir}). Stopping.')
            break
        print(f'Executing strategy [{i+1}/{len(found_monsters)}] → Formation: {direction} | Monster: {monster_dir} (cached dispatch)')
        strategy_fn = combat_cache.get_strategy(direction, monster_dir, i)
        strategy_fn(dm)

        if i < len(found_monsters) - 1:
            wait_time = 0 if i in (0, 1) else duration
            wait_time = max(0, wait_time)
            if wait_time > 0:
                print(f'Waiting {wait_time}s before next strategy (active polling)...')
                wait_end = time.time() + wait_time
                while time.time() < wait_end:
                    if not is_in_battle():
                        print(f'[Battle] Battle finished during inter-strategy wait [{i+1}]. Stopping.')
                        return True
                    check_anti_cheat_throttled(dm, interval=1.0)
                    time.sleep(0.01)  # 100Hz responsive check
            select_unit_1(dm, delay_ms=25)
        else:
            # Active polling during final strategy: exit immediately when battle screen ends
            print(f'Waiting up to {duration}s for battle to complete (active polling)...')
            wait_end = time.time() + duration
            while time.time() < wait_end:
                if not is_in_battle():
                    print('[Battle] Battle finished early!')
                    break
                check_anti_cheat_throttled(dm, interval=1.0)
                time.sleep(0.01)  # 100Hz responsive check

            # When duration is reached, actively press ESC to exit battle immediately
            if is_in_battle():
                print(f'[Battle] Reached {duration}s duration. Pressing Esc to exit battle...')
                safe_stop_battle(dm, max_wait_sec=15)

    return True


def handle_battle(dm) -> None:
    """Process a single battle until it ends with low latency scanning."""
    print('Entered battle screen')
    action_executed = False
    empty_scan_rounds = 0
    max_empty_scan_rounds = 2  # Exit battle after 2 unsuccessful scan checks

    # Brief delay for battle screen and minimap to settle
    time.sleep(0.1)
    dm.MoveTo(640, 425)

    while True:
        if state.is_paused():
            time.sleep(0.5)
            gc.collect()
            continue

        if action_executed:
            print('Waiting for battle screen to close...')
            wait_end_time = time.time() + 12.0
            # Actively wait for battle to end naturally
            while is_in_battle() and time.time() < wait_end_time:
                check_anti_cheat_throttled(dm, interval=1.0)
                time.sleep(0.02)

            # If still in battle after timeout, try pressing Esc to close
            if is_in_battle():
                print('[Battle] Battle still active after wait timeout. Attempting to exit with Esc...')
                safe_stop_battle(dm, max_wait_sec=12)

            print('Battle screen ended')
            break

        # Check if battle ended (double check with small delay to avoid false exit on UI flicker)
        if not is_in_battle():
            time.sleep(0.05)
            if not is_in_battle():
                print('Battle screen ended')
                break

        # Step 1: Detect formation
        direction = find_formation(dm)
        if direction:
            # Step 2: Detect monsters for this formation
            found_monsters = find_monsters(dm, direction, timeout=1.0)

            # Step 3: Execute battle strategy if monsters were confirmed
            if found_monsters:
                action_executed = execute_battle(dm, direction, found_monsters)
                continue
            else:
                # Check opposite direction monster if no monsters found in formation
                print(f'No monsters found in {direction} formation on minimap. Checking opposite direction...')
                if check_and_execute_opposite_monster(dm, initiation_battle, execute_skill_loop, 12):
                    action_executed = True
                    break
        else:
            # Check monster in opposite direction if formation detection was inconclusive
            print('[Battle] Formation detection inconclusive. Checking opposite direction...')
            if check_and_execute_opposite_monster(dm, initiation_battle, execute_skill_loop):
                action_executed = True
                stop_battle(dm, 1)
                continue

        if not action_executed:
            empty_scan_rounds += 1
            print(f'[Battle] No monsters found (check {empty_scan_rounds}/{max_empty_scan_rounds})...')
            if empty_scan_rounds >= max_empty_scan_rounds:
                print(f'[Battle] 🛑 Monsters not found after {empty_scan_rounds} checks. Quitting battle...')
                safe_stop_battle(dm, max_wait_sec=10)
                break
            time.sleep(0.05)


# ---------------------------------------------------------------------------
# Hotkeys Setup
# ---------------------------------------------------------------------------
def setup_hotkeys(dm, hwnd) -> None:
    """Registers global hotkeys for pause/resume (Delete) and restart (Page Up)."""
    last_toggle_time = 0.0

    def on_pause_press(event=None):
        nonlocal last_toggle_time
        current_time = time.time()
        if current_time - last_toggle_time < 0.3:
            return
        if event.name and event.name.lower() in ('delete',):
            last_toggle_time = current_time
            is_now_paused = state.toggle_pause()
            if is_now_paused:
                print('All commands paused, press Delete to resume...')
                dm.UnBindWindow()
                gc.collect()
            else:
                print('All commands resumed...')
                bind_game_window(dm, hwnd)

    def on_restart_press(event=None):
        nonlocal last_toggle_time
        current_time = time.time()
        if current_time - last_toggle_time < 0.3:
            return
        if event.name and event.name.lower() in ('page up',):
            last_toggle_time = current_time
            print(f'{event.name} pressed: restarting run.bat and closing current terminal...')
            try:
                battle_watcher.stop()
                captcha_watcher.stop()
                dm.UnBindWindow()
            except Exception:
                pass
            try:
                bat_path = os.path.join(_SCRIPT_DIR, 'run.bat')
                os.startfile(bat_path)
            except Exception as e:
                print(f'Error starting run.bat: {e}')
            try:
                os.kill(os.getppid(), 9)
            except Exception as e:
                print(f'Error killing parent terminal: {e}')
            sys.exit(0)

    keyboard.on_press_key('delete', on_pause_press)
    keyboard.on_press_key('page up', on_restart_press)


# ---------------------------------------------------------------------------
# In-Process Fresh Start (Every 20 Battles)
# ---------------------------------------------------------------------------
def perform_fresh_start(dm, hwnd, resource_path: str) -> None:
    """
    Performs a full in-process fresh start every 20 battles:
    - Stops background threads (BattleWatcher, CaptchaWatcher) and unbinds them cleanly.
    - Resets all BotState caches, timers, counters, and food/stamina states.
    - Reloads core modules (combat, combat2, combat3, game_actions) with importlib.
    - Clears minimap region and image caches.
    - Rebinds game window on main DM instance to flush DaMo's internal GDI / capture buffers.
    - Re-instantiates and warms up CombatMemoryCache.
    - Restarts background watchers with fresh COM STA threads.
    - Performs full generational garbage collection (gc.collect).
    - Flushes OS working set memory back to Windows kernel.
    """
    global combat_cache, _last_stamina_eat_time
    global check_revive, check_formation, execute_battle_strategy, initial_call, initiation_battle, execute_skill_loop
    global execute_battle_strategy2, execute_battle_strategy3, STRATEGIES_1, STRATEGIES_2, STRATEGIES_3

    print('\n' + '=' * 68)
    print(f'🔄 [Fresh Start] Reached {BATTLES_PER_FRESH_START} battles! Running fresh start refresh...')
    print('=' * 68)

    # 1. Stop background watchers to cleanly release COM threads & GDI bindings
    print('[Fresh Start] 🛑 Stopping background watcher threads...')
    try:
        battle_watcher.stop()
        captcha_watcher.stop()
        time.sleep(0.2)
    except Exception as e:
        print(f'[Fresh Start] Watcher stop warning: {e}')

    # 2. Reset runtime bot state & mercenary caches
    print('[Fresh Start] 🧹 Resetting runtime state, food, and mercenary caches...')
    state.last_monster_seen_time = time.time()
    state.no_monster_search_count = 0
    state.last_revive_check = 0.0
    state.last_stamina_check = 0.0
    state.last_anti_cheat_check = 0.0
    state.engage_fail_count = 0
    state.invalidate_mercenary_cache()
    _last_stamina_eat_time = 0.0

    # 3. Reload underlying modules (clears function closures and module caches)
    print('[Fresh Start] 📦 Reloading combat, combat2, combat3, and game_actions modules...')
    try:
        import importlib
        importlib.reload(combat_module)
        importlib.reload(combat2_module)
        importlib.reload(combat3_module)
        importlib.reload(game_actions)

        # Re-link fresh function references
        check_revive = combat_module.check_revive
        check_formation = combat_module.check_formation
        execute_battle_strategy = combat_module.execute_battle_strategy
        initial_call = combat_module.initial_call
        initiation_battle = combat_module.initiation_battle
        execute_skill_loop = getattr(combat_module, 'execute_skill_loop', execute_skill_loop)
        execute_battle_strategy2 = combat2_module.execute_battle_strategy2
        execute_battle_strategy3 = combat3_module.execute_battle_strategy3
        STRATEGIES_1 = getattr(combat_module, 'STRATEGIES', STRATEGIES_1)
        STRATEGIES_2 = getattr(combat2_module, 'STRATEGIES', STRATEGIES_2)
        STRATEGIES_3 = getattr(combat3_module, 'STRATEGIES', STRATEGIES_3)

        # Re-wire global is_in_battle into game_actions
        game_actions.is_in_battle = is_in_battle

        if hasattr(combat_module, '_MONSTER_REGION_CACHE'):
            combat_module._MONSTER_REGION_CACHE.clear()
        print('[Fresh Start] ✅ Modules reloaded and symbol tables refreshed.')
    except Exception as e:
        print(f'[Fresh Start] ⚠️ Warning during module reload: {e}')

    # 4. Refresh window binding on main DM instance (clears internal GDI DC / bitmap cache in DaMo)
    print('[Fresh Start] 🔌 Refreshing game window binding...')
    try:
        dm.UnBindWindow()
        time.sleep(0.15)
        dm_ret = bind_game_window(dm, hwnd)
        if dm_ret != 1:
            print(f'[Fresh Start] ⚠️ Window rebind returned: {dm_ret}, retrying...')
            time.sleep(0.2)
            bind_game_window(dm, hwnd)
        else:
            print('[Fresh Start] ✅ Game window re-bound successfully.')
    except Exception as e:
        print(f'[Fresh Start] ⚠️ Window rebind error: {e}')

    # 5. Re-instantiate and warm up CombatMemoryCache
    print('[Fresh Start] ⚡ Re-building and pre-warming CombatMemoryCache...')
    try:
        combat_cache = CombatMemoryCache()
        combat_cache.warmup(dm)
    except Exception as e:
        print(f'[Fresh Start] ⚠️ Combat cache warmup error: {e}')

    # 6. Restart background watchers with fresh COM STA instances
    print('[Fresh Start] 🚀 Restarting background watchers...')
    try:
        captcha_watcher.start(hwnd, resource_path)
        battle_watcher.start(hwnd, resource_path)
    except Exception as e:
        print(f'[Fresh Start] ⚠️ Watcher restart error: {e}')

    # 7. Deep generational garbage collection
    print('[Fresh Start] 🗑️ Performing deep garbage collection...')
    gc.collect(0)
    gc.collect(1)
    gc.collect(2)
    gc.collect()

    # 8. Release unused Windows memory pages back to OS
    try:
        import ctypes
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        ctypes.windll.kernel32.SetProcessWorkingSetSize(handle, -1, -1)
        print('[Fresh Start] 💾 Windows process working set flushed back to OS.')
    except Exception:
        pass

    print('=' * 68)
    print(f'✅ [Fresh Start] Refresh complete! Everything running fresh for next {BATTLES_PER_FRESH_START} battles.')
    print('=' * 68 + '\n')


# ---------------------------------------------------------------------------
# Main Orchestrator Loop
# ---------------------------------------------------------------------------
def run_main_script():
    """Initializes DM, binds game window, and starts the session scheduler."""
    dm = RegDm.reg()
    ret = dm.reg(DM_REG_KEY, DM_REG_CODE)
    print('DM registration result:', ret)
    print('DM version:', dm.ver())

    hwnd = move_game_window(dm)
    state.game_hwnd = hwnd

    dm_ret = bind_game_window(dm, hwnd)
    if dm_ret != 1:
        messagebox.showerror('Error', f'Window binding failed, error code: {dm_ret}')
        sys.exit(1)
    print('Window binding successful, background mode started')

    basedir = getattr(sys, '_MEIPASS', _PROJECT_ROOT) if getattr(sys, 'frozen', None) else _PROJECT_ROOT
    dm.setPath(os.path.join(basedir, 'Resource'))

    # Pre-render / precompute combat routines, templates, and possibilities into memory
    combat_cache.warmup(dm)

    # Background captcha detection (own DM instance, display-only binding)
    captcha_watcher.start(hwnd, os.path.join(basedir, 'Resource'))

    # Background battle detection (own DM instance, display-only binding, 60Hz+ intense check)
    battle_watcher.start(hwnd, os.path.join(basedir, 'Resource'))

    setup_hotkeys(dm, hwnd)

    # Enable automatic GC with standard thresholds to prevent memory accumulation in 32-bit Python
    gc.enable()
    gc.set_threshold(700, 10, 10)
    gc.collect()

    try:
        loop_counter = 0
        battle_counter = 0
        battles_since_refresh = 0

        def do_battle_cycle() -> bool:
            """Executes battle and post-battle maintenance cycle with zero missed battle transitions."""
            nonlocal battle_counter, battles_since_refresh
            print('[Active] Battle screen detected. Handling battle...')
            handle_battle(dm)
            state.invalidate_mercenary_cache()
            gc.collect()

            if check_pending_anti_cheat_relog(dm):
                battle_counter = 0
                battles_since_refresh = 0
                return True

            # If battle ended and we're back in overworld, do maintenance
            if not is_in_battle():
                # Settle wait for overworld screen: interrupt immediately if another battle starts
                if not interruptible_sleep(1.0):
                    check_revive(dm, state.is_paused)
                    state.invalidate_mercenary_cache()
                    if not ensure_mercenaries_recovered(dm, DRAKE_IMAGES):
                        print('[Maintenance] ⚠️ Mercenaries could not be recovered after battle. Holding before next cycle...')
                        interruptible_sleep(1.0)
                        return False

                    if not is_in_battle() and check_food(dm):
                        return False

            battle_counter += 1
            battles_since_refresh += 1
            elapsed_mins = int((time.time() - scheduler.session_start_time) // 60)
            target_dur = getattr(scheduler, '_target_duration', None)
            target_iter = getattr(scheduler, '_target_iterations', '?')
            duration_str = (
                f'{elapsed_mins}m/{int(target_dur // 60)}m'
                if target_dur is not None
                else f'{elapsed_mins}m'
            )
            print(
                f'Battles completed: {scheduler.current_iteration + 1}/{target_iter} '
                f'(Grinding session: {duration_str} | Batch: {battle_counter}/{BATTLES_PER_BATCH_RELOG} | Cycle: {battles_since_refresh}/{BATTLES_PER_FRESH_START})'
            )

            # Fresh start refresh every 20 battles
            if battles_since_refresh >= BATTLES_PER_FRESH_START:
                perform_fresh_start(dm, hwnd, os.path.join(basedir, 'Resource'))
                battles_since_refresh = 0

            print('Standby 2s after battle before continuing to next battle...')
            interruptible_sleep(2.0)
            return True

        def primary_game_step() -> bool:
            """
            Executes one overworld exploration/combat tick.
            Returns True if a battle was fought, False otherwise.
            """
            nonlocal loop_counter, battle_counter

            # CRITICAL: Instant global check - if in battle screen, immediately handle battle!
            if is_in_battle():
                return do_battle_cycle()

            if check_stamina_throttled(dm, interval=1.5):
                scheduler.stop()
                return False

            if is_in_battle():
                return do_battle_cycle()

            if check_anti_cheat_throttled(dm, interval=1.0):
                return False

            if is_in_battle():
                return do_battle_cycle()

            # Pre-battle check: ensure all mercenaries are alive before searching monsters (uses short-lived cache)
            is_dead, target_slots = check_mercenary_dead_cached(dm, max_age=0.4)
            if is_dead:
                print(f'[Pre-Battle] ⚠️ Dead mercenary detected ({target_slots})! Reviving FIRST before battle...')
                if not ensure_mercenaries_recovered(dm, DRAKE_IMAGES):
                    print('[Pre-Battle] ⛔ Dead mercenary still not recovered! Holding before battle...')
                    interruptible_sleep(1.0)
                    return False
                state.invalidate_mercenary_cache()

            if is_in_battle():
                return do_battle_cycle()

            battle_entered = find_and_engage_monster(dm)
            if battle_entered or is_in_battle():
                return do_battle_cycle()

            loop_counter += 1
            if loop_counter % 100 == 0:
                gc.collect(1)  # Periodically clean up during exploration without heavy sweeps

            return False

        def session_cooldown_handler(reason: str, iterations: int, elapsed_sec: float) -> None:
            """Triggered by SessionScheduler when rest threshold (time/iterations) is reached."""
            nonlocal battle_counter, battles_since_refresh
            print(f'[Break Session] 🛑 Rest break triggered ({reason}). Performing fresh start and standing by in place...')
            battle_counter = 0
            battles_since_refresh = 0
            perform_fresh_start(dm, hwnd, os.path.join(basedir, 'Resource'))

        session_cfg = SessionConfig(
            max_iterations=(BATTLES_BEFORE_BREAK_MIN, BATTLES_BEFORE_BREAK_MAX),
            max_duration_seconds=None,
            cooldown_seconds=(BREAK_DURATION_MIN_SECONDS, BREAK_DURATION_MAX_SECONDS),
            loop_interval_seconds=0.01,  # Ultra-fast loop yielding high CPU and maximum polling speed
        )

        scheduler = SessionScheduler(
            task_func=primary_game_step,
            cooldown_func=session_cooldown_handler,
            pause_check=state.is_paused,
            config=session_cfg,
        )

        # Start continuous scheduler loop
        scheduler.run()

    except KeyboardInterrupt:
        print('Program interrupted.')
    finally:
        battle_watcher.stop()
        captcha_watcher.stop()
        keyboard.unhook_all()
        gc.collect()
        print('Cleanup complete, program exited.')


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def create_login_window():
    run_main_script()


if __name__ == '__main__':
    run_main_script()
