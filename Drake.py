# Drake.py — Main entrypoint and orchestrator

import os
import sys
import time
import keyboard
import winsound
import gc
from tkinter import messagebox

from PyGameAuto.Dm import RegDm
from config import (
    DM_REG_KEY, DM_REG_CODE,
    FORMATION_REGIONS, MONSTER_DIRECTION_REGIONS, MONSTER_CHECKS,
)
from window_manager import move_game_window, bind_game_window
from combat import (
    check_revive, check_formation, execute_skill_loop, 
    strategy_east_south, strategy_south_north, strategy_west_north, strategy_north_west,
    get_monster_direction, execute_battle_strategy
)

# ---------------------------------------------------------------------------
# Image pattern strings (kept here to avoid bloating config with long literals)
# ---------------------------------------------------------------------------
# MONSTER_IMAGES = '|'.join([rf'ancient_heo\a{i}.bmp' for i in range(1, 26)])
MONSTER_IMAGES = '|'.join([rf'ancient_byeok\a{i}.bmp' for i in range(1, 26)])
DRAKE_IMAGES = '|'.join([rf'drake\drake{i}.bmp' for i in range(2, 13)])

# ---------------------------------------------------------------------------
# Pause state  (shared via closure / global)
# ---------------------------------------------------------------------------
paused = False
last_monster_seen_time = time.time()


def is_paused():
    return paused


# ---------------------------------------------------------------------------
# Overworld helpers
# ---------------------------------------------------------------------------
def check_food(dm):
    """Check hunger level and consume food if needed.
    Returns True if script should pause (food exhausted)."""
    (_, x_food, _) = dm.FindPic(52, 649, 246, 684, 'food.bmp', '050505', 0.8, 0)
    (_, x_bread, _) = dm.FindPic(43, 644, 101, 692, 'bread.bmp', '050505', 0.8, 0)

    if x_food > 0:
        # Satiety is sufficient, no print to avoid console spam
        pass
    elif x_bread > 0:
        print('Replenishing satiety')
        dm.KeyDown(18)
        dm.KeyPress(50)
        dm.KeyUp(18)

    (_, x_empty, _) = dm.FindPic(582, 418, 617, 446, 'emptyfooddrake.bmp', '050505', 0.8, 0)
    if x_empty > 0:
        print('Satiety depleted, script paused')
        return True
    return False



def check_dead_mercenary(dm):
    """If a dead mercenary is detected, consume half-chicken soup."""
    (_, x, _) = dm.FindPic(0, 0, 110, 650, DRAKE_IMAGES, '050505', 0.8, 0)
    if x > 0:
        print('Dead mercenary detected, opening inventory to revive...')
        # Check if inventory is already open
        (_, bx, _) = dm.FindPic(0, 0, 1024, 768, 'bag.bmp', '050505', 0.8, 0)
        if bx <= 0:
            print('Inventory not open, pressing "i" to open...')
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
        
        # Press 'i' again to close inventory if it is detected open
        (_, bx_end, _) = dm.FindPic(0, 0, 1024, 768, 'bag.bmp', '050505', 0.8, 0)
        if bx_end > 0:
            print('Inventory still open, pressing "i" to close...')
            dm.KeyPress(73)
            dm.Delay(500)


def check_anti_cheat(dm):
    """Returns True if the anti-cheat horse-stamp is detected."""
    (_, x_horse, _) = dm.FindPic(599, 21, 650, 49, 'horse.bmp', '050505', 0.8, 0)
    (_, x_bread, _) = dm.FindPic(50, 650, 93, 689, 'bread.bmp', '050505', 0.8, 0)
    if x_horse <= 0 and x_bread > 0:
        return True
    return False


def play_alert_sound(dm):
    """Play an alert sound when anti-cheat is triggered."""
    try:
        sound_path = os.path.join(dm.GetBasePath(), 'whatsapp.wav')
        if os.path.exists(sound_path):
            winsound.PlaySound(sound_path, winsound.SND_FILENAME)
    except Exception:
        pass


def is_in_battle(dm):
    (_, x, _) = dm.FindPic(959, 666, 1016, 747, 'battle.bmp', '050505', 0.8, 0)
    return x > 0


# ---------------------------------------------------------------------------
# Overworld: find and engage a monster
# ---------------------------------------------------------------------------
def find_and_engage_monster(dm):
    global last_monster_seen_time
    """Search for a monster on the overworld and attempt to enter battle.
    Returns True if battle was entered, False otherwise."""
    if check_revive(dm, is_paused):
        return False
    (_, x, y) = dm.FindPic(96, 84, 964, 600, MONSTER_IMAGES, '050505', 0.8, 0)
    
    check_dead_mercenary(dm)
    time.sleep(0.1)

    if x <= 0:
        print('No monster found. Returning to overworld.')
        return False

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
            print('Anti-cheat (horse stamp) detected, pausing script')
            play_alert_sound(dm)
            dm.Delay(300)   
            time.sleep(5)
            return False

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
from combat import get_minimap_positions, map_vector_to_direction

def wait_for_minimap_to_load(dm):
    """Wait for the minimap dots to fade in."""
    import time
    
    print('   [Minimap] Waiting for minimap dots to load...')
    for attempt in range(25): # Wait up to 5 seconds
        px, py, mx, my = get_minimap_positions(dm)
        if px is not None and py is not None:
            debug_path = os.path.join(dm.GetBasePath(), 'debug_minimap.bmp')
            dm.Capture(0, 675, 259, 767, debug_path)
            return True
        time.sleep(0.2)
        
    print('   [Minimap] Failed to find minimap dots after 5 seconds.')
    
    # Save debug screenshot of failure
    debug_path = os.path.join(dm.GetBasePath(), 'debug_minimap.bmp')
    dm.Capture(0, 675, 259, 767, debug_path)
    
    return False

def handle_battle(dm):
    """Process a single battle until it ends."""
    print('Entered battle screen')
    
    # Debug: capture full screen and minimap during battle
    time.sleep(0.5)  # Wait for battle to fully render
    resource_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Resource')
    dm.Capture(0, 0, 1023, 767, os.path.join(resource_dir, 'debug_fullscreen.bmp'))
    dm.Capture(0, 675, 259, 767, os.path.join(resource_dir, 'debug_minimap.bmp'))
    print(f'   [DEBUG] Screenshots saved to Resource/debug_fullscreen.bmp and debug_minimap.bmp')

    action_executed = False
    no_monster_checks_count = 0
    detected_formation = None

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

        if not detected_formation:
            wait_for_minimap_to_load(dm)
            
            # Use reliable corner screen detection
            if check_formation(dm, FORMATION_REGIONS['East'][0], FORMATION_REGIONS['East'][1]):
                detected_formation = 'East'
            elif check_formation(dm, FORMATION_REGIONS['South'][0], FORMATION_REGIONS['South'][1]):
                detected_formation = 'South'
            elif check_formation(dm, FORMATION_REGIONS['West'][0], FORMATION_REGIONS['West'][1]):
                detected_formation = 'West'
            elif check_formation(dm, FORMATION_REGIONS['North'][0], FORMATION_REGIONS['North'][1]):
                detected_formation = 'North'
            else:
                detected_formation = 'East'
            print(f'Formation position detected via Screen Corners: {detected_formation}')

        if detected_formation:
            monster_found = False
            monster_dir = get_monster_direction(dm, detected_formation)
            if monster_dir:
                monster_found = True
                print(f'Executing strategy → Formation: {detected_formation} | Monster: {monster_dir}')
                execute_battle_strategy(dm, detected_formation, monster_dir)
                time.sleep(12)
                action_executed = True

            if not monster_found:
                no_monster_checks_count += 1
                print(f'Checked all sides for {detected_formation} formation, found no monsters. Attempt {no_monster_checks_count}/8')
                if no_monster_checks_count >= 8:
                    print('No monsters found in 8 consecutive checks. Exiting battle by pressing Esc 4 times...')
                    for _ in range(4):
                        dm.KeyPress(27)
                        dm.Delay(100)
                    
                    print('Waiting for battle screen to close...')
                    start_wait = time.time()
                    battle_closed = False
                    while time.time() - start_wait < 5.0:
                        if not is_in_battle(dm):
                            battle_closed = True
                            break
                        time.sleep(0.2)
                    
                    check_revive(dm, is_paused)
                    check_dead_mercenary(dm)
                    return
            else:
                no_monster_checks_count = 0

        # Check if battle ended
        if not is_in_battle(dm):
            action_executed = True
            print('Battle screen ended')
            check_revive(dm, is_paused)
            check_dead_mercenary(dm)
            no_monster_checks_count = 0
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
        basedir = os.path.dirname(__file__)
    dm.setPath(os.path.join(basedir, 'Resource'))

    paused = False

    def on_page_up_press(event=None):
        global paused
        if event.name == 'page up':
            paused = not paused
            if paused:
                print('All commands paused, press Page Up to resume...')
                dm.UnBindWindow()
            else:
                print('All commands resumed...')
                bind_game_window(dm, hwnd)

    keyboard.on_press_key('page up', on_page_up_press)

    # Disable automatic GC to avoid stutters during time-sensitive key presses
    gc.disable()
    
    # Perform initial collection
    gc.collect()

    try:
        loop_counter = 0
        battle_counter = 0
        last_refresh_time = time.time()
        while True:
            if paused:
                gc.collect()  # Collect when paused
                time.sleep(0.5)
                continue
            time.sleep(0.1)
            check_dead_mercenary(dm)
            battle_entered = find_and_engage_monster(dm)
            if battle_entered or is_in_battle(dm):
                handle_battle(dm)
                gc.collect()  # Clean up COM references and memory after battle

                # Check revive and food after battle
                check_revive(dm, is_paused)
                if check_food(dm):
                    paused = True
                    print('All commands paused, press Page Up to resume...')
                    dm.UnBindWindow()
                    continue

                battle_counter += 1
                print(f'Battles completed: {battle_counter}/5')
                if battle_counter >= 5:
                    print('Reached 5 battles. Restarting application...')
                    dm.UnBindWindow()
                    time.sleep(0.5)
                    if getattr(sys, 'frozen', None):
                        import subprocess
                        cwd = os.path.dirname(os.path.abspath(sys.executable))
                        subprocess.Popen([sys.executable], cwd=cwd, creationflags=0x00000010)
                        sys.exit(0)
                    else:
                        sys.exit(5)  # Exit code 5 signals run.bat to restart

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
