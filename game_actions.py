# game_actions.py — Centralized shared game actions for Drake bots
# Includes: Anti-cheat, Captcha solving, Stamina, Inventory/Item routines,
#           Food & Mercenary revival, Town break & Portal travel routines.

import os
import sys
import time
import random
import winsound
from tkinter import messagebox

import cv2
import numpy as np

from captcha_solver import solve_captcha

# ---------------------------------------------------------------------------
# Default Assets
# ---------------------------------------------------------------------------
DEFAULT_DRAKE_IMAGES = (
    '|'.join([rf'Character\drakemoon\drake{i}.bmp' for i in range(1, 12)]) + '|' +
    '|'.join([rf'drake\drake{i}.bmp' for i in range(1, 19)])
)


# ---------------------------------------------------------------------------
# Sound & Alerts
# ---------------------------------------------------------------------------
def play_alert_sound(dm, sound_name='whatsapp.wav'):
    """Play an alert sound when anti-cheat or critical events occur."""
    try:
        sound_path = os.path.join(dm.getPath(), sound_name)
        if not os.path.exists(sound_path):
            for alt in ['whatsapp.wav', 'alert.wav']:
                alt_path = os.path.join(dm.getPath(), alt)
                if os.path.exists(alt_path):
                    sound_path = alt_path
                    break
        if os.path.exists(sound_path):
            winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Battle State Checks
# ---------------------------------------------------------------------------
def is_in_battle(dm):
    """Returns True if the game is currently on the battle screen."""
    (_, x, _) = dm.FindPic(959, 666, 1016, 747, 'battle3.bmp|battle.bmp|battle2.bmp', '050505', 0.8, 0)
    return x > 0


def stop_battle(dm, max_wait_sec=15):
    """
    Stops/exits the battle screen immediately by pressing Esc until back in overworld.
    Returns True if battle exited successfully, False if still in battle.
    """
    if not is_in_battle(dm):
        return True

    print('[Battle] 🛑 Stopping battle (retreating via Esc)...')
    start_time = time.time()
    while is_in_battle(dm) and (time.time() - start_time < max_wait_sec):
        for _ in range(2):
            dm.KeyPress(27)  # Esc
            dm.Delay(50)
        time.sleep(1.0)

    exited = not is_in_battle(dm)
    if exited:
        print('[Battle] ✅ Successfully exited battle.')
    else:
        print('[Battle] ⚠️ Failed to exit battle screen within timeout.')
    return exited


def check_community_popup(dm):
    """Check for the Community popup and press ESC once to dismiss it.
    Returns True if the popup was detected and dismissed."""
    (_, x, _) = dm.FindPic(0, 0, 1024, 768, 'community.bmp', '050505', 0.8, 0)
    if x > 0:
        print('[Popup] Community popup detected, pressing ESC to dismiss...')
        dm.KeyPress(27)  # Press ESC
        dm.Delay(300)
        return True
    return False


# ---------------------------------------------------------------------------
# Anti-Cheat & Stamina
# ---------------------------------------------------------------------------
def handle_captcha(dm, x_captcha, y_captcha):
    """
    Handles captcha dialog:
    1. Moves cursor away so it doesn't block the characters.
    2. Waits 2 seconds.
    3. Captures the captcha region to temp_captcha.bmp (auto-cropped by solve_captcha).
    4. Solves the captcha code via solve_captcha().
    5. Types the code directly (input is auto-focused) and presses Enter.
    6. Moves cursor to confirm button (405, 440) and left clicks.
    """
    print(f'[Captcha Handler] 2nd Captcha dialog located at ({x_captcha}, {y_captcha}).')
    # 1. Move cursor away from dialog
    dm.MoveTo(0, 0)

    # 2. Wait for 2 seconds
    print('[Captcha Handler] Waiting 2 seconds before solving...')
    time.sleep(2.0)

    # 3. Capture captcha rectangle relative to detect_captcha match
    # Captures an encompassing region around the dialog; solve_captcha() auto-crops to the inner box
    x1 = max(0, x_captcha - 30)
    y1 = max(0, y_captcha - 90)
    x2 = min(1024, x_captcha + 300)
    y2 = min(768, y_captcha + 160)

    captcha_save_path = os.path.join(dm.getPath(), 'temp_captcha.bmp')
    dm.Capture(x1, y1, x2, y2, captcha_save_path)
    dm.Delay(100)

    # 4. Recognize captcha text
    code = solve_captcha(captcha_save_path, debug=True)
    print(f'[Captcha Handler] Solved code: "{code}"')

    # 5. Type characters into form (input is auto-focused)
    if code:
        for char in code:
            dm.KeyPressChar(char)
            dm.Delay(80)
        dm.Delay(200)
        dm.KeyPress(13)  # Enter key
    else:
        print('[Captcha Handler] Warning: No code recognized.')

    dm.Delay(200)

    # 6. Move cursor to button position (405, 440) and left click
    dm.MoveTo(405, 440)
    dm.Delay(150)
    dm.LeftClick()
    dm.Delay(1000)

    print('[Captcha Handler] Moved to (405, 440) and left-clicked button successfully.')
    return True


# ---------------------------------------------------------------------------
# Anti-Cheat State & Routines
# ---------------------------------------------------------------------------
_anti_cheat_pending_relog = False
_last_anti_cheat_sound_time = 0
_anti_cheat_relogin_func = None


def is_anti_cheat_pending_relog():
    """Returns True if a post-battle relog is currently pending."""
    return _anti_cheat_pending_relog


def set_anti_cheat_pending_relog(pending=True, relogin_func=None):
    """Sets or clears the pending post-battle anti-cheat relog flag."""
    global _anti_cheat_pending_relog, _anti_cheat_relogin_func
    _anti_cheat_pending_relog = pending
    if relogin_func:
        _anti_cheat_relogin_func = relogin_func


def check_pending_anti_cheat_relog(dm, relogin_func=None):
    """
    Checks if a post-battle relog was flagged by anti-cheat (missing horse stamp).
    If flagged, executes relogin after the battle finishes and resets the flag.
    Returns True if relog was performed, False otherwise.
    """
    global _anti_cheat_pending_relog, _last_anti_cheat_sound_time, _anti_cheat_relogin_func
    if _anti_cheat_pending_relog:
        print('[Anti-Cheat] 🎯 Battle finished! 1 monster killed under anti-cheat condition.')
        print('[Anti-Cheat] 🔄 Triggering scheduled post-battle relogin now...')
        _anti_cheat_pending_relog = False
        _last_anti_cheat_sound_time = 0
        fn_relogin = relogin_func or _anti_cheat_relogin_func or relogin
        time.sleep(1)
        fn_relogin(dm)
        return True
    return False


def check_anti_cheat(dm, relogin_func=None):
    """Returns True if anti-cheat (horse-stamp missing or 2nd captcha dialog popup) is detected."""
    global _anti_cheat_pending_relog, _last_anti_cheat_sound_time, _anti_cheat_relogin_func
    if relogin_func:
        _anti_cheat_relogin_func = relogin_func

    # 1. Check horse stamp vs bread indicator
    (_, x_horse, _) = dm.FindPic(599, 21, 650, 49, r'anti_cheat\horse.bmp', '050505', 0.8, 0)
    (_, x_bread, _) = dm.FindPic(50, 650, 93, 689, r'anti_cheat\bread.bmp', '050505', 0.8, 0)
    if x_horse <= 0 and x_bread > 0:
        now = time.time()
        if not _anti_cheat_pending_relog:
            _anti_cheat_pending_relog = True
            _last_anti_cheat_sound_time = now
            print('[Anti-Cheat] 🚨 Horse stamp missing while bread icon is visible!')
            print('[Anti-Cheat] 🔔 Playing alert sound. Account will kill 1 monster first, then relog after battle.')
            play_alert_sound(dm)
        elif now - _last_anti_cheat_sound_time > 15.0:
            _last_anti_cheat_sound_time = now
            print('[Anti-Cheat] 🚨 Alert sound active (missing horse stamp). Waiting to finish 1 monster battle before relog...')
            play_alert_sound(dm)
        return True

    # 2. Check 2nd captcha popup box
    (_, x_captcha, y_captcha) = dm.FindPic(0, 0, 1024, 768, r'anti_cheat\detect_captcha.bmp', '050505', 0.8, 0)
    if x_captcha > 0:
        print(f'[Anti-Cheat] 🚨 2nd Captcha dialog detected at ({x_captcha}, {y_captcha})!')
        print('[Anti-Cheat] Playing alert sound and solving 2nd captcha automatically...')
        play_alert_sound(dm)
        handle_captcha(dm, x_captcha, y_captcha)
        return True

    return False


def check_stamina(dm, pause_callback=None):
    """Check for the no stamina indicator. Pauses, unbinds, and shows popup if detected."""
    (_, x_no_stamina, _) = dm.FindPic(90, 695, 99, 703, 'nostamina.bmp', '050505', 1, 0)
    if x_no_stamina >= 0:
        print('[Stamina] No stamina detected, pausing...')
        if pause_callback:
            pause_callback()
        dm.UnBindWindow()
        messagebox.showinfo('No Stamina', 'No stamina detected, pausing...')
        return True
    return False


# ---------------------------------------------------------------------------
# Character Maintenance: Food & Mercenary Revival
# ---------------------------------------------------------------------------
def check_food(dm, relogin_func=None, pause_callback=None):
    """Check hunger level and consume food if needed.
    Returns True if script should pause (food exhausted)."""
    # Check if a post-battle relog was scheduled by missing horse stamp alert
    if check_pending_anti_cheat_relog(dm, relogin_func=relogin_func):
        return False

    if not hasattr(check_food, "eat_count"):
        check_food.eat_count = 0

    check_food.eat_count += 1

    if check_food.eat_count % 5 == 0:
        inv_open = False
        for _ in range(5):
            (_, bx, by) = dm.FindPic(0, 0, 1024, 768, 'break_inventory_bag.bmp|bag.bmp', '101010', 0.75, 0)
            if bx > 0:
                inv_open = True
                break
            dm.KeyPress(73)  # 'i' key
            dm.Delay(500)

        if inv_open:
            print('[Food] Inventory is open. Searching for food item...')
            (_, fx, fy) = dm.FindPic(0, 0, 1024, 768, 'drake_food.bmp|food.bmp', '101010', 0.75, 0)
            if fx > 0:
                print(f'[Food] Food detected at ({fx}, {fy}). Right-clicking 5 times to consume...')
                dm.MoveTo(fx + 5, fy + 5)
                dm.Delay(150)
                for _ in range(5):
                    dm.RightClick()
                    dm.Delay(200)
                # Close inventory
                dm.KeyPress(73)  # 'i' key
                dm.Delay(400)
                return False
            else:
                print('[Food] ⚠️ Food item (drake_food.bmp) not detected in inventory, pausing script...')
                # Close inventory
                dm.KeyPress(73)  # 'i' key
                dm.Delay(400)
                check_food.eat_count = 0
                if pause_callback:
                    pause_callback()
                print('All commands paused, press delete or page down to resume...')
                dm.UnBindWindow()
                return True

    (_, x_bread, _) = dm.FindPic(43, 644, 101, 692, 'bread.bmp', '050505', 0.8, 0)
    if x_bread > 0:
        print(f'Replenished satiety 500 times, pausing script... {check_food.eat_count}/500')
        if check_food.eat_count >= 500:
            fn_relogin = relogin_func or relogin
            fn_relogin(dm)
            check_food.eat_count = 0
            if pause_callback:
                pause_callback()
            print('All commands paused, press delete or page down to resume...')
            dm.UnBindWindow()
            return True

    (_, x_empty, _) = dm.FindPic(450, 350, 680, 480, 'emptyfoodinter.bmp|emptyfooddrake.bmp', '050505', 0.8, 0)
    if x_empty > 0:
        print('Satiety depleted, script paused')
        check_food.eat_count = 0
        if pause_callback:
            pause_callback()
        print('All commands paused, press delete or page down to resume...')
        dm.UnBindWindow()
        return True
    return False


# Coordinates for mercenary sidebar: (0, 5, 55, 505), width=55, height=500
MERCENARY_SIDEBAR_REGION = (0, 5, 55, 505)
# Mercenary slots (slots 2 to 12; slot 1 is Main Character and handled separately)
MERCENARY_SLOT_KEYS = {
    # Slot 1 is Main Character (excluded from mercenary checks)
    2: 50,   # Key '2'
    3: 51,   # Key '3'
    4: 52,   # Key '4'
    5: 53,   # Key '5'
    6: 54,   # Key '6'
    7: 55,   # Key '7'
    8: 56,   # Key '8'
    9: 57,   # Key '9'
    10: 48,  # Key '0'
    11: 189, # Key '-'
    12: 187, # Key '='
}

REVIVE_BUTTON_IMAGES = 'revivedrake.bmp|revive.bmp'


def detect_dead_mercenary_slots(dm, x1=0, y1=5, x2=55, y2=505, include_main_character=False):
    """
    Captures the mercenary sidebar region (0, 5, 55, 505)
    and checks mercenary portrait slots (slots 2 to 12 by default).
    
    In Gersang:
    - Slot 1 is the Main Character (excluded by default; handles death via revive popup).
    - Slots 2 to 12 are Mercenaries.
    - As long as a mercenary is alive (has HP > 0), their red HP bar is present.
    - Even if HP is not full, as long as they are alive and not dead/grayed out, continue battle.
    - A DEAD mercenary has HP = 0, so their RED HP BAR IS COMPLETELY GONE (red_pixels < 10).
    
    Returns:
        dead_slots: list of dead slot numbers (1-indexed: 2 to 12 by default).
    """
    # The mercenary sidebar is hidden during battle; only check on overworld
    if is_in_battle(dm):
        return []

    temp_path = os.path.join(dm.getPath(), 'temp_merc_sidebar.bmp')
    dm.Capture(x1, y1, x2, y2, temp_path)
    if not os.path.exists(temp_path):
        return []

    try:
        img = cv2.imread(temp_path)
        if img is None:
            return []

        h, w = img.shape[:2]
        if h < 50 or w < 10:
            return []

        slot_h = h / 12.0
        dead_slots = []

        # Do not include main character (slot 0) by default; only check mercenary slots (1 to 11 -> slots 2 to 12)
        start_index = 0 if include_main_character else 1
        for i in range(start_index, 12):
            y_start = int(round(i * slot_h))
            y_end = int(round((i + 1) * slot_h))
            slot = img[y_start:y_end, :]
            if slot.size == 0:
                continue

            # Skip empty / unassigned mercenary slot (uniform background with very low variance)
            std_val = float(np.std(slot))
            mean_val = float(np.mean(slot))
            if std_val < 15.0 or mean_val < 15.0:
                continue

            b = slot[:, :, 0].astype(int)
            g = slot[:, :, 1].astype(int)
            r = slot[:, :, 2].astype(int)

            # Red HP bar in Gersang: high red, low green and blue
            red_mask = (r > 130) & (g < 65) & (b < 65)
            red_pixels = int(np.sum(red_mask))

            # If red HP bar is completely missing (HP = 0), mercenary is dead!
            # If HP is not full (has red pixels >= 10), they are still alive -> continue battle
            if red_pixels < 10:
                dead_slots.append(i + 1)

        return dead_slots
    except Exception as e:
        print(f'[Revival] Error checking mercenary sidebar: {e}')
        return []


def is_mercenary_dead(dm, drake_images=None):
    """
    Checks if any mercenary is dead (HP = 0, no red HP bar).
    Returns (is_dead: bool, dead_slots: list[int]).
    """
    x1, y1, x2, y2 = MERCENARY_SIDEBAR_REGION
    dead_slots = detect_dead_mercenary_slots(dm, x1, y1, x2, y2)
    if dead_slots:
        return True, dead_slots

    return False, []


_last_alt_1_time = 0


def press_alt_1(dm, min_interval=3.0):
    """
    Press Alt+1 to consume quick-slot revival item (half-chicken soup).
    Strictly rate-limited to avoid wasting revival items.
    """
    global _last_alt_1_time
    now = time.time()
    if now - _last_alt_1_time < min_interval:
        print(f'[Revival] ⏳ Alt+1 cooldown active ({now - _last_alt_1_time:.1f}s < {min_interval}s). Skipping to prevent item waste.')
        return False

    print('[Revival] 🍗 Pressing Alt+1 (1 time only) to consume revival item...')
    dm.KeyDown(18)   # Alt
    dm.Delay(200)
    dm.KeyPress(49)  # '1'
    dm.Delay(200)
    dm.KeyUp(18)     # Alt
    dm.Delay(500)
    _last_alt_1_time = time.time()
    return True

def check_main_character_revive(dm, is_paused_func=None, revive_images=REVIVE_BUTTON_IMAGES):
    """
    Checks if main character died and the revive/review confirmation button ('OK') is shown.
    If found:
    - Confirms prompt: presses Enter or clicks button OK.
    - Transports to clinic: waits 5s for town to load.
    - Exits town: presses Esc 2 times.
    (Does NOT press Alt+1 - Alt+1 is preserved exclusively for dead mercenaries).
    
    Returns True if revival was executed, False otherwise.
    """
    if is_paused_func and is_paused_func():
        return False

    (r, x, y) = dm.FindPic(0, 0, 1024, 768, revive_images, '202020', 0.8, 0)
    if x > 0:
        print(f'[Revival] ⚠️ Main character revive button OK found at ({x}, {y})!')
        # Press button OK
        dm.MoveTo(x, y)
        dm.Delay(100)
        dm.LeftClick()
        dm.Delay(300)
        return True

    return False


# Alias for backward compatibility
check_revive = check_main_character_revive


def _perform_mercenary_revival(dm, dead_slots=None):
    """Presses Alt+1 once to revive dead mercenaries."""
    press_alt_1(dm)


def check_dead_mercenary(dm, drake_images=None, max_attempts=1):
    """
    Checks if any mercenary is dead. If detected:
    Presses Alt+1 exactly 1 time to revive without wasting items.
    """
    # Check if main character died and revive prompt is open
    if check_main_character_revive(dm):
        return True

    is_dead, dead_slots = is_mercenary_dead(dm, drake_images)
    if not is_dead:
        return False

    print(f'[Revival] ⚠️ Dead mercenary detected (slots: {dead_slots})! Pressing Alt+1 (1 time only)...')
    press_alt_1(dm)
    dm.Delay(800)
    return True


def ensure_mercenaries_recovered(dm, drake_images=None, max_attempts=1):
    """
    Ensures dead mercenaries are revived.
    Presses Alt+1 only 1 time when dead mercenaries are detected to prevent item waste.
    """
    # First ensure main character isn't waiting on revive prompt
    if check_main_character_revive(dm):
        return True

    is_dead, dead_slots = is_mercenary_dead(dm, drake_images)
    if not is_dead:
        return True

    print(f'[Revival] ⚠️ Dead mercenary detected (slots: {dead_slots}). Consuming 1 revival item (Alt+1)...')
    press_alt_1(dm)
    dm.Delay(800)
    return True


# ---------------------------------------------------------------------------
# Relogin & Inventory Organization
# ---------------------------------------------------------------------------
def relogin(dm):
    """Press Esc to open System Menu, then click 'Char Select' and wait with humanized movement."""
    print('Relogin: Opening System Menu...')
    dm.KeyPress(27)  # Esc to open System Menu
    dm.Delay(500)
    dm.MoveTo(509, 290)
    dm.Delay(500)
    dm.LeftClick()
    dm.Delay(500)
    dm.KeyPress(13)

    # Move cursor from corner to corner every 5 to 10 seconds for 90 seconds
    corners = [(10, 10), (1014, 10), (1014, 758), (10, 758)]
    start_time = time.time()
    corner_idx = 0
    while time.time() - start_time < 90:
        cx, cy = corners[corner_idx % len(corners)]
        dm.MoveTo(cx, cy)
        corner_idx += 1
        sleep_sec = random.randint(1, 10)
        if sleep_sec > 0:
            time.sleep(sleep_sec)

    dm.KeyPress(13)
    dm.Delay(5000)
    # Press 'A' to enter game
    dm.KeyPress(65)
    dm.Delay(500)


def organize_items(dm):
    """Opens inventory and browses mercenary tabs, simulating item organization and management."""
    print('[Inventory] 🎒 Opening inventory to organize items...')
    dm.KeyPress(73)  # 'i' key
    dm.Delay(600)

    merc_keys = [49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 189, 187]
    random.shuffle(merc_keys)
    for key in merc_keys:
        dm.KeyPress(key)
        dm.Delay(random.randint(200, 400))

        # Simulate inspecting/organizing inventory grid slots
        for _ in range(random.randint(2, 4)):
            rx = random.randint(560, 760)
            ry = random.randint(140, 360)
            dm.MoveTo(rx, ry)
            dm.Delay(150)
            dm.LeftClick()
            dm.Delay(200)
            dm.MoveTo(rx + 20, ry + 20)
            dm.Delay(random.randint(100, 250))
            dm.LeftClick()
            dm.Delay(150)

    print('[Inventory] Closing inventory...')
    dm.KeyPress(73)  # 'i' key
    dm.Delay(500)


def reorganize_and_consume_item(dm, is_paused_func=None):
    """Opens inventory, reorganizes mercenary tabs, and consumes break_inventory_item.bmp."""
    print('[Inventory] 🎒 Opening inventory to reorganize items and consume item...')
    dm.KeyPress(73)  # 'i' key
    dm.Delay(600)

    merc_keys = [49]
    random.shuffle(merc_keys)
    for key in merc_keys:
        dm.KeyPress(key)
        dm.Delay(random.randint(200, 400))

        for _ in range(random.randint(1, 5)):
            rx = random.randint(560, 760)
            ry = random.randint(140, 360)
            dm.MoveTo(rx, ry)
            dm.Delay(250)
            dm.LeftClick()
            dm.Delay(250)
            dm.MoveTo(rx + 20, ry + 20)
            dm.Delay(random.randint(250, 2000))
            dm.LeftClick()
            dm.Delay(250)

    # Select main character tab ('1')
    dm.KeyPress(49)
    dm.Delay(400)

    # Find and consume item
    print('[Inventory] Looking for item image (break_inventory_item.bmp)...')
    item_used = False
    for _ in range(15):
        (_, ix, iy) = dm.FindPic(0, 0, 1024, 768, 'break_inventory_item.bmp', '101010', 0.75, 0)
        if ix > 0:
            print(f'[Inventory] Item detected at ({ix}, {iy}). Moving cursor and right-clicking 1 time to consume...')
            dm.MoveTo(ix + 2, iy + 2)
            dm.Delay(200)
            dm.RightClick()
            dm.Delay(500)
            item_used = True
            break
        time.sleep(0.3)

    if not item_used:
        print('[Inventory] ⚠️ Item (break_inventory_item.bmp) not detected in inventory.')

    # Close inventory
    dm.KeyPress(27)  # Esc
    dm.Delay(500)

    # Standby
    standby_seconds = random.randint(10, 30)
    print(f'[Standby] ⏳ Standing by for {standby_seconds // 60}m {standby_seconds % 60}s before resuming battles...')
    start_standby = time.time()
    while time.time() - start_standby < standby_seconds:
        if is_paused_func and is_paused_func():
            time.sleep(1)
            continue
        remaining = int(standby_seconds - (time.time() - start_standby))
        if remaining > 0 and remaining % 15 == 0:
            print(f'[Standby] Waiting... {remaining // 60}m {remaining % 60}s remaining.')
        time.sleep(1)

    print('[Standby] ✅ Standby completed. Resuming battles...\n')


# ---------------------------------------------------------------------------
# Town Break Routines & Store Purchases
# ---------------------------------------------------------------------------
def simulate_town_activities(dm, duration_seconds=150):
    """Spends duration performing town actions (inventory check, random wanders)."""
    print(f'[Town Activity] Simulating town routine for ~{duration_seconds // 60}m {duration_seconds % 60}s...')
    start_time = time.time()

    organize_items(dm)

    while time.time() - start_time < duration_seconds:
        remaining = int(duration_seconds - (time.time() - start_time))
        print(f'[Town Activity] Active in town: {remaining}s remaining...')

        if random.random() < 0.35:
            dm.MoveTo(random.randint(350, 680), random.randint(250, 520))

        time.sleep(min(15, max(1, remaining)))

    print('[Town Activity] Town routine completed.')


def travel_to_town_via_portal(dm):
    """Travels to town safe zone via portal/map shortcut sequence."""
    print('[Town Travel] 🗺️ Opening map (pressing M every 2s until portal icon is found)...')
    portal_found = False
    px, py = 0, 0
    for _ in range(30):
        (_, px, py) = dm.FindPic(0, 0, 1024, 768, 'break_portal_icon.bmp', '101010', 0.8, 0)
        if px > 0:
            print(f'[Town Travel] Portal icon detected at ({px}, {py}). Moving cursor and clicking...')
            dm.MoveTo(px + 10, py + 10)
            dm.Delay(200)
            dm.LeftClick()
            dm.Delay(1000)
            portal_found = True
            break
        dm.KeyPress(77)  # 'M' key
        time.sleep(2)

    if not portal_found:
        print('[Town Travel] ⚠️ Portal icon not detected after retries. Checking one last time...')
        (_, px, py) = dm.FindPic(0, 0, 1024, 768, 'break_portal_icon.bmp', '101010', 0.8, 0)
        if px > 0:
            dm.MoveTo(px + 10, py + 10)
            dm.Delay(200)
            dm.LeftClick()
            dm.Delay(1000)
            portal_found = True

    # Disable shortcut button if active
    for _ in range(10):
        (_, sx_active, sy_active) = dm.FindPic(0, 0, 1024, 768, 'break_shortcut_active.bmp', '101010', 0.8, 0)
        if sx_active > 0:
            print(f'[Town Travel] Shortcut button is active at ({sx_active}, {sy_active}). Clicking to disable...')
            dm.MoveTo(sx_active + 10, sy_active + 5)
            dm.Delay(150)
            dm.LeftClick()
            dm.Delay(400)
        else:
            break
        time.sleep(0.3)

    # Click hometown icon
    print('[Town Travel] Looking for hometown icon...')
    hometown_clicked = False
    for _ in range(15):
        (_, hx, hy) = dm.FindPic(0, 0, 1024, 768, 'break_hometown_icon.bmp', '101010', 0.75, 0)
        if hx > 0:
            print(f'[Town Travel] Hometown icon found at ({hx}, {hy}). Moving cursor and clicking...')
            dm.MoveTo(hx + 10, hy + 5)
            dm.Delay(200)
            dm.LeftClick()
            dm.Delay(600)
            hometown_clicked = True
            break
        time.sleep(0.5)

    if not hometown_clicked:
        print('[Town Travel] ⚠️ Hometown icon was not found!')

    # Press Enter to travel to hometown
    dm.KeyPress(13)
    time.sleep(3)

    # Click town destination
    print('[Town Travel] Looking for town destination to click...')
    for _ in range(20):
        (_, tx, ty) = dm.FindPic(0, 0, 1024, 768, 'break_town_destination.bmp|break_town_destination2.bmp', '101010', 0.75, 0)
        if tx > 0:
            print(f'[Town Travel] Town destination found at ({tx}, {ty}). Clicking to enter town...')
            dm.MoveTo(tx + 5, ty + 5)
            dm.Delay(200)
            dm.LeftClick()
            dm.Delay(2000)
            break
        time.sleep(0.5)

    # Verify arrival inside town
    print('[Town Travel] Waiting and verifying arrival inside town...')
    in_town = False
    town_verified_images = 'break_town_hanyang.bmp|break_town_verified.bmp'
    attempt = 0
    while not in_town:
        attempt += 1
        (_, vx, vy) = dm.FindPic(0, 0, 1024, 768, town_verified_images, '101010', 0.75, 0)
        if vx > 0:
            print(f'[Town Travel] ✅ Confirmed inside town (detected at ({vx}, {vy})).')
            in_town = True
            break

        if attempt % 3 == 0:
            (_, tx, ty) = dm.FindPic(0, 0, 1024, 768, 'break_town_destination.bmp|break_town_destination2.bmp', '101010', 0.75, 0)
            if tx > 0:
                dm.MoveTo(tx + 5, ty + 5)
                dm.Delay(200)
                dm.LeftClick()
                dm.Delay(1500)

        time.sleep(1)

    print('[Town Travel] Travel to town sequence completed.')


def buy_store_item_and_use(dm, travel_scroll_image='scroll_travel_kingyama.bmp'):
    """Enters store, purchases item, and consumes travel scroll from inventory."""
    print('[Store Interaction] 🏪 Looking for store icon...')
    store_entered = False
    for _ in range(20):
        (_, st_x, st_y) = dm.FindPic(0, 0, 1024, 768, 'break_store_outside_icon.bmp|break_town_store.bmp', '101010', 0.75, 0)
        if st_x > 0:
            dm.MoveTo(st_x + 10, st_y + 10)
            dm.Delay(200)
            dm.LeftClick()
            dm.Delay(1500)
            store_entered = True
            break
        time.sleep(0.5)

    if not store_entered:
        print('[Store Interaction] ⚠️ Store icon not found! Cannot enter store.')
        return

    # Verify inside store
    inside_store = False
    for attempt in range(25):
        (_, s2_x, s2_y) = dm.FindPic(0, 0, 1024, 768, 'break_store_inside_title.bmp', '101010', 0.75, 0)
        if s2_x > 0:
            inside_store = True
            break
        if attempt % 5 == 0 and attempt > 0:
            (_, st_x, st_y) = dm.FindPic(0, 0, 1024, 768, 'break_store_outside_icon.bmp|break_town_store.bmp', '101010', 0.75, 0)
            if st_x > 0:
                dm.MoveTo(st_x + 10, st_y + 10)
                dm.Delay(200)
                dm.LeftClick()
                dm.Delay(1500)
        time.sleep(0.5)

    if not inside_store:
        print('[Store Interaction] ⚠️ Could not confirm inside store! Aborting.')
        return

    # Select item tab
    for _ in range(20):
        (_, it_x, it_y) = dm.FindPic(0, 0, 1024, 768, 'break_store_sell_item.bmp|break_store_tab.bmp', '101010', 0.75, 0)
        if it_x > 0:
            dm.MoveTo(it_x + 5, it_y + 5)
            dm.Delay(200)
            dm.LeftClick()
            dm.Delay(600)
            break
        time.sleep(0.5)

    # Click confirm item button
    for _ in range(20):
        (_, c_x, c_y) = dm.FindPic(0, 0, 1024, 768, 'break_store_confirm_item.bmp|break_store_item.bmp', '101010', 0.75, 0)
        if c_x > 0:
            dm.MoveTo(c_x + 5, c_y + 5)
            dm.Delay(200)
            dm.LeftClick()
            dm.Delay(400)
            break
        time.sleep(0.5)

    # Quantity '1' + Enter
    dm.KeyPress(49)  # '1'
    dm.Delay(300)
    dm.KeyPress(13)  # Enter
    dm.Delay(500)

    # Close store menus (ESC twice)
    dm.KeyPress(27)
    dm.Delay(400)
    dm.KeyPress(27)
    dm.Delay(3000)

    # Open inventory to use scroll
    for _ in range(10):
        (_, bx, _) = dm.FindPic(0, 0, 1024, 768, 'break_inventory_bag.bmp|bag.bmp', '101010', 0.75, 0)
        if bx > 0:
            break
        dm.KeyPress(73)  # 'i'
        time.sleep(2.5)

    # Find and right click travel scroll
    item_used = False
    for _ in range(25):
        (_, ix, iy) = dm.FindPic(0, 0, 1024, 768, travel_scroll_image, '101010', 0.75, 0)
        if ix > 0:
            dm.MoveTo(ix + 5, iy + 5)
            dm.Delay(200)
            dm.RightClick()
            dm.Delay(300)
            dm.KeyPress(13)
            dm.Delay(500)
            item_used = True
            break
        time.sleep(0.5)

    if not item_used:
        print(f'[Store Interaction] ⚠️ Item ({travel_scroll_image}) not detected in inventory.')

    print('[Store Interaction] Store interaction completed.')


def handle_grinding_break_session(dm, reason="", town_activity_min=60, town_activity_max=180, travel_scroll_image='scroll_travel_kingyama.bmp'):
    """Executes full Grinding Break Session: Portal -> Town activities -> Store purchase."""
    town_activity_seconds = random.randint(town_activity_min, town_activity_max)

    print('\n' + '=' * 65)
    print(f'[Break Session] 🛑 Initiating Grinding Break ({reason})')
    print(f'[Break Session] -> Town routine: ~{town_activity_seconds // 60}m {town_activity_seconds % 60}s')
    print('=' * 65)

    travel_to_town_via_portal(dm)
    time.sleep(2)
    simulate_town_activities(dm, town_activity_seconds)
    buy_store_item_and_use(dm, travel_scroll_image=travel_scroll_image)

    print('[Break Session] Town routine complete. Standing by for rest period...\n')
