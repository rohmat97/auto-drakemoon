# Drake.py — Main entrypoint and orchestrator (Dark Gujimo Elder)

from os import system
import os
import sys
import time
import keyboard
import winsound
import gc
from tkinter import messagebox

# Ensure local modules (combat.py, config.py, etc.) are found first
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

# Add the project root for shared modules (PyGameAuto, etc.)
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..','..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

from PyGameAuto.Dm import RegDm
from config import (
    DM_REG_KEY, DM_REG_CODE,
    FORMATION_REGIONS, MONSTER_DIRECTION_REGIONS, MONSTER_CHECKS,
)
from window_manager import move_game_window, bind_game_window
from Battle.Nytheris.ikan_tol.combat import (
    check_revive, has_non_black_in_region, check_formation,
    execute_battle_strategy,
)

# ---------------------------------------------------------------------------
# Image pattern strings (kept here to avoid bloating config with long literals)
# ---------------------------------------------------------------------------
MONSTER_IMAGES = '|'.join([rf'fish\fish{i}.bmp' for i in range(1, 21)])
DRAKE_IMAGES = '|'.join([rf'drake\drake{i}.bmp' for i in range(1, 18)])

# ---------------------------------------------------------------------------
# Pause state  (shared via closure / global)
# ---------------------------------------------------------------------------
paused = False
anti_cheat_detected = False
last_monster_seen_time = time.time()
no_monster_search_count = 0


def is_paused():
    return paused


# ---------------------------------------------------------------------------
# Overworld helpers
# ---------------------------------------------------------------------------
def check_food(dm):
    """Check hunger level and consume food if needed.
    Returns True if script should pause (food exhausted)."""
    global paused
    if not hasattr(check_food, "eat_count"):
        check_food.eat_count = 0

    (_, x_food, y_food) = dm.FindPic(52, 649, 246, 684, 'food.bmp', '050505', 0.8, 0)
    (_, x_bread, y_bread) = dm.FindPic(43, 644, 101, 692, 'bread.bmp', '050505', 0.8, 0)

    if x_food > 0:
        # Satiety is sufficient, reset the eat counter
        check_food.eat_count = 0
    elif x_bread > 0:
        print('Replenishing satiety')
        if (check_food.eat_count % 2 == 0):
            dm.KeyDown(18)
            dm.KeyPress(50)
            dm.KeyUp(18)
            dm.Delay(100)
        
        check_food.eat_count += 1
        print('Replenished satiety 500 times, pausing script... ' + str(check_food.eat_count) + '/500')
        if check_food.eat_count >= 800:
            def logout(dm):
                print('Logout: Opening System Menu...')
                dm.KeyPress(27)  # Esc to open System Menu
                dm.Delay(500)
                dm.MoveTo(509, 290)
                dm.Delay(500)
                dm.LeftClick()
                dm.Delay(500)
                dm.KeyPress(13)
                dm.Delay(3000)
                dm.KeyPress(13)
                dm.Delay(500)
            
            logout(dm)
            check_food.eat_count = 0
            paused = True
            print('All commands paused, press delete to resume...')
            dm.UnBindWindow()
            return True

    (_, x_empty, y_empty) = dm.FindPic(582, 418, 617, 446, 'emptyfooddrake.bmp', '050505', 0.8, 0)
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
            dm.Delay(100)  # Increased delay to allow inventory UI to load
            dm.MoveTo(600,150)
            dm.Delay(100)
            dm.RightClick()
            dm.Delay(100)
        
        # Press 'i' again to close inventory
        dm.KeyPress(73)
        dm.Delay(500)


def check_anti_cheat(dm):
    """Returns True if the anti-cheat horse-stamp is detected."""
    (_, x_horse, _) = dm.FindPic(599, 21, 650, 49, r'anti_cheat\horse.bmp', '050505', 0.8, 0)
    (_, x_bread, _) = dm.FindPic(50, 650, 93, 689, r'anti_cheat\bread.bmp', '050505', 0.8, 0)
    if x_horse <= 0 and x_bread > 0:
        return True
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


def check_community_popup(dm):
    """Check for the Community popup and press ESC once to dismiss it.
    Returns True if the popup was detected and dismissed."""
    (_, x, _) = dm.FindPic(0, 0, 1024, 768, 'community.bmp', '050505', 0.8, 0)
    if x > 0:
        print('Community popup detected, pressing ESC to dismiss...')
        dm.KeyPress(27)  # Press ESC once
        dm.Delay(300)
        return True
    return False


def is_in_battle(dm):
    (_, x, _) = dm.FindPic(959, 666, 1016, 747, 'battle.bmp', '050505', 0.8, 0)
    return x > 0


# ---------------------------------------------------------------------------
# Overworld: find and engage a monster
# ---------------------------------------------------------------------------
def find_and_engage_monster(dm):
    global last_monster_seen_time, anti_cheat_detected, no_monster_search_count
    """Search for a monster on the overworld and attempt to enter battle.
    Returns True if battle was entered, False otherwise."""
    if check_revive(dm, is_paused):
        print('Waiting for town to load after reviving main character...')
        time.sleep(5)  # Wait for the loading screen to pass
        return False
        
    check_dead_mercenary(dm)
    (_, x, y) = dm.FindPic(96, 84, 964, 600, MONSTER_IMAGES, '050505', 0.8, 0)
    if x <= 0:
        current_time = time.time()
        if current_time - last_monster_seen_time > 5.0:
            no_monster_search_count += 1
            print(f'[Active] Searching for monsters on overworld... ({no_monster_search_count}/5)')
            last_monster_seen_time = current_time
            if no_monster_search_count >= 5:
                print('No monsters found 5 times, pressing ESC to dismiss any popups...')
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

    while time.time() - start_time < 3.5:
        if check_anti_cheat(dm):
            print('Anti-cheat (horse stamp) detected, will exit after current battle finishes')
            anti_cheat_detected = True

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

    time.sleep(0.5)
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
            print('Pressing Esc 4 times to exit')
            for _ in range(4):
                dm.KeyPress(27)
                dm.Delay(30)
                time.sleep(0.1)
            
            # Wait for battle screen to actually end (i.e. is_in_battle returns False)
            print('Waiting for battle screen to close...')
            start_wait = time.time()
            battle_closed = False
            while time.time() - start_wait < 5.0:  # Timeout after 5 seconds
                if not is_in_battle(dm):
                    battle_closed = True
                    break
                time.sleep(0.2)
            if battle_closed:
                print('Battle screen ended')
            else:
                print('Warning: Battle screen did not close within timeout')
            
            check_revive(dm, is_paused)
            check_dead_mercenary(dm)
            break

        for direction, regions in FORMATION_REGIONS.items():
            if action_executed:
                break

            if check_formation(dm, regions[0], regions[1]):
                print(f'Formation position detected: {direction}')
                time.sleep(0.1)

                for monster_dir in MONSTER_CHECKS[direction]:
                    (x1, y1, x2, y2) = MONSTER_DIRECTION_REGIONS[monster_dir]
                    if has_non_black_in_region(dm, x1, y1, x2, y2, monster_dir):
                        print(f'Executing strategy → Formation: {direction} | Monster: {monster_dir}')
                        execute_battle_strategy(dm, direction, monster_dir)
                        time.sleep(12)
                        action_executed = True
                        break

        if not action_executed:
            no_monster_count += 1
            if no_monster_count >= 20:
                print('No monsters found 20 times. Exiting battle by pressing Esc 2 times...')
                dm.KeyPress(27)
                dm.Delay(100)
                dm.KeyPress(27)
                dm.Delay(100)
                time.sleep(2)
                no_monster_count = 0
            else:
                time.sleep(0.25)

        # Check if battle ended
        if not is_in_battle(dm):
            action_executed = True
            print('Battle screen ended')
            if check_revive(dm, is_paused):
                print('Waiting for town to load after reviving main character...')
                time.sleep(5)
            else:
                check_dead_mercenary(dm)
            break
        else:
            time.sleep(0.5)


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

    # Disable automatic GC to avoid stutters during time-sensitive key presses
    gc.disable()
    
    # Perform initial collection
    gc.collect()

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
        dm.Delay(3000)
        dm.KeyPress(13)
        dm.Delay(500)
    
    try:
        loop_counter = 0
        battle_counter = 0
        last_refresh_time = time.time()
        while True:
            if check_stamina(dm):
                break

            if paused:
                gc.collect()  # Collect when paused
                time.sleep(0.5)
                continue

            # Check for Community popup and dismiss it
            if check_community_popup(dm):
                continue

            battle_entered = find_and_engage_monster(dm)
            if battle_entered or is_in_battle(dm):
                handle_battle(dm)
                gc.collect()  # Clean up COM references and memory after battle

                # If anti-cheat was detected, exit now that the battle is over
                # if anti_cheat_detected:
                #     print('Battle finished. Anti-cheat was detected, exiting now...')
                #     for _ in range(10):
                #         play_alert_sound(dm)
                #         time.sleep(0.5)
                #     relogin(dm)
                #     time.sleep(2)
                #     sys.exit(10)

                # Check revive and food after battle
                check_revive(dm, is_paused)
                check_food(dm)

                battle_counter += 1
                print(f'Battles completed: {battle_counter}/25')
                if battle_counter >= 25:
                    print('Reached 25 battles. Restarting application...')
                    time.sleep(0.5)
                    if getattr(sys, 'frozen', None):
                        import subprocess
                        cwd = os.path.dirname(os.path.abspath(sys.executable))
                        subprocess.Popen([sys.executable], cwd=cwd)
                        sys.exit(0)
                    else:
                        system('cls')
                        gc.collect()
                        battle_counter = 0
                        print('Cache cleared, continuing...')
                        time.sleep(5)
                        relogin(dm)
                        time.sleep(15)


            # # Anti-cheat detected outside of battle — exit immediately
            # if anti_cheat_detected and not (battle_entered or is_in_battle(dm)):
            #     print('Anti-cheat detected (not in battle), exiting now...')
            #     for _ in range(10):
            #         play_alert_sound(dm)
            #         time.sleep(0.5)
            #     sys.exit(10)

            loop_counter += 1
            if loop_counter % 50 == 0:
                gc.collect()  # Periodically clean up during overworld exploration

            time.sleep(0.15)
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
def create_login_window():
    run_main_script()


if __name__ == '__main__':
    create_login_window()
