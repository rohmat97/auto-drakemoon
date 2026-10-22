# Drake.py — Main entrypoint and orchestrator (Dark Gujimo Elder)

import os
import sys
import time
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
from Battle.Drakemoon.dark_gujimo.combat import (
    check_revive, has_non_black_in_region, check_formation,
    execute_battle_strategy, initial_call, initiation_battle,
)
from Battle.Drakemoon.dark_gujimo.combat2 import execute_battle_strategy2
from Battle.Drakemoon.dark_gujimo.combat3 import execute_battle_strategy3
from game_actions import (
    relogin,
    check_food as base_check_food,
    check_anti_cheat,
    check_pending_anti_cheat_relog,
    check_stamina as base_check_stamina,
    is_in_battle,
    stop_battle,
    is_mercenary_dead,
    ensure_mercenaries_recovered,
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
MONSTER_IMAGES = '|'.join(
    [rf'dark_gujimo\elder{i}.bmp' for i in range(1, 12)] +
    [rf'dark_gujimo\goju{i}.bmp' for i in range(1, 12)]
)
DRAKE_IMAGES = '|'.join([rf'Character\drakemoon\drake{i}.bmp' for i in range(1, 12)])

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
BREAK_DURATION_MIN_SECONDS = 1 * 60   # 1 minute (60s)
BREAK_DURATION_MAX_SECONDS = 3 * 60  # 3 minutes (180s)


# ---------------------------------------------------------------------------
# State Management
# ---------------------------------------------------------------------------
class BotState:
    """Encapsulates runtime state for the automation bot."""

    def __init__(self):
        self.paused = False
        self.last_monster_seen_time = time.time()
        self.no_monster_search_count = 0
        self.last_revive_check = 0.0
        # Performance & throttling caches
        self.last_stamina_check = 0.0
        self.last_anti_cheat_check = 0.0
        self.engage_fail_count = 0

    def is_paused(self) -> bool:
        return self.paused

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def toggle_pause(self) -> bool:
        self.paused = not self.paused
        return self.paused


state = BotState()


# ---------------------------------------------------------------------------
# Helper Routines
# ---------------------------------------------------------------------------
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
            success = eat_stamina(dm, times=9)
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


def check_mercenary_dead_cached(dm, max_age: float = 0.6) -> tuple:
    """Checks mercenary status directly from the screen (no caching; max_age is ignored)."""
    return is_mercenary_dead(dm, DRAKE_IMAGES)


def check_anti_cheat_throttled(dm, interval: float = 1.0, **kwargs) -> bool:
    """
    Throttles anti-cheat checking during overworld roaming or wait loops.
    Avoids running multiple fullscreen FindPic scans on every 150ms tick
    while maintaining sub-second detection latency.
    """
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


# ---------------------------------------------------------------------------
# Overworld: find and engage a monster
# ---------------------------------------------------------------------------
def find_and_engage_monster(dm) -> bool:
    """
    Search for a monster on the overworld and attempt to enter battle.
    Returns True if battle was entered, False otherwise.
    """
    current_time = time.time()

    # Periodic check for main character revive prompt every 5 seconds
    if current_time - state.last_revive_check > 5.0:
        state.last_revive_check = current_time
        if check_revive(dm, state.is_paused):
            print('[Overworld] Main character revival sequence completed. Ready for exploration.')
            return False

    # Check if any mercenary is dead before searching monsters (uses short-lived cache)
    is_dead, dead_slots = check_mercenary_dead_cached(dm, max_age=0.6)
    if is_dead:
        print(f'[Overworld] ⚠️ Dead mercenary detected ({dead_slots})! Halting monster search to revive first...')
        if not ensure_mercenaries_recovered(dm, DRAKE_IMAGES):
            print('[Overworld] ⛔ Dead mercenary could not be recovered yet! Standing by...')
        return False

    # Search concentric zones from center outward
    x, y = 0, 0
    for zx1, zy1, zx2, zy2 in MONSTER_SEARCH_ZONES:
        (_, x, y) = dm.FindPic(zx1, zy1, zx2, zy2, MONSTER_IMAGES, '050505', 0.8, 0)
        if x > 0:
            break

    if x <= 0:
        if current_time - state.last_monster_seen_time > 5:
            state.no_monster_search_count += 1
            print(f'[Active] Searching for monsters on overworld... ({state.no_monster_search_count}/10)')
            state.last_monster_seen_time = current_time
            if state.no_monster_search_count >= 10:
                print('No monsters found 10 times, pressing ESC to dismiss any popups...')
                dm.KeyPress(KEY_ESC)
                dm.Delay(300)
                state.no_monster_search_count = 0
        time.sleep(0.04)  # Small yield to prevent 100% CPU core spinning while roaming
        return False

    state.no_monster_search_count = 0
    state.last_monster_seen_time = time.time()
    print(f'Monster found at coords: ({x}, {y})')

    # Ensure all mercenaries are alive before moving/clicking (uses short-lived cache)
    is_dead, dead_slots = check_mercenary_dead_cached(dm, max_age=0.6)
    if is_dead:
        print(f'[Overworld] ⚠️ Monster found, but dead mercenary detected ({dead_slots})! Aborting chase to revive first...')
        ensure_mercenaries_recovered(dm, DRAKE_IMAGES)
        return False

    # Engage monster
    dm.MoveTo(x, y)
    dm.Delay(150)
    dm.RightClick()
    dm.Delay(300)

    print('Waiting to enter battle screen... (max 3s)')
    start_time = time.time()
    attempt = 1

    while time.time() - start_time < 5:
        if is_in_battle(dm):
            print('✅ Successfully entered battle screen')
            state.engage_fail_count = 0
            return True

        if check_anti_cheat_throttled(dm, interval=1.0, immediate_wait=False):
            return False

        if time.time() - start_time > 1.5 and attempt == 1:
            print('Battle not entered, right-clicking monster again...')
            dm.MoveTo(x, y)
            dm.Delay(100)
            dm.RightClick()
            dm.Delay(300)
            attempt = 2

        time.sleep(0.1)

    # Final check, then recovery if still not in battle
    if is_in_battle(dm):
        print('✅ Successfully entered battle screen')
        state.engage_fail_count = 0
        return True

    state.engage_fail_count += 1
    print(f'[Overworld] Battle not entered ({state.engage_fail_count}/3).')
    if state.engage_fail_count >= 3:
        print('[Overworld] ⚠️ Stuck engaging monster. Dismissing popups and moving cursor away to recover...')
        dm.KeyPress(KEY_ESC)
        dm.Delay(300)
        dm.MoveTo(512, 384)
        time.sleep(1.0)
        state.engage_fail_count = 0
    time.sleep(0.1)
    return False



# ---------------------------------------------------------------------------
# Battle phase routines: find formation, find monsters, and execute battle
# ---------------------------------------------------------------------------
def find_formation(dm) -> str | None:
    """
    Step 1: Check formation first.
    Moves cursor to center to avoid obstructing checks and verifies formation regions.
    Returns the detected direction ('East', 'South', 'West', 'North') or None.
    """
    dm.MoveTo(640, 425)
    for direction, regions in FORMATION_REGIONS.items():
        if check_formation(dm, regions[0], regions[1]):
            return direction
    return None


def find_monsters(dm, direction: str) -> list[str]:
    """
    Step 2: Scan minimap regions for monsters corresponding to the detected formation.
    Rule: A monster can NEVER be on the same side as our own formation.
    Returns a list of monster direction names found.
    """
    print(f'Scanning {direction} formation for monsters...')
    found_monsters = []
    for monster_dir in MONSTER_CHECKS.get(direction, []):
        # Rule: A monster can NEVER be on the same side as our own formation
        if monster_dir == direction:
            continue
        (x1, y1, x2, y2) = MONSTER_DIRECTION_REGIONS[monster_dir]
        if has_non_black_in_region(dm, x1, y1, x2, y2, monster_dir):
            found_monsters.append(monster_dir)
    return found_monsters


def execute_battle(dm, direction: str, found_monsters: list[str]) -> bool:
    """
    Step 3: Execute initial battle commands and combat strategies for all detected monsters.
    Sends directional key, calls initial and initiation sequences, selects primary unit,
    and executes appropriate battle strategies sequentially.
    Returns True if strategies were executed.
    """
    if not found_monsters:
        return False

    duration = 15 if found_monsters else 10
    key_code = DIRECTION_KEYS.get(direction)
    if key_code is not None:
        dm.KeyDown(key_code)
        dm.Delay(400)
        dm.KeyUp(key_code)

    initial_call(dm)
    initiation_battle(dm)
    select_unit_1(dm, delay_ms=25)

    # Execute battle strategy for each found monster
    print(f'Total monsters found: {len(found_monsters)} -> {found_monsters}')
    for i, monster_dir in enumerate(found_monsters):
        if not is_in_battle(dm):
            print(f'[Battle] Battle finished before executing strategy [{i+1}/{len(found_monsters)}] ({monster_dir}). Stopping.')
            break
        print(f'Executing strategy [{i+1}/{len(found_monsters)}] → Formation: {direction} | Monster: {monster_dir}')
        if i == 0:
            execute_battle_strategy(dm, direction, monster_dir)
        elif i == 1:
            execute_battle_strategy2(dm, direction, monster_dir)
        elif i == 2:
            execute_battle_strategy3(dm, direction, monster_dir)
        else:
            execute_battle_strategy(dm, direction, monster_dir)

        if i < len(found_monsters) - 1:
            wait_time = 2 if i in (0, 1) else duration
            wait_time = max(0, wait_time)
            if wait_time > 0:
                print(f'Waiting {wait_time}s before next strategy...')
                time.sleep(wait_time)
            select_unit_1(dm, delay_ms=100)
        else:
            time.sleep(duration)

    return True


def handle_battle(dm) -> None:
    """Process a single battle until it ends."""
    print('Entered battle screen')
    action_executed = False
    empty_scan_rounds = 0
    max_empty_scan_rounds = 10

    # Brief delay for battle screen and minimap to settle
    time.sleep(0.3)

    while True:
        if state.is_paused():
            time.sleep(1)
            continue

        if action_executed:
            print('Waiting for battle screen to close...')
            stop_battle(dm, max_wait_sec=15)
            print('Battle screen ended')
            break

        # Check if battle ended
        if not is_in_battle(dm):
            print('Battle screen ended')
            break

        # Step 1: Detect formation
        direction = find_formation(dm)
        if direction:
            # Step 2: Detect monsters for this formation
            found_monsters = find_monsters(dm, direction)

            # Step 3: Execute battle strategy if monsters were confirmed
            if found_monsters:
                action_executed = execute_battle(dm, direction, found_monsters)
                continue

        if not action_executed:
            empty_scan_rounds += 1
            if empty_scan_rounds >= max_empty_scan_rounds:
                print(f'No monsters or formation confirmed after {empty_scan_rounds} scan rounds. Leaving battle...')
                stop_battle(dm, max_wait_sec=15)
                break
            time.sleep(0.3)


# ---------------------------------------------------------------------------
# Hotkeys Setup
# ---------------------------------------------------------------------------
def setup_hotkeys(dm, hwnd) -> None:
    """Registers global hotkeys for pause/resume (F10 / Delete) and restart (Page Down / Page Up)."""
    last_toggle_time = 0.0

    def on_pause_press(event=None):
        nonlocal last_toggle_time
        current_time = time.time()
        if current_time - last_toggle_time < 0.3:
            return
        if event.name in ('f10'):
            last_toggle_time = current_time
            is_now_paused = state.toggle_pause()
            if is_now_paused:
                print('All commands paused, press F10 or Delete to resume...')
                dm.UnBindWindow()
            else:
                print('All commands resumed...')
                bind_game_window(dm, hwnd)

    def on_restart_press(event=None):
        nonlocal last_toggle_time
        current_time = time.time()
        if current_time - last_toggle_time < 0.3:
            return
        if event.name in ('page down'):
            last_toggle_time = current_time
            print(f'{event.name} pressed: restarting run.bat and closing current terminal...')
            try:
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

    keyboard.on_press_key('f10', on_pause_press)
    keyboard.on_press_key('page down', on_restart_press)


# ---------------------------------------------------------------------------
# Main Orchestrator Loop
# ---------------------------------------------------------------------------
def run_main_script():
    """Initializes DM, binds game window, and runs the main bot loop."""
    dm = RegDm.reg()
    ret = dm.reg(DM_REG_KEY, DM_REG_CODE)
    print('DM registration result:', ret)
    print('DM version:', dm.ver())

    hwnd = move_game_window(dm)
    dm_ret = bind_game_window(dm, hwnd)
    if dm_ret != 1:
        messagebox.showerror('Error', f'Window binding failed, error code: {dm_ret}')
        sys.exit(1)
    print('Window binding successful, background mode started')

    basedir = getattr(sys, '_MEIPASS', _PROJECT_ROOT) if getattr(sys, 'frozen', None) else _PROJECT_ROOT
    dm.setPath(os.path.join(basedir, 'Resource'))

    setup_hotkeys(dm, hwnd)

    try:
        battle_counter = 0
        session_start_time = time.time()

        def primary_game_step() -> bool:
            """
            Executes one overworld exploration/combat tick.
            Returns True if a battle was fought, False otherwise.
            Raises StopIteration if the bot should stop (food depleted).
            """
            nonlocal battle_counter

            if check_stamina_throttled(dm, interval=1.5):
                raise StopIteration

            if check_anti_cheat_throttled(dm, interval=1.0):
                return False

            # Pre-battle check: ensure all mercenaries are alive before searching monsters
            is_dead, target_slots = check_mercenary_dead_cached(dm, max_age=0.6)
            if is_dead:
                print(f'[Pre-Battle] ⚠️ Dead mercenary detected ({target_slots})! Reviving FIRST before battle...')
                if not ensure_mercenaries_recovered(dm, DRAKE_IMAGES):
                    print('[Pre-Battle] ⛔ Dead mercenary still not recovered! Holding before battle...')
                    time.sleep(2)
                    return False

            battle_entered = find_and_engage_monster(dm)
            if battle_entered or is_in_battle(dm):
                handle_battle(dm)

                # Check if anti-cheat flagged a relog after finishing battle
                if check_pending_anti_cheat_relog(dm):
                    battle_counter = 0
                    return True

                # Post-battle maintenance: only check when battle has ended and on overworld
                if not is_in_battle(dm):
                    # Wait for overworld screen and mercenary sidebar to settle
                    time.sleep(1.5)

                    # Post-battle maintenance: revives and food
                    check_revive(dm, state.is_paused)
                    if not ensure_mercenaries_recovered(dm, DRAKE_IMAGES):
                        print('[Maintenance] ⚠️ Mercenaries could not be recovered after battle. Holding before next cycle...')
                        time.sleep(2)
                        return False

                    if check_food(dm):
                        return False

                battle_counter += 1
                elapsed_mins = int((time.time() - session_start_time) // 60)
                print(f'Battles completed: {battle_counter} (Session: {elapsed_mins}m)')

                print('Waiting 2s after battle before continuing to next battle...')
                time.sleep(2)

                return True

            return False

        # Plain continuous loop (no scheduler)
        while True:
            if state.is_paused():
                time.sleep(0.5)
                continue
            try:
                primary_game_step()
            except StopIteration:
                break
            time.sleep(0.15)

    except KeyboardInterrupt:
        print('Program interrupted.')
    finally:
        keyboard.unhook_all()
        print('Cleanup complete, program exited.')


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def create_login_window():
    run_main_script()


if __name__ == '__main__':
    run_main_script()
