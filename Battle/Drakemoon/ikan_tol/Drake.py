# Drake.py — Main entrypoint and orchestrator (Fish / Ikan Tol)

from Battle.Drakemoon.ikan_tol.combat2 import execute_battle_strategy2
import os
import sys
import time
import winsound
import gc
import keyboard
from tkinter import messagebox

# Ensure local modules (combat.py, config.py, etc.) are found first
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

# Add the project root for shared modules (PyGameAuto, game_actions, etc.)
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

from PyGameAuto.Dm import RegDm
from config import (
    DM_REG_KEY, DM_REG_CODE,
    FORMATION_REGIONS, MONSTER_DIRECTION_REGIONS, MONSTER_CHECKS,
)
from window_manager import move_game_window, bind_game_window
from Battle.Drakemoon.ikan_tol.combat import (
    check_revive, has_non_black_in_region, check_formation,
    execute_battle_strategy,
    initial_call, initiation_battle,
)
from session_scheduler import SessionScheduler, SessionConfig
from game_actions import (
    relogin,
    check_food as base_check_food, check_dead_mercenary as base_check_dead_merc,
    check_anti_cheat, check_stamina as base_check_stamina,
    is_in_battle,
    stop_battle, is_mercenary_dead, ensure_mercenaries_recovered,
)

# ---------------------------------------------------------------------------
# Image pattern strings
# ---------------------------------------------------------------------------
# MONSTER_IMAGES = '|'.join([rf'crab_tomb\crab_tomb{i}.bmp' for i in range(1, 5)])
MONSTER_IMAGES = '|'.join([rf'tarbagan\tarbagan{i}.bmp' for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25]])
DRAKE_IMAGES = '|'.join([rf'Character\drakemoon\drake{i}.bmp' for i in range(1, 12)])

# Concentric monster search regions: search center outward to corners
MONSTER_SEARCH_ZONES = [
    (352, 242, 672, 442),  # Zone 1: Center (immediate proximity to player)
    (222, 162, 802, 522),  # Zone 2: Mid-range
    (0, 0, 1024, 768),     # Zone 3: Full window (corners)
]

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
# Continuous battles threshold before break: 120 to 240 battles
BATTLES_BEFORE_BREAK_MIN = 120
BATTLES_BEFORE_BREAK_MAX = 240

# Battles per batch before relogging
BATTLES_PER_BATCH_RELOG = 50

# Total break duration: 1 to 3 minutes (in seconds)
BREAK_DURATION_MIN_SECONDS = 1 * 60   # 1 minutes (60s)
BREAK_DURATION_MAX_SECONDS = 3 * 60  # 3 minutes (180s)


# ---------------------------------------------------------------------------
# Local Adapters for Shared Routines
# ---------------------------------------------------------------------------
def check_food(dm):
    global paused
    def set_paused():
        global paused
        paused = True
    return base_check_food(dm, relogin_func=relogin, pause_callback=set_paused)


def check_dead_mercenary(dm):
    return ensure_mercenaries_recovered(dm, drake_images=DRAKE_IMAGES)


def check_stamina(dm):
    global paused
    def set_paused():
        global paused
        paused = True
    return base_check_stamina(dm, pause_callback=set_paused)


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
            time.sleep(5)  # Wait for loading screen to pass
            return False

    # Check if any mercenary is dead before searching monsters
    is_dead, dead_slots = is_mercenary_dead(dm, DRAKE_IMAGES)
    if is_dead:
        print(f'[Overworld] ⚠️ Dead mercenary detected ({dead_slots})! Halting monster search to revive first...')
        if not ensure_mercenaries_recovered(dm, DRAKE_IMAGES):
            print('[Overworld] ⛔ Dead mercenary could not be recovered yet! Standing by...')
        return False

    x, y = 0, 0
    for zx1, zy1, zx2, zy2 in MONSTER_SEARCH_ZONES:
        (_, x, y) = dm.FindPic(zx1, zy1, zx2, zy2, MONSTER_IMAGES, '050505', 0.8, 0)
        if x > 0:
            break
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

    # Ensure all mercenaries are alive before chasing/clicking
    is_dead, dead_slots = is_mercenary_dead(dm, DRAKE_IMAGES)
    if is_dead:
        print(f'[Overworld] ⚠️ Monster found, but dead mercenary detected ({dead_slots})! Aborting chase to revive first...')
        ensure_mercenaries_recovered(dm, DRAKE_IMAGES)
        return False

    dm.MoveTo(x, y)
    dm.Delay(150)
    dm.RightClick()
    dm.Delay(300)

    print('Waiting to enter battle screen... (max 3s)')
    start_time = time.time()
    attempt = 1

    while time.time() - start_time < 5:
        check_anti_cheat(dm)

        if is_in_battle(dm):
            print('✅ Successfully entered battle screen')
            return True

        if time.time() - start_time > 2.5 and attempt == 1:
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
            # # 1. Check for monsters around the battle map (nearby) up to 5 times
            # for attempt in range(5):
            #     (_, mx, my) = dm.FindPic(0, 0, 1024, 768, MONSTER_IMAGES, '050505', 0.8, 0)
            #     if mx > 0:
            #         print(f'Monster detected nearby on battle screen at coords: ({mx}, {my}) (attempt {attempt + 1}/15). Exiting battle...')
            #         action_executed = True
            #         break
            #     time.sleep(0.1)

            # 2. If no monster detected around map, proceed with formation checking
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
                        if len(found_monsters) < 2:
                            duration = 7
                        elif len(found_monsters) >= 2:
                            duration = 10
                            break
                        time.sleep(0.25)

                    if found_monsters:
                        print(f'Total monsters found: {len(found_monsters)} -> {found_monsters}')
                        for i, monster_dir in enumerate(found_monsters):
                            print(f'Executing strategy [{i+1}/{len(found_monsters)}] → Formation: {direction} | Monster: {monster_dir}')
                            if i == 0: execute_battle_strategy(dm, direction, monster_dir)
                            if i == 1: execute_battle_strategy2(dm, direction, monster_dir)
                            if i == 2: execute_battle_strategy(dm, direction, monster_dir)

                            if i < len(found_monsters) - 1:
                                print(f'Waiting {i} before next battle...')
                                if i == 0:
                                    time.sleep(2)
                                    dm.KeyPress(49)
                                    dm.Delay(100)
                                    dm.KeyPress(49)
                                    dm.Delay(100)
                                elif i == 1:
                                    time.sleep(duration - 7)
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

    def on_pause_press(event=None):
        global paused
        nonlocal last_toggle_time
        current_time = time.time()
        if current_time - last_toggle_time < 0.3:
            return
        if event.name == 'f10':
            last_toggle_time = current_time
            paused = not paused
            if paused:
                print('All commands paused, press F10 to resume...')
                dm.UnBindWindow()
            else:
                print('All commands resumed...')
                bind_game_window(dm, hwnd)

    keyboard.on_press_key('f10', on_pause_press)

    def on_pagedown_press(event=None):
        nonlocal last_toggle_time
        current_time = time.time()
        if current_time - last_toggle_time < 0.3:
            return
        if event.name == 'page down':
            last_toggle_time = current_time
            print('Page Down pressed: restarting run.bat and closing current terminal...')
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

    keyboard.on_press_key('page down', on_pagedown_press)

    # Disable automatic GC to avoid stutters during time-sensitive key presses
    gc.disable()
    gc.collect()

    try:
        loop_counter = 0
        battle_counter = 0

        def primary_game_step() -> bool:
            """
            Executes one overworld exploration/combat tick.
            Returns True if a battle was fought, False otherwise.
            """
            nonlocal loop_counter, battle_counter

            if check_stamina(dm):
                scheduler.stop()
                return False

            check_anti_cheat(dm)

            # ALWAYS DETECT AND REVIVE FIRST BEFORE EXPLORATION AND BATTLE
            is_dead, target_slots = is_mercenary_dead(dm, DRAKE_IMAGES)
            if is_dead:
                print(f'[Pre-Battle] ⚠️ Dead mercenary detected ({target_slots})! Reviving FIRST before battle...')
                if not ensure_mercenaries_recovered(dm, DRAKE_IMAGES):
                    print('[Pre-Battle] ⛔ Dead mercenary still not recovered! Holding before battle...')
                    time.sleep(2)
                    return False

            battle_entered = find_and_engage_monster(dm)
            if battle_entered or is_in_battle(dm):
                handle_battle(dm)
                gc.collect()  # Clean up COM references and memory after battle

                # Check revive, ensure mercenaries recovered, and check food after battle
                check_revive(dm, is_paused)
                if not ensure_mercenaries_recovered(dm, DRAKE_IMAGES):
                    print('[Maintenance] ⚠️ Mercenaries could not be recovered after battle. Holding before next cycle...')
                    time.sleep(2)
                    return False

                if check_food(dm):
                    return False

                battle_counter += 1
                elapsed_mins = int((time.time() - scheduler.session_start_time) // 60)
                duration_str = (
                    f'{elapsed_mins}m/{int(scheduler._target_duration // 60)}m'
                    if scheduler._target_duration is not None
                    else f'{elapsed_mins}m'
                )
                print(
                    f'Battles completed: {scheduler.current_iteration + 1}/{scheduler._target_iterations} '
                    f'(Grinding session: {duration_str} | Batch: {battle_counter}/{BATTLES_PER_BATCH_RELOG})'
                )

                if battle_counter >= BATTLES_PER_BATCH_RELOG:
                    print(f'Reached {BATTLES_PER_BATCH_RELOG} battles threshold. Relogging...')
                    battle_counter = 0
                    time.sleep(3)
                    relogin(dm)

                return True

            loop_counter += 1
            if loop_counter % 50 == 0:
                gc.collect()  # Periodically clean up during overworld exploration

            return False

        def session_cooldown_handler(reason: str, iterations: int, elapsed_sec: float) -> None:
            """Triggered by SessionScheduler when rest threshold (time/iterations) is reached."""
            nonlocal battle_counter
            print(f'[Break Session] 🛑 Rest break triggered ({reason}). Standing by in place...')
            battle_counter = 0
            gc.collect()

        session_cfg = SessionConfig(
            max_iterations=(BATTLES_BEFORE_BREAK_MIN, BATTLES_BEFORE_BREAK_MAX),
            max_duration_seconds=None,
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
