# Drake.py — Main entrypoint and orchestrator (Fire Gwi / King Yama)

import gc
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
from Battle.Drakemoon.kingyama.combat import (
    check_revive, has_non_black_in_region, check_formation,
    execute_battle_strategy, initial_call, initiation_battle, send_key,
)
from Battle.Drakemoon.kingyama.combat2 import execute_battle_strategy2
from Battle.Drakemoon.kingyama.combat3 import execute_battle_strategy3
from session_scheduler import SessionScheduler, SessionConfig
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
MONSTER_IMAGES = '|'.join([rf'kingyama\koh{i}.bmp' for i in range(1, 43)])
DRAKE_IMAGES = '|'.join([rf'Character\drakemoon\drake{i}.bmp' for i in range(1, 12)])
EMERGENCY_EXIT_IMAGES = '|'.join([rf'kingyama\emergency_exit{i}.bmp' for i in range(1, 10)] + [r'kingyama\emergency_exit.bmp'])

# Concentric monster search regions: search center outward to corners
MONSTER_SEARCH_ZONES = [
    (352, 242, 672, 442),  # Zone 1: Center (immediate proximity to player)
    (222, 162, 802, 522),  # Zone 2: Mid-range
    (0, 0, 1024, 768),     # Zone 3: Full window (corners)
]

# Grinding Session & Break Guidelines Configuration
BATTLES_BEFORE_BREAK_MIN = 120
BATTLES_BEFORE_BREAK_MAX = 240
BATTLES_PER_BATCH_RELOG = 100
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


def check_food(dm):
    """Check hunger and consume food if needed, pausing if food is exhausted."""
    return base_check_food(dm, relogin_func=relogin, pause_callback=state.pause)


def check_stamina(dm):
    """Check stamina and pause if depleted."""
    return base_check_stamina(dm, pause_callback=state.pause)


def emergency_exit_game_and_terminal(dm):
    """
    Forcefully terminates both the game application window (Gersang) and the terminal.
    Triggered when the emergency target image is detected during monster search or engagement.
    """
    print('\n' + '=' * 65)
    print('🚨 [EMERGENCY EXIT] Danger target detected on screen!')
    print('🚨 Force closing game window and terminal immediately...')
    print('=' * 65 + '\n')

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
    current_time = time.time()

    # Periodic check for main character revive prompt every 5 seconds
    if current_time - state.last_revive_check > 5.0:
        state.last_revive_check = current_time
        if check_revive(dm, state.is_paused):
            print('[Overworld] Main character revival sequence completed. Ready for exploration.')
            return False

    # Check for danger target before searching
    check_emergency_exit_target(dm)

    # Check if any mercenary is dead before searching monsters
    is_dead, dead_slots = is_mercenary_dead(dm, DRAKE_IMAGES)
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
        return False

    state.no_monster_search_count = 0
    state.last_monster_seen_time = time.time()
    print(f'Monster found at coords: ({x}, {y})')

    # Check for danger target before engaging
    check_emergency_exit_target(dm)

    # Ensure all mercenaries are alive before moving/clicking
    is_dead, dead_slots = is_mercenary_dead(dm, DRAKE_IMAGES)
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

    while time.time() - start_time < 3:
        check_anti_cheat(dm, immediate_wait=False)
        check_emergency_exit_target(dm)

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
def handle_battle(dm) -> None:
    """Process a single battle until it ends."""
    print('Entered battle screen')
    action_executed = False
    no_monster_count = 0

    while True:
        if state.is_paused():
            time.sleep(1)
            continue

        if action_executed:
            print('Waiting for battle screen to close...')
            stop_battle(dm, max_wait_sec=15)
            print('Battle screen ended')
            break

        # 1. Check for monsters around the battle map (nearby) up to 5 times
        for attempt in range(5):
            (_, mx, my) = dm.FindPic(0, 0, 1024, 768, MONSTER_IMAGES, '050505', 0.8, 0)
            if mx > 0:
                print(f'Monster detected nearby on battle screen at coords: ({mx}, {my}) (attempt {attempt + 1}/5). Exiting battle...')
                action_executed = True
                break
            time.sleep(0.1)

        if action_executed:
            continue

        # 2. If no monster detected around map, proceed with formation checking
        for direction, regions in FORMATION_REGIONS.items():
            if action_executed:
                break

            if check_formation(dm, regions[0], regions[1]):
                print(f'Formation position detected: {direction}')
                time.sleep(0.1)
                dm.MoveTo(640, 425)
                dm.Delay(25)

                key_code = DIRECTION_KEYS.get(direction)
                if key_code is not None:
                    dm.KeyDown(key_code)
                    dm.Delay(400)
                    dm.KeyUp(key_code)

                dm.Delay(25)
                initial_call(dm)
                dm.Delay(25)
                initiation_battle(dm)
                dm.Delay(25)
                select_unit_1(dm, delay_ms=25)

                found_monsters = []
                duration = 0
                print(f'Scanning {direction} formation for monsters...')
                for _ in range(10):
                    for monster_dir in MONSTER_CHECKS.get(direction, []):
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
                        if i == 0:
                            execute_battle_strategy(dm, direction, monster_dir)
                        elif i == 1:
                            execute_battle_strategy2(dm, direction, monster_dir)
                        elif i == 2:
                            execute_battle_strategy3(dm, direction, monster_dir)

                        if i < len(found_monsters) - 1:
                            print(f'Waiting {i} before next battle...')
                            if i == 0:
                                select_unit_1(dm, delay_ms=100)
                            elif i == 1:
                                wait_time = max(0, duration - 5)
                                if wait_time > 0:
                                    time.sleep(wait_time)
                                select_unit_1(dm, delay_ms=100)
                            else:
                                time.sleep(duration)
                                select_unit_1(dm, delay_ms=100)
                        else:
                            time.sleep(duration)

                    action_executed = True
                    break

        if not action_executed:
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
        if event.name and event.name.lower() == 'delete':
            last_toggle_time = current_time
            is_now_paused = state.toggle_pause()
            if is_now_paused:
                print('All commands paused, press Delete to resume...')
                dm.UnBindWindow()
            else:
                print('All commands resumed...')
                bind_game_window(dm, hwnd)

    def on_restart_press(event=None):
        nonlocal last_toggle_time
        current_time = time.time()
        if current_time - last_toggle_time < 0.3:
            return
        if event.name and event.name.lower() == 'page up':
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
                print(f'Error starting run.bat: {e}')
            try:
                os.kill(os.getppid(), 9)
            except Exception as e:
                print(f'Error killing parent terminal: {e}')
            sys.exit(0)

    keyboard.on_press_key('delete', on_pause_press)
    keyboard.on_press_key('page up', on_restart_press)


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

    setup_hotkeys(dm, hwnd)

    # Disable automatic GC to avoid micro-stutters during time-sensitive combat
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

            if check_anti_cheat(dm):
                return False

            # Pre-battle check: ensure all mercenaries are alive before searching monsters
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

                # Check if anti-cheat flagged a relog after finishing battle
                if check_pending_anti_cheat_relog(dm):
                    battle_counter = 0
                    return True

                # Post-battle maintenance: revives and food
                check_revive(dm, state.is_paused)
                if not ensure_mercenaries_recovered(dm, DRAKE_IMAGES):
                    print('[Maintenance] ⚠️ Mercenaries could not be recovered after battle. Holding before next cycle...')
                    time.sleep(2)
                    return False

                if check_food(dm):
                    return False

                battle_counter += 1
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
                    f'(Grinding session: {duration_str} | Batch: {battle_counter}/{BATTLES_PER_BATCH_RELOG})'
                )

                # if battle_counter >= BATTLES_PER_BATCH_RELOG:
                #     print(f'Reached {BATTLES_PER_BATCH_RELOG} battles threshold. Relogging...')
                #     battle_counter = 0
                #     time.sleep(3)
                #     relogin(dm)
                # else:
                print('Waiting 5s after battle before continuing to next battle...')
                time.sleep(5)

                return True

            loop_counter += 1
            if loop_counter % 50 == 0:
                gc.collect()  # Periodically clean up during exploration

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
            pause_check=state.is_paused,
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
