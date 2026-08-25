# Drake.py — Main entrypoint and orchestrator (Fire Gwi)

from Battle.Drakemoon.dark_gujimo.combat import initiation_battle
from Battle.Drakemoon.fire_gwi.combat2 import execute_battle_strategy2
from Battle.Drakemoon.fire_gwi.combat3 import execute_battle_strategy3
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
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

from PyGameAuto.Dm import RegDm
from config import (
    DM_REG_KEY, DM_REG_CODE,
    FORMATION_REGIONS, MONSTER_DIRECTION_REGIONS, MONSTER_CHECKS,
)
from window_manager import move_game_window, bind_game_window
from Battle.Drakemoon.bot_tengu.combat import (
    check_revive, has_non_black_in_region, check_formation,
    execute_battle_strategy, initial_call,
)

# ---------------------------------------------------------------------------
# Image pattern strings (kept here to avoid bloating config with long literals)
# ---------------------------------------------------------------------------
MONSTER_IMAGES = '|'.join(
    [rf'blackbear/blackbear{i}.bmp' for i in range(1, 26)]
)
DRAKE_IMAGES = '|'.join([rf'Character\nytheris\nytheris{i}.bmp' for i in range(1, 12)])

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


def check_food(dm):
    """Check hunger level and consume food if needed.
    Returns True if script should pause (food exhausted)."""
    global paused
    print('[Post-Battle] Checking hunger & consuming food (Alt+1, Alt+2)...')
    if not hasattr(check_food, "eat_count"):
        check_food.eat_count = 0
        
    check_food.eat_count += 1
    # press alt+1 every finish battle
    # dm.KeyDown(18)
    # dm.Delay(200)
    # dm.KeyPress(49)
    # dm.Delay(200)
    # dm.KeyUp(18)
    # dm.Delay(200)
    # press alt+2 every times battle
    if (check_food.eat_count % 1 == 0):
        dm.KeyDown(18)
        dm.Delay(200)
        dm.KeyPress(50)
        dm.Delay(200)
        dm.KeyUp(18)
    dm.Delay(200)

    (_, x_bread, y_bread) = dm.FindPic(43, 644, 101, 692, 'bread.bmp', '050505', 0.8, 0)
    if x_bread > 0:
        print('Replenishing satiety')
        print('Replenished satiety 500 times, pausing script... ' + str(check_food.eat_count) + '/500')
        if check_food.eat_count >= 800:
            relogin(dm)
            check_food.eat_count = 0
            paused = True
            print('All commands paused, press page down to resume...')
            dm.UnBindWindow()
            return True

    (_, x_empty, y_empty) = dm.FindPic(450, 350, 680, 480, 'emptyfoodinter.bmp', '050505', 0.8, 0)
    if x_empty > 0:
        print('Satiety depleted, script paused')
        check_food.eat_count = 0
        paused = True
        print('All commands paused, press page down to resume...')
        dm.UnBindWindow()
        return True
    return False


def check_dead_mercenary(dm):
    """If a dead mercenary is detected, open inventory and use revival item.
    Returns True if a dead mercenary was detected and revival performed, False otherwise."""
    print('[Team Status] Checking mercenary status...')
    (_, x, _) = dm.FindPic(0, 0, 120, 700, DRAKE_IMAGES, '050505', 0.8, 0)
    if x > 0:
        print(f'Dead mercenary detected (found icon at x={x}), opening inventory to revive...')
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
            dm.Delay(150)  # Delay to allow inventory UI to load
            dm.MoveTo(600, 150)
            dm.Delay(150)
            dm.RightClick()
            dm.Delay(150)
        
        # Press 'i' again to close inventory
        dm.KeyPress(73)
        dm.Delay(500)
        return True
    else:
        print('[Team Status] All mercenaries are alive.')
        return False


def ensure_team_alive(dm, max_retries=3):
    """
    Ensures that main character and all mercenaries are 100% alive before searching/engaging monsters.
    Returns True only when the entire team is confirmed alive.
    Returns False if any member is dead / reviving.
    """
    # 1. Main character revive check
    if check_revive(dm, is_paused):
        print('[Team Status] Main character revived, waiting for town/screen to load...')
        time.sleep(5.0)
        return False

    # 2. Mercenaries revive check with retry verification
    for attempt in range(max_retries):
        (_, x, _) = dm.FindPic(0, 0, 120, 700, DRAKE_IMAGES, '050505', 0.8, 0)
        if x > 0:
            print(f'[Team Status] Dead mercenary detected (attempt {attempt + 1}/{max_retries}), reviving now...')
            check_dead_mercenary(dm)
            time.sleep(1.0)  # Wait for UI to update
        else:
            return True

    # Final check after retries
    (_, x_final, _) = dm.FindPic(0, 0, 120, 700, DRAKE_IMAGES, '050505', 0.8, 0)
    if x_final > 0:
        print('[Team Status] ⚠️ Warning: Dead mercenary still detected! Halting monster engagement until team is alive.')
        return False

    return True


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


def is_in_battle(dm):
    (_, x, _) = dm.FindPic(959, 666, 1016, 747, 'battle3.bmp', '050505', 0.8, 0)
    return x > 0


# ---------------------------------------------------------------------------
# Overworld: find and engage a monster
# ---------------------------------------------------------------------------
def find_and_engage_monster(dm):
    global last_monster_seen_time, anti_cheat_detected, no_monster_search_count
    """Search for a monster on the overworld and attempt to enter battle.
    Returns True if battle was entered, False otherwise."""
    
    # Strictly ensure all team members are alive before searching for or clicking any monsters
    if not ensure_team_alive(dm):
        return False

    (_, x, y) = dm.FindPic(96, 84, 964, 600, MONSTER_IMAGES, '050505', 0.8, 0)
    if x <= 0:
        current_time_check = time.time()
        if current_time_check - last_monster_seen_time > 3.5:
            no_monster_search_count += 1
            print(f'[Active] Searching for monsters on overworld... ({no_monster_search_count}/5)')
            last_monster_seen_time = current_time_check
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

    print('Waiting to enter battle screen... (max 4s)')
    start_time = time.time()
    attempt = 1

    while time.time() - start_time < 2.0:
        # if check_anti_cheat(dm):
        #     print('Anti-cheat (horse stamp) detected, will exit after current battle finishes')
        #     anti_cheat_detected = True

        if is_in_battle(dm):
            print('✅ Successfully entered battle screen')
            return True

        if time.time() - start_time > 1.2 and attempt == 1:
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
            # Wait/Press Esc until battle screen actually ends
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
                    action_executed = True
                    break

        # Check if battle ended
        if not is_in_battle(dm):
            action_executed = True
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

    def on_pagedown_press(event=None):
        global paused
        nonlocal last_toggle_time
        current_time = time.time()
        if current_time - last_toggle_time < 0.3:
            return
        if event.name == 'page down':
            last_toggle_time = current_time
            paused = not paused
            if paused:
                print('All commands paused, press page down to resume...')
                dm.UnBindWindow()
            else:
                print('All commands resumed...')
                bind_game_window(dm, hwnd)

    keyboard.on_press_key('page down', on_pagedown_press)



    # Disable automatic GC to avoid stutters during time-sensitive key presses
    gc.disable()
    
    # Perform initial collection
    gc.collect()


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

            # If anti-cheat was detected, exit now that the battle is over
            if anti_cheat_detected:
                print('Battle finished. Anti-cheat was detected, exiting now...')
                for _ in range(10):
                    play_alert_sound(dm)
                    time.sleep(0.5)
                # dm.UnBindWindow()
                time.sleep(2)

            battle_entered = find_and_engage_monster(dm)
            if battle_entered or is_in_battle(dm):
                print('Entering battle...')
                handle_battle(dm)
                gc.collect()  # Clean up COM references and memory after battle

       
                # -----------------------------------------------------------------
                # Mandatory Post-Battle Sequence:
                # 1. Wait for overworld UI to load fully
                # 2. Check & ensure all team members are alive (main + mercenaries)
                # 3. Check hunger & consume food (Alt+1, Alt+2)
                # Monsters will NOT be searched or clicked until this is verified.
                # -----------------------------------------------------------------
                print('==================================================')
                print('[Post-Battle] Waiting 2.5s for overworld screen to load...')
                time.sleep(2.5)

                print('[Post-Battle 1/2] Ensuring all team members are alive...')
                team_ready = ensure_team_alive(dm)
                while not team_ready and not paused:
                    print('[Post-Battle] Team not fully revived yet, retrying check in 2.0s...')
                    time.sleep(2.0)
                    team_ready = ensure_team_alive(dm)

                print('[Post-Battle 2/2] Checking food & replenishing satiety...')
                check_food(dm)
                time.sleep(0.5)

                print('[Post-Battle] ✅ All team members ALIVE & ready. Resuming monster hunting...')
                print('==================================================')

                battle_counter += 1
                print(f'Battles completed: {battle_counter}/25')
                if battle_counter >= 25:
                    print('Reached 25 battles. Relogging character...')
                    system('cls')
                    gc.collect()
                    battle_counter = 0
                    print('Performing relogin...')
                    time.sleep(2)
                    relogin(dm)
                    time.sleep(10)

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
