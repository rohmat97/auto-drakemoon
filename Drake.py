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
    check_revive, has_non_black_in_region, check_formation,
    execute_battle_strategy,
)

# ---------------------------------------------------------------------------
# Image pattern strings (kept here to avoid bloating config with long literals)
# ---------------------------------------------------------------------------
GHOST_IMAGES = '|'.join([f'ghosttur{i}.bmp' for i in range(1, 16)])
# GHOST_IMAGES = '|'.join([f'elder{i}.bmp' for i in range(1, 12)])
DRAKE_IMAGES = '|'.join([
    'drake1.bmp', 'drake2.bmp', 'drake3.bmp', 'drake5.bmp',
    'drake6.bmp', 'drake7.bmp', 'drake8.bmp', 'drake9.bmp',
    'drake10.bmp', 'drake11.bmp', 'drake88.bmp',
])

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
    (_, x, _) = dm.FindPic(0, 0, 108, 499, DRAKE_IMAGES, '050505', 0.8, 0)
    if x > 0:
        print('Dead mercenary detected, consuming half-chicken soup')
        dm.KeyDown(18)
        dm.KeyPress(49)
        dm.KeyPress(49)
        dm.KeyUp(18)


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
        sound_path = os.path.join(dm.getPath(), 'whatsapp.wav')
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
    (_, x, y) = dm.FindPic(96, 84, 964, 524, GHOST_IMAGES, '050505', 0.8, 0)
    if x <= 0:
        if time.time() - last_monster_seen_time > 3.0:
            print('No monsters found for 3 seconds, pressing Esc to close any open dialogs')
            dm.KeyPress(27)
            last_monster_seen_time = time.time()
        return False

    last_monster_seen_time = time.time()
    print(f'Monster found at coords: ({x}, {y})')
    dm.MoveTo(x, y)
    dm.Delay(150)
    dm.RightClick()
    dm.Delay(300)

    check_dead_mercenary(dm)

    print('Waiting to enter battle screen... (max 3s)')
    start_time = time.time()
    attempt = 1

    while time.time() - start_time < 3.5:
        if check_anti_cheat(dm):
            print('Anti-cheat (horse stamp) detected, pausing script')
            play_alert_sound(dm)
            # keyboard.press_and_release('page up')
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

    print('⚠️  Two clicks failed to enter battle, skipping this monster, pressing Esc')
    dm.KeyPress(27)
    time.sleep(2)
    return False


# ---------------------------------------------------------------------------
# Battle phase: detect formation and execute strategy
# ---------------------------------------------------------------------------
def handle_battle(dm):
    """Process a single battle until it ends."""
    print('Entered battle screen')
    action_executed = False

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

                detected_monsters = []
                for monster_dir in MONSTER_CHECKS[direction]:
                    (x1, y1, x2, y2) = MONSTER_DIRECTION_REGIONS[monster_dir]
                    if has_non_black_in_region(dm, x1, y1, x2, y2, monster_dir):
                        detected_monsters.append(monster_dir)

                if detected_monsters:
                    print(f'Monsters detected in directions: {detected_monsters}')
                    for idx, monster_dir in enumerate(detected_monsters):
                        print(f'Executing strategy → Formation: {direction} | Monster: {monster_dir}')
                        execute_battle_strategy(dm, direction, monster_dir)
                        if idx < len(detected_monsters) - 1:
                            time.sleep(2.0)  # Delay between executing strategies

                    # Adjust final sleep time depending on how many directions were hit
                    final_sleep = max(12.0 - (len(detected_monsters) - 1) * 4.0, 4.0)
                    time.sleep(final_sleep)
                    action_executed = True
                    break

        # Check if battle ended
        if not is_in_battle(dm):
            print('Battle screen ended')
            check_revive(dm, is_paused)
            check_dead_mercenary(dm)
            break
        else:
            time.sleep(1.0)


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
                    time.sleep(1)
                    if getattr(sys, 'frozen', None):
                        import subprocess
                        cwd = os.path.dirname(os.path.abspath(sys.executable))
                        subprocess.Popen([sys.executable], cwd=cwd)
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
