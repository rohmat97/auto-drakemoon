# Drake.py — Main entrypoint and orchestrator (Fire Gwi)

import os
import sys
import time
import random
import winsound
import gc
import keyboard
from tkinter import messagebox

# Ensure local modules (combat.py, config.py, etc.) are found first
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

# Add the project root for shared modules (PyGameAuto, etc.)
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

from PyGameAuto.Dm import RegDm
from config import (
    DM_REG_KEY, DM_REG_CODE,
    FORMATION_REGIONS, MONSTER_DIRECTION_REGIONS, MONSTER_CHECKS,
)
from window_manager import move_game_window, bind_game_window
from Battle.Drakemoon.kingyama.combat import (
    check_revive, has_non_black_in_region, check_formation,
    execute_battle_strategy, initial_call,
)
from Battle.Drakemoon.kingyama.combat2 import execute_battle_strategy2
from Battle.Drakemoon.kingyama.combat3 import execute_battle_strategy3
from Battle.Drakemoon.kingyama.combat import initiation_battle
from captcha_solver import solve_captcha
from session_scheduler import SessionScheduler, SessionConfig

# ---------------------------------------------------------------------------
# Image pattern strings
# ---------------------------------------------------------------------------
MONSTER_IMAGES = '|'.join([rf'koh{i}.bmp' for i in range(1, 18)])
DRAKE_IMAGES = '|'.join([rf'Character\drakemoon\drake{i}.bmp' for i in range(1, 12)])

# ---------------------------------------------------------------------------
# State variables
# ---------------------------------------------------------------------------
paused = False
last_monster_seen_time = time.time()
no_monster_search_count = 0


def is_paused():
    return paused


# ---------------------------------------------------------------------------
# Grinding Session & Break Guidelines Configuration
# ---------------------------------------------------------------------------
# Hunt session duration before break: 1 to 2 hours (in seconds)
HUNT_SESSION_MIN_SECONDS = 60 * 60    # 1 hour (3600s)
HUNT_SESSION_MAX_SECONDS = 120 * 60   # 2 hours (7200s)

# Continuous battles threshold before break: 100 to 150 battles
BATTLES_BEFORE_BREAK_MIN = 100
BATTLES_BEFORE_BREAK_MAX = 150

# Total break duration: 5 to 10 minutes (in seconds)
BREAK_DURATION_MIN_SECONDS = 5 * 60   # 5 minutes (300s)
BREAK_DURATION_MAX_SECONDS = 10 * 60  # 10 minutes (600s)

# Town activity duration to reset server combat metrics: 2 to 3 minutes (in seconds)
TOWN_ACTIVITY_MIN_SECONDS = 2 * 60    # 2 minutes (120s)
TOWN_ACTIVITY_MAX_SECONDS = 3 * 60    # 3 minutes (180s)


# ---------------------------------------------------------------------------
# Overworld helpers
# ---------------------------------------------------------------------------
def relogin(dm):
    """Press Esc to open System Menu, then click 'Char Select'."""
    print('Relogin: Opening System Menu...')
    dm.KeyPress(27)  # Esc to open System Menu
    dm.Delay(500)
    dm.MoveTo(509, 290)
    dm.Delay(500)
    dm.LeftClick()
    dm.Delay(500)
    dm.KeyPress(13)
    dm.Delay(5000)
    dm.KeyPress(13)
    dm.Delay(2500)


def simulate_town_activities(dm, duration_seconds=150):
    """
    Spends 2-3 minutes performing town actions (마을):
    - Opening/browsing inventory and mercenary tabs
    - Organizing items, checking satiety/healing
    - Natural mouse movements and idle pauses
    This breaks the consecutive combat loop registered by server tracking metrics.
    """
    print(f'[Town Activity] Simulating town routine for ~{duration_seconds // 60}m {duration_seconds % 60}s...')
    start_time = time.time()

    # 1. Open Inventory ('i')
    print('[Town Activity] Opening inventory to organize items...')
    dm.KeyPress(73)  # 'i' key
    dm.Delay(600)

    # 2. Iterate through mercenary tabs (keys: 1..9, 0, -, =)
    merc_keys = [49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 189, 187]
    random.shuffle(merc_keys)
    for key in merc_keys:
        if time.time() - start_time >= (duration_seconds - 30):
            break
        dm.KeyPress(key)
        dm.Delay(random.randint(300, 600))

        # Simulate inspecting inventory grid slots (coords 560~760, 140~360)
        for _ in range(random.randint(2, 4)):
            rx = random.randint(560, 760)
            ry = random.randint(140, 360)
            dm.MoveTo(rx, ry)
            dm.Delay(random.randint(150, 400))

    # 3. Replenish satiety / check food (Alt + 2)
    dm.KeyDown(18)
    dm.KeyPress(50)
    dm.KeyUp(18)
    dm.Delay(300)

    # 4. Close Inventory ('i')
    print('[Town Activity] Closing inventory...')
    dm.KeyPress(73)  # 'i' key
    dm.Delay(500)

    # 5. Spend remaining town activity time with natural pacing & minor idle / checks
    while time.time() - start_time < duration_seconds:
        remaining = int(duration_seconds - (time.time() - start_time))
        print(f'[Town Activity] Active in town: {remaining}s remaining...')

        action = random.random()
        if action < 0.35:
            dm.MoveTo(random.randint(350, 680), random.randint(250, 520))
        elif action < 0.55:
            dm.KeyDown(18)
            dm.KeyPress(50)
            dm.KeyUp(18)

        time.sleep(min(15, max(1, remaining)))

    print('[Town Activity] Town routine completed.')


def travel_to_town_via_portal(dm):
    """
    Travels to town via portal/map sequence:
    1. Press 'M' every 2s until portal icon (break_portal_icon.bmp) is found.
    2. Move cursor to portal icon and left click to open travel dialog.
    3. If Shortcut button is active (break_shortcut_active.bmp), left click until disabled (break_shortcut_disabled.bmp).
    4. Left click hometown icon (break_hometown_icon.bmp).
    5. Press Enter to confirm travel to hometown.
    6. Left click town destination (break_town_destination.bmp) to travel into town.
    7. Validate arrival in town using break_town_verified.bmp.
    """
    print('[Town Travel] 🗺️ Opening map (pressing M every 2s until portal icon is found)...')
    portal_found = False
    px, py = 0, 0
    for attempt in range(30):
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
            print(f'[Town Travel] Portal icon detected at ({px}, {py}). Clicking...')
            dm.MoveTo(px + 10, py + 10)
            dm.Delay(200)
            dm.LeftClick()
            dm.Delay(1000)
            portal_found = True

    # Check and toggle Shortcut button until disabled
    print('[Town Travel] Checking shortcut button status...')
    for _ in range(10):
        (_, sx_active, sy_active) = dm.FindPic(0, 0, 1024, 768, 'break_shortcut_active.bmp', '101010', 0.8, 0)
        if sx_active > 0:
            print(f'[Town Travel] Shortcut button is active at ({sx_active}, {sy_active}). Clicking to disable...')
            dm.MoveTo(sx_active + 10, sy_active + 5)
            dm.Delay(150)
            dm.LeftClick()
            dm.Delay(400)
        else:
            print('[Town Travel] Shortcut button is disabled.')
            break
        time.sleep(0.3)

    # Click hometown icon (4th picture)
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
        print('[Town Travel] ⚠️ Hometown icon was not found! Checking portal state again...')

    # Press Enter to go to hometown
    print('[Town Travel] Pressing Enter to confirm travel to hometown...')
    dm.KeyPress(13)  # Enter key
    time.sleep(3)

    # Left click town destination to go to town
    print('[Town Travel] Looking for town destination to click...')
    town_clicked = False
    for attempt in range(20):
        (_, tx, ty) = dm.FindPic(0, 0, 1024, 768, 'break_town_destination.bmp|break_town_destination2.bmp', '101010', 0.75, 0)
        if tx > 0:
            print(f'[Town Travel] Town destination found at ({tx}, {ty}). Clicking to enter town...')
            dm.MoveTo(tx + 5, ty + 5)
            dm.Delay(200)
            dm.LeftClick()
            dm.Delay(2000)
            town_clicked = True
            break
        time.sleep(0.5)

    if not town_clicked:
        print('[Town Travel] ⚠️ Town destination not detected on screen after retries.')

    # Check town confirmation images (Hanyang title, verified, verified2, verified3) until found
    print('[Town Travel] Waiting and verifying arrival inside town...')
    in_town = False
    town_verified_images = 'break_town_hanyang.bmp'
    attempt = 0
    while not in_town:
        attempt += 1
        (_, vx, vy) = dm.FindPic(0, 0, 1024, 768, town_verified_images, '101010', 0.75, 0)
        if vx > 0:
            print(f'[Town Travel] ✅ Confirmed inside town (detected at ({vx}, {vy})).')
            in_town = True
            break

        # Every 3-4 seconds, if destination is still visible, re-click destination
        if attempt % 3 == 0:
            (_, tx, ty) = dm.FindPic(0, 0, 1024, 768, 'break_town_destination.bmp|break_town_destination2.bmp', '101010', 0.75, 0)
            if tx > 0:
                print(f'[Town Travel] Re-clicking town destination at ({tx}, {ty})...')
                dm.MoveTo(tx + 5, ty + 5)
                dm.Delay(200)
                dm.LeftClick()
                dm.Delay(1500)

        time.sleep(1)

    print('[Town Travel] Travel to town sequence completed.')


def buy_store_item_and_use(dm):
    """
    Enters store, interacts with item, and consumes it from inventory:
    1. 1st icon: Locate store icon (break_store_outside_icon.bmp), move cursor and left click to enter.
    2. 2nd icon: Validate inside store by locating (break_store_inside_title.bmp).
    3. 3rd icon: Locate item (break_store_sell_item.bmp) and left click it.
    4. 4th icon: Check position of 4th icon (break_store_confirm_item.bmp), left click it, press '1', press Enter.
    5. Press Esc 2 times to close store menus.
    6. Open inventory ('i'), right-click item at (600, 265), and confirm with Enter.
    """
    # 1. Locate store icon outside in town and left click to enter
    print('[Store Interaction] 🏪 Looking for store icon (1st icon)...')
    store_entered = False
    for attempt in range(20):
        (_, st_x, st_y) = dm.FindPic(0, 0, 1024, 768, 'break_store_outside_icon.bmp|break_town_store.bmp', '101010', 0.75, 0)
        if st_x > 0:
            print(f'[Store Interaction] Store icon found at ({st_x}, {st_y}). Moving cursor and clicking...')
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

    # 2. Verify inside store by locating 2nd icon (Store title)
    print('[Store Interaction] Verifying inside store (2nd icon)...')
    inside_store = False
    for attempt in range(25):
        (_, s2_x, s2_y) = dm.FindPic(0, 0, 1024, 768, 'break_store_inside_title.bmp', '101010', 0.75, 0)
        if s2_x > 0:
            print(f'[Store Interaction] ✅ Confirmed inside store (Store title found at ({s2_x}, {s2_y})).')
            inside_store = True
            break
        # If not detected, re-click store outside icon if still on screen
        if attempt % 5 == 0 and attempt > 0:
            (_, st_x, st_y) = dm.FindPic(0, 0, 1024, 768, 'break_store_outside_icon.bmp|break_town_store.bmp', '101010', 0.75, 0)
            if st_x > 0:
                print(f'[Store Interaction] Re-clicking store icon at ({st_x}, {st_y})...')
                dm.MoveTo(st_x + 10, st_y + 10)
                dm.Delay(200)
                dm.LeftClick()
                dm.Delay(1500)
        time.sleep(0.5)

    if not inside_store:
        print('[Store Interaction] ⚠️ Could not confirm inside store! Aborting subsequent store actions.')
        return

    # 3. Locate 3rd icon (item) and left click
    print('[Store Interaction] Looking for 3rd icon (item)...')
    item_clicked = False
    for _ in range(20):
        (_, it_x, it_y) = dm.FindPic(0, 0, 1024, 768, 'break_store_sell_item.bmp|break_store_tab.bmp', '101010', 0.75, 0)
        if it_x > 0:
            print(f'[Store Interaction] 3rd icon found at ({it_x}, {it_y}). Moving cursor and clicking...')
            dm.MoveTo(it_x + 5, it_y + 5)
            dm.Delay(200)
            dm.LeftClick()
            dm.Delay(600)
            item_clicked = True
            break
        time.sleep(0.5)

    if not item_clicked:
        print('[Store Interaction] ⚠️ 3rd icon not found! Aborting subsequent store actions.')
        return

    # 4. Check 4th icon position, left click it, press '1', then press Enter
    print('[Store Interaction] Looking for 4th icon position...')
    confirm_clicked = False
    for _ in range(20):
        (_, c_x, c_y) = dm.FindPic(0, 0, 1024, 768, 'break_store_confirm_item.bmp|break_store_item.bmp', '101010', 0.75, 0)
        if c_x > 0:
            print(f'[Store Interaction] 4th icon found at ({c_x}, {c_y}). Moving cursor and clicking...')
            dm.MoveTo(c_x + 5, c_y + 5)
            dm.Delay(200)
            dm.LeftClick()
            dm.Delay(400)
            confirm_clicked = True
            break
        time.sleep(0.5)

    if not confirm_clicked:
        print('[Store Interaction] ⚠️ 4th icon not found! Aborting subsequent store actions.')
        return

    # Press '1'
    print('[Store Interaction] Pressing 1...')
    dm.KeyPress(49)  # '1' key
    dm.Delay(300)

    # Press Enter
    print('[Store Interaction] Pressing Enter...')
    dm.KeyPress(13)  # Enter key
    dm.Delay(500)

    # 5. Press Esc 2 times to close store menus
    print('[Store Interaction] Pressing Esc 2 times to close menus...')
    dm.KeyPress(27)  # Esc
    dm.Delay(400)
    dm.KeyPress(27)  # Esc
    dm.Delay(3000)

    # 6. Open inventory ('i'), make sure it is open via Bag icon, right-click item at (600, 265), and confirm with Enter
    print('[Store Interaction] Opening inventory to use item at (600, 265)...')
    inv_open = False
    for attempt in range(10):
        # Check if inventory Bag title is visible
        (_, bx, by) = dm.FindPic(0, 0, 1024, 768, 'break_inventory_bag.bmp|bag.bmp', '101010', 0.75, 0)
        if bx > 0:
            print(f'[Store Interaction] ✅ Inventory is open (Bag title detected at ({bx}, {by})).')
            inv_open = True
            break
        print('[Store Interaction] Pressing i to open inventory...')
        dm.KeyPress(73)  # 'i' key
        time.sleep(2.5)

    if not inv_open:
        print('[Store Interaction] ⚠️ Inventory Bag title not confirmed, attempting final check...')
        (_, bx, by) = dm.FindPic(0, 0, 1024, 768, 'break_inventory_bag.bmp|bag.bmp', '101010', 0.75, 0)
        if bx > 0:
            inv_open = True

    # Right-click item at (600, 265) and confirm with Enter
    dm.MoveTo(600, 265)
    dm.Delay(200)
    dm.RightClick()
    dm.Delay(300)
    dm.KeyPress(13)  # Enter key
    dm.Delay(500)

    print('[Store Interaction] Store interaction and item use completed successfully.')


def handle_grinding_break_session(dm, reason=""):
    """
    Executes Grinding Session Break:
    1. Leaves combat zone and travels to town safe zone via portal sequence.
    2. Spends 2-3 minutes performing town activities FIRST (inventory, healing, tab checks).
    3. Enters store, purchases item, and uses it from inventory.
    4. Standby duration is managed cleanly by SessionScheduler.
    """
    # town_activity_seconds = random.randint(TOWN_ACTIVITY_MIN_SECONDS, TOWN_ACTIVITY_MAX_SECONDS)
    town_activity_seconds = random.randint(2, 5) #test purpose 

    print('\n' + '=' * 65)
    print(f'[Break Session] 🛑 Initiating Grinding Break ({reason})')
    print(f'[Break Session] -> Town routine: ~{town_activity_seconds // 60}m {town_activity_seconds % 60}s')
    print('=' * 65)

    # 1. Travel to town safe zone via portal shortcut routine
    print('[Break Session] Executing portal travel sequence to enter town safe zone...')
    travel_to_town_via_portal(dm)
    time.sleep(2)

    # 2. Perform town activities FIRST upon arriving in town
    simulate_town_activities(dm, town_activity_seconds)

    # 3. Enter store, purchase item, and use it
    buy_store_item_and_use(dm)

    print('[Break Session] Town routine complete. Standing by for rest period...\n')


def check_food(dm):
    """Check hunger level and consume food if needed.
    Returns True if script should pause (food exhausted)."""
    global paused
    if not hasattr(check_food, "eat_count"):
        check_food.eat_count = 0
        
    check_food.eat_count += 1
    dm.KeyDown(18)
    dm.KeyPress(50)
    dm.KeyUp(18)
    dm.Delay(100)

    (_, x_bread, y_bread) = dm.FindPic(43, 644, 101, 692, 'bread.bmp', '050505', 0.8, 0)
    if x_bread > 0:
        print('Replenishing satiety')
        print('Replenished satiety 500 times, pausing script... ' + str(check_food.eat_count) + '/500')
        if check_food.eat_count >= 500:
            relogin(dm)
            check_food.eat_count = 0
            paused = True
            print('All commands paused, press delete to resume...')
            dm.UnBindWindow()
            return True

    (_, x_empty, y_empty) = dm.FindPic(450, 350, 680, 480, 'emptyfoodinter.bmp', '050505', 0.8, 0)
    if x_empty > 0:
        print('Satiety depleted, script paused')
        check_food.eat_count = 0
        paused = True
        print('All commands paused, press delete to resume...')
        dm.UnBindWindow()
        return True
    return False


def check_dead_mercenary(dm):
    """If a dead mercenary is detected, consume half-chicken soup."""
    (_, x, _) = dm.FindPic(0, 0, 110, 650, DRAKE_IMAGES, '050505', 0.8, 0)
    if x > 0:
        print('Dead mercenary detected, opening inventory to revive...')
        # Press 'i' to open inventory
        dm.KeyPress(73)
        dm.Delay(500)
        
        # Save a debug screen capture of what DaMo actually sees
        debug_path = os.path.join(dm.getPath(), 'debug_inventory.bmp')
        dm.Capture(0, 0, 1024, 768, debug_path)
        print(f"Debug screen capture saved to: {debug_path}")
        
        # Search for revival.bmp in main character's inventory first
        (_, rx_main, ry_main) = dm.FindPic(0, 0, 1024, 768, 'revival.bmp', '101010', 0.7, 0)
        print(f"Before selection loop -> Found revival.bmp at: ({rx_main}, {ry_main})")
        
        # Select and revive each mercenary from 2 to 12: 2, 3, 4, 5, 6, 7, 8, 9, 0, -, =
        keys = [50, 51, 52, 53, 54, 55, 56, 57, 48, 189, 187]
        for key in keys:
            dm.KeyPress(key)
            dm.Delay(200)  # Increased delay to allow inventory UI to load
            dm.MoveTo(600,150)
            dm.Delay(200)
            dm.RightClick()
            dm.Delay(200)
        
        # Press 'i' again to close inventory
        dm.KeyPress(73)
        dm.Delay(500)


def handle_captcha(dm, x_captcha, y_captcha):
    """
    Handles captcha dialog:
    1. Moves cursor away so it doesn't block the characters.
    2. Waits 2 seconds.
    3. Captures the captcha region to temp_captcha.bmp.
    4. Solves the captcha code via solve_captcha().
    5. Types the code directly (input is auto-focused).
    6. Moves cursor to button (386, 556, 434, 568) and right clicks.
    """
    print(f'[Captcha Handler] Captcha dialog located at ({x_captcha}, {y_captcha}).')
    # 1. Move cursor away from the dialog
    dm.MoveTo(0, 0)
    
    # 2. Wait for 2 seconds as requested
    print('[Captcha Handler] Waiting 2 seconds before solving...')
    time.sleep(2.0)

    # 3. Capture captcha rectangle relative to detect_captcha match
    x1 = max(0, x_captcha + 3)
    y1 = max(0, y_captcha - 84)
    x2 = min(1024, x_captcha + 266)
    y2 = min(768, y_captcha + 6)

    captcha_save_path = os.path.join(dm.getPath(), 'temp_captcha.bmp')
    dm.Capture(x1, y1, x2, y2, captcha_save_path)
    dm.Delay(100)

    # 4. Recognize captcha text
    code = solve_captcha(captcha_save_path, debug=True)
    print(f'[Captcha Handler] Solved code: "{code}"')

    # 5. Type the characters into the form (input is auto-focused)
    if code:
        for char in code:
            dm.KeyPressChar(char)
            dm.Delay(80)
    else:
        print('[Captcha Handler] Warning: No code recognized.')

    dm.Delay(200)

    # 6. Move cursor to button position (408,440,409,441) and left click
    dm.MoveTo(405, 440)
    dm.Delay(150)
    dm.LeftClick()
    dm.Delay(1000)

    print(f'[Captcha Handler] Moved to (405, 440) and left-clicked button successfully.')
    return True


def check_anti_cheat(dm):
    """Returns True if anti-cheat (horse-stamp missing or captcha dialog popup) is detected."""
    # 1. Check horse stamp vs bread indicator
    (_, x_horse, _) = dm.FindPic(599, 21, 650, 49, r'anti_cheat\horse.bmp', '050505', 0.8, 0)
    (_, x_bread, _) = dm.FindPic(50, 650, 93, 689, r'anti_cheat\bread.bmp', '050505', 0.8, 0)
    if x_horse <= 0 and x_bread > 0:
        print('[Anti-Cheat] Horse stamp missing while bread icon is visible! Triggering relogin...')
        relogin(dm)
        print('[Anti-Cheat] Idling for 5 minutes...')
        for m in range(5, 0, -1):
            print(f'[Anti-Cheat] Waiting... {m} minute(s) remaining.')
            time.sleep(60)
        print('[Anti-Cheat] 5 minutes passed. Triggering second relogin...')
        relogin(dm)
        return True

    # 2. Check captcha popup box
    (_, x_captcha, y_captcha) = dm.FindPic(0, 0, 1024, 768, r'anti_cheat\detect_captcha.bmp', '050505', 0.8, 0)
    if x_captcha > 0:
        print(f'[Anti-Cheat] Captcha dialog detected at ({x_captcha}, {y_captcha})!')
        handle_captcha(dm, x_captcha, y_captcha)

    return False


def check_stamina(dm):
    """Check for the no stamina indicator. Pauses, unbinds, and shows popup if detected."""
    global paused
    (_, x_no_stamina, _) = dm.FindPic(90, 695, 99, 703, 'nostamina.bmp', '050505', 1, 0)
    if x_no_stamina >= 0:
        print('No stamina detected, pausing...')
        paused = True
        dm.UnBindWindow()
        messagebox.showinfo('No Stamina', 'No stamina detected, pausing...')
        return True
    return False


def play_alert_sound(dm):
    """Play an alert sound when anti-cheat is triggered."""
    try:
        sound_path = os.path.join(dm.getPath(), 'whatsapp.wav')
        if os.path.exists(sound_path):
            winsound.PlaySound(sound_path, winsound.SND_FILENAME)
    except Exception:
        pass


def is_in_battle(dm):
    (_, x, _) = dm.FindPic(959, 666, 1016, 747, 'battle3.bmp', '050505', 0.8, 0)
    return x > 0


# ---------------------------------------------------------------------------
# Overworld: find and engage a monster
# ---------------------------------------------------------------------------
def find_and_engage_monster(dm):
    global last_monster_seen_time, no_monster_search_count
    """Search for a monster on the overworld and attempt to enter battle.
    Returns True if battle was entered, False otherwise."""
    current_time = time.time()
    if not hasattr(find_and_engage_monster, "last_revive_check"):
        find_and_engage_monster.last_revive_check = 0
    if not hasattr(find_and_engage_monster, "last_dead_check"):
        find_and_engage_monster.last_dead_check = 0

    if current_time - find_and_engage_monster.last_revive_check > 5.0:
        find_and_engage_monster.last_revive_check = current_time
        if check_revive(dm, is_paused):
            print('Waiting for town to load after reviving main character...')
            time.sleep(5)  # Wait for the loading screen to pass
            return False

    if current_time - find_and_engage_monster.last_dead_check > 2.0:
        find_and_engage_monster.last_dead_check = current_time
        check_dead_mercenary(dm)

    (_, x, y) = dm.FindPic(96, 84, 964, 600, MONSTER_IMAGES, '050505', 0.8, 0)
    if x <= 0:
        current_time_check = time.time()
        if current_time_check - last_monster_seen_time > 10:
            no_monster_search_count += 1
            print(f'[Active] Searching for monsters on overworld... ({no_monster_search_count}/10)')
            last_monster_seen_time = current_time_check
            if no_monster_search_count >= 10:
                print('No monsters found 10 times, pressing ESC to dismiss any popups...')
                dm.KeyPress(27)
                dm.Delay(300)
                no_monster_search_count = 0
        return False

    no_monster_search_count = 0
    last_monster_seen_time = time.time()
    print(f'Monster found at coords: ({x}, {y})')
    dm.MoveTo(x, y)
    dm.Delay(150)
    dm.RightClick()
    dm.Delay(300)

    print('Waiting to enter battle screen... (max 3s)')
    start_time = time.time()
    attempt = 1

    while time.time() - start_time < 2:
        check_anti_cheat(dm)

        if is_in_battle(dm):
            print('✅ Successfully entered battle screen')
            return True

        if time.time() - start_time > 0.5 and attempt == 1:
            print('Battle not entered, right-clicking monster again...')
            dm.MoveTo(x, y)
            dm.Delay(100)
            dm.RightClick()
            dm.Delay(300)
            attempt = 2

        time.sleep(0.08)

    time.sleep(0.1)
    return False

# ---------------------------------------------------------------------------
# Battle phase: detect formation and execute strategy
# ---------------------------------------------------------------------------
def handle_battle(dm):
    """Process a single battle until it ends."""
    print('Entered battle screen')
    action_executed = False
    no_monster_count = 0

    while True:
        if paused:
            time.sleep(1)
            continue

        if action_executed:
            print('Waiting for battle screen to close...')
            while is_in_battle(dm):
                print('Still in battle field, pressing Esc to exit...')
                for _ in range(2):
                    dm.KeyPress(27)
                    dm.Delay(20)
                time.sleep(2)

            print('Battle screen ended')
            break

        if not action_executed:
            for direction, regions in FORMATION_REGIONS.items():
                if action_executed:
                    break
                if check_formation(dm, regions[0], regions[1]):
                    print(f'Formation position detected: {direction}')
                    time.sleep(0.1)
                    dm.MoveTo(640, 425)
                    dm.Delay(25)
                    key_code = None
                    if direction == 'West':
                        key_code = 39  # Arrow Right
                    elif direction == 'East':
                        key_code = 37  # Arrow Left
                    elif direction == 'North':
                        key_code = 40  # Arrow Down
                    elif direction == 'South':
                        key_code = 38  # Arrow Up

                    if key_code is not None:
                        dm.KeyDown(key_code)
                        dm.Delay(400)
                        dm.KeyUp(key_code)
                    dm.Delay(25)
                    initial_call(dm)
                    dm.Delay(25)
                    initiation_battle(dm)
                    dm.Delay(25)
                    dm.KeyPress(49)
                    dm.Delay(25)
                    dm.KeyPress(49)
                    dm.Delay(25)

                    found_monsters = []
                    duration = 0
                    print(f'Scanning {direction} formation up to 30 times for monsters...')
                    for scan_attempt in range(10):
                        for monster_dir in MONSTER_CHECKS[direction]:
                            if monster_dir not in found_monsters:
                                (x1, y1, x2, y2) = MONSTER_DIRECTION_REGIONS[monster_dir]
                                if has_non_black_in_region(dm, x1, y1, x2, y2, monster_dir):
                                    found_monsters.append(monster_dir)
                        if len(found_monsters) >= 2:
                            duration = 8  # Break early if we found at least 2 monsters
                            break
                        else:
                            duration = 12

                        time.sleep(0.25)

                    if found_monsters:
                        print(f'Total monsters found: {len(found_monsters)} -> {found_monsters}')
                        for i, monster_dir in enumerate(found_monsters):
                            print(f'Executing strategy [{i+1}/{len(found_monsters)}] → Formation: {direction} | Monster: {monster_dir}')
                            if i == 0: execute_battle_strategy(dm, direction, monster_dir)
                            if i == 1: execute_battle_strategy2(dm, direction, monster_dir)
                            if i == 2: execute_battle_strategy3(dm, direction, monster_dir)

                            if i < len(found_monsters) - 1:
                                print(f'Waiting {i} before next battle...')
                                if i == 0:
                                    dm.KeyPress(49)
                                    dm.Delay(100)
                                    dm.KeyPress(49)
                                    dm.Delay(100)
                                elif i == 1:
                                    time.sleep(duration - 4)
                                    dm.KeyPress(49)
                                    dm.Delay(100)
                                    dm.KeyPress(49)
                                    dm.Delay(100)
                                else:
                                    time.sleep(duration)
                                    dm.KeyPress(49)
                                    dm.Delay(100)
                                    dm.KeyPress(49)
                                    dm.Delay(100)
                            else:
                                time.sleep(duration)

                        action_executed = True
                        break

            no_monster_count += 1
            if no_monster_count >= 20:
                print('No monsters found 20 times. Exiting battle...')
                time.sleep(2)
                no_monster_count = 0
            else:
                time.sleep(0.25)

        # Check if battle ended
        if not is_in_battle(dm):
            print('Battle screen ended')
            break
        else:
            time.sleep(0.15)

# ---------------------------------------------------------------------------
# Main game loop
# ---------------------------------------------------------------------------
def run_main_script():
    global paused
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

    if getattr(sys, 'frozen', None):
        basedir = sys._MEIPASS
    else:
        basedir = _PROJECT_ROOT
    dm.setPath(os.path.join(basedir, 'Resource'))

    paused = False
    last_toggle_time = 0

    def on_delete_press(event=None):
        global paused
        nonlocal last_toggle_time
        current_time = time.time()
        if current_time - last_toggle_time < 0.3:
            return
        if event.name == 'delete':
            last_toggle_time = current_time
            paused = not paused
            if paused:
                print('All commands paused, press delete to resume...')
                dm.UnBindWindow()
            else:
                print('All commands resumed...')
                bind_game_window(dm, hwnd)

    keyboard.on_press_key('delete', on_delete_press)

    def on_pageup_press(event=None):
        nonlocal last_toggle_time
        current_time = time.time()
        if current_time - last_toggle_time < 0.3:
            return
        if event.name == 'page up':
            last_toggle_time = current_time
            print('Page Up pressed: restarting run.bat and closing current terminal...')
            try:
                dm.UnBindWindow()
            except Exception:
                pass
            try:
                bat_path = os.path.join(_SCRIPT_DIR, 'run.bat')
                os.startfile(bat_path)
            except Exception as e:
                print(f"Error starting run.bat: {e}")
            try:
                os.kill(os.getppid(), 9)
            except Exception as e:
                print(f"Error killing parent terminal: {e}")
            sys.exit(0)

    keyboard.on_press_key('page up', on_pageup_press)

    # Disable automatic GC to avoid stutters during time-sensitive key presses
    gc.disable()
    gc.collect()

    try:
        loop_counter = 0

        def primary_game_step() -> bool:
            """
            Executes one overworld exploration/combat tick.
            Returns True if a battle was fought, False otherwise.
            """
            nonlocal loop_counter

            if check_stamina(dm):
                scheduler.stop()
                return False

            check_anti_cheat(dm)

            battle_entered = find_and_engage_monster(dm)
            if battle_entered or is_in_battle(dm):
                handle_battle(dm)
                gc.collect()  # Clean up COM references and memory after battle

                # Check revive and food after battle
                check_revive(dm, is_paused)
                check_food(dm)

                elapsed_mins = int((time.time() - scheduler.session_start_time) // 60)
                target_mins = int(scheduler._target_duration // 60)
                print(
                    f'Battles completed: {scheduler.current_iteration + 1}/{scheduler._target_iterations} '
                    f'(Grinding session: {elapsed_mins}m/{target_mins}m)'
                )
                return True

            loop_counter += 1
            if loop_counter % 50 == 0:
                gc.collect()  # Periodically clean up during overworld exploration

            return False

        def session_cooldown_handler(reason: str, iterations: int, elapsed_sec: float) -> None:
            """Triggered by SessionScheduler when rest threshold (time/iterations) is reached."""
            handle_grinding_break_session(dm, reason=reason)
            gc.collect()

        session_cfg = SessionConfig(
            max_iterations=(BATTLES_BEFORE_BREAK_MIN, BATTLES_BEFORE_BREAK_MAX),
            # max_iterations=(1, 1),  # For testing
            max_duration_seconds=(HUNT_SESSION_MIN_SECONDS, HUNT_SESSION_MAX_SECONDS),
            cooldown_seconds=(BREAK_DURATION_MIN_SECONDS, BREAK_DURATION_MAX_SECONDS),
            loop_interval_seconds=0.15,
        )

        scheduler = SessionScheduler(
            task_func=primary_game_step,
            cooldown_func=session_cooldown_handler,
            pause_check=is_paused,
            config=session_cfg,
        )

        # Start continuous scheduler loop
        scheduler.run()

    except KeyboardInterrupt:
        print('Program interrupted.')
    finally:
        keyboard.unhook_all()
        gc.enable()  # Re-enable GC on exit
        gc.collect()
        print('Cleanup complete, program exited.')


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    run_main_script()
