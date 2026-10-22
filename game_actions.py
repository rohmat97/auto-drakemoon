# game_actions.py — Centralized shared game actions for Drake bots
# Includes: Anti-cheat, Captcha solving, Stamina, Inventory/Item routines,
#           Food & Mercenary revival, Town break & Portal travel routines.

import os
import sys
import time
import random
import winsound
from tkinter import messagebox
from collections import Counter

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

    dm.KeyPress(27)  # Esc
    dm.Delay(200)
    dm.KeyPress(27)  # Esc
    dm.Delay(200)

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
    2. Waits 2 seconds for dialog rendering to stabilize.
    3. Captures and verifies the captcha 2-3 times across frames,
       computing majority consensus across samples for maximum accuracy.
    4. Clears input field and types verified 5-character code.
    5. Confirms before clicking OK, clicks OK button, and verifies dismissal.
    """
    print(f'[Captcha Handler] 2nd Captcha dialog located at ({x_captcha}, {y_captcha}).')
    # 1. Move cursor away from dialog
    dm.MoveTo(0, 0)

    # 2. Wait for 2 seconds
    print('[Captcha Handler] Waiting 2 seconds before solving...')
    time.sleep(2.0)

    # 3. Capture captcha rectangle focused on the inner captcha card
    # Inner captcha card containing all characters is located at (368, 274, 657, 380)
    x1, y1, x2, y2 = 368, 274, 657, 380
    captcha_save_path = os.path.join(dm.getPath(), 'temp_captcha.bmp')

    char_cleanup = {
        '了': 'J',
        '亅': 'J',
        '父': 'J',
        '工': 'I',
        '上': 'I',
        '口': 'O',
        '日': 'B',
        '一': '1',
        '丁': 'T',
        '下': 'T',
        '乙': 'Z',
        '匚': 'C',
        '乂': 'X',
        '&': '8',
        '只': '8',
        '七': '7',
    }

    # Verify 2-3 times across frames for maximum accuracy
    print('[Captcha Handler] Sampling and verifying captcha 3 times across frames...')
    samples = []
    for sample_round in range(2):
        dm.Capture(x1, y1, x2, y2, captcha_save_path)
        dm.Delay(100)
        sample_code = solve_captcha(captcha_save_path, debug=False)
        if sample_code:
            for k, v in char_cleanup.items():
                sample_code = sample_code.replace(k, v)
            sample_code = ''.join([c.upper() for c in sample_code if c.isascii() and c.isalnum()])
            if len(sample_code) == 5:
                samples.append(sample_code)
                print(f'[Captcha Handler] Frame sample {sample_round + 1}/2: "{sample_code}"')
            else:
                print(f'[Captcha Handler] Frame sample {sample_round + 1}/2 (non-5 chars): "{sample_code}"')
        time.sleep(0.2)

    # Positional voting consensus across the 2-3 samples
    if samples:
        consensus_chars = []
        for pos in range(5):
            pos_counter = Counter([s[pos] for s in samples])
            consensus_chars.append(pos_counter.most_common(1)[0][0])
        code = ''.join(consensus_chars)
        print(f'[Captcha Handler] Confirmed consensus from {len(samples)} sample(s): "{code}"')
    else:
        # Fallback to single detailed solve if no 5-character sample was captured
        print('[Captcha Handler] Multi-frame samples incomplete. Performing fallback detailed solve...')
        dm.Capture(x1, y1, x2, y2, captcha_save_path)
        dm.Delay(100)
        code = solve_captcha(captcha_save_path, debug=True)
        if code:
            for k, v in char_cleanup.items():
                code = code.replace(k, v)
            code = ''.join([c.upper() for c in code if c.isascii() and c.isalnum()])
        print(f'[Captcha Handler] Fallback solved code: "{code}"')

    # 4. Clear input box and type verified characters
    if code:
        # Focus input and clear any residual/dirty text
        for _ in range(8):
            dm.KeyPress(8)  # Backspace
            dm.Delay(35)
        dm.Delay(100)

        for char in code:
            dm.KeyPressChar(char)
            dm.Delay(80)
        dm.Delay(200)
        dm.KeyPress(13)  # Enter key
    else:
        print('[Captcha Handler] Warning: No code recognized.')

    dm.Delay(300)

    # 5. Click OK button with 2-3 validation checks
    (_, ok_x, ok_y) = dm.FindPic(350, 450, 550, 530, r'anti_cheat\ok.bmp', '101010', 0.75, 0)
    if ok_x >= 0:
        click_x = ok_x + 21
        click_y = ok_y + 7
        print(f'[Captcha Handler] OK button matched at ({ok_x}, {ok_y}), moving to center ({click_x}, {click_y})')
    else:
        click_x = 446
        click_y = 482
        print(f'[Captcha Handler] Moving cursor directly to default OK button at ({click_x}, {click_y})')

    dm.MoveTo(click_x, click_y)
    dm.Delay(150)
    for _ in range(4):
        dm.LeftClick()
        dm.Delay(100)
    dm.Delay(600)

    # Verify if dialog has been dismissed or needs re-click confirmation (up to 2 extra rounds)
    for confirm_round in range(2):
        (_, still_ok_x, still_ok_y) = dm.FindPic(350, 450, 550, 530, r'anti_cheat\ok.bmp', '101010', 0.75, 0)
        if still_ok_x >= 0:
            print(f'[Captcha Handler] OK button still visible (confirm attempt {confirm_round + 2}/3). Re-clicking...')
            dm.MoveTo(click_x, click_y)
            dm.Delay(100)
            dm.LeftClick()
            dm.Delay(600)
        else:
            print('[Captcha Handler] Captcha dialog confirmed dismissed.')
            break

    print(f'[Captcha Handler] OK button confirmed and clicked successfully.')
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


def wait_anti_cheat_cooldown(dm, min_seconds=60, max_seconds=180, reason="Horse stamp missing"):
    """
    Waits or stays in place for 1 to 3 minutes (60-180 seconds) instead of relogging.
    Allows time for anti-cheat check to clear before continuing hunting.
    """
    wait_time = random.randint(min_seconds, max_seconds)
    mins = wait_time // 60
    secs = wait_time % 60
    print(f'[Anti-Cheat] 🛑 {reason}: Staying in place for {wait_time}s ({mins}m {secs}s) instead of relogging...')
    play_alert_sound(dm)

    start_wait = time.time()
    while time.time() - start_wait < wait_time:
        remaining = int(wait_time - (time.time() - start_wait))
        if remaining > 0 and remaining % 30 == 0:
            print(f'[Anti-Cheat] ⏳ Standing by in place: {remaining}s remaining ({remaining // 60}m {remaining % 60}s)...')
        time.sleep(1)

    print('[Anti-Cheat] ✅ Wait period complete! Continuing hunting again.\n')


def check_pending_anti_cheat_relog(dm, relogin_func=None):
    """
    Checks if a post-battle relog was flagged by anti-cheat (missing horse stamp).
    Waits until confirmed outside of battle, then executes relogin.
    Returns True if relog was performed, False otherwise.
    """
    global _anti_cheat_pending_relog, _last_anti_cheat_sound_time, _anti_cheat_relogin_func
    if _anti_cheat_pending_relog:
        # Crucial safeguard: Make sure we don't execute during battle!
        if is_in_battle(dm):
            print('[Anti-Cheat] ⚠️ Battle still active! Waiting for battle to fully end before relog...')
            stop_battle(dm, max_wait_sec=15)
            time.sleep(1)

        # If STILL in battle, strictly do not execute relog during battle
        if is_in_battle(dm):
            print('[Anti-Cheat] ⛔ Cannot relog: battle screen is still active. Postponing relog.')
            return False

        print('[Anti-Cheat] 🎯 1 battle completed under anti-cheat condition. Executing relogin now...')
        _anti_cheat_pending_relog = False
        _last_anti_cheat_sound_time = 0
        time.sleep(2)
        fn_relogin = relogin_func or _anti_cheat_relogin_func or relogin
        fn_relogin(dm)
        time.sleep(3)
        return True
    return False


def check_anti_cheat(dm, relogin_func=None, immediate_wait=False):
    """
    Checks for anti-cheat indicators:
    1. 2nd captcha dialog popup:
       Solves captcha automatically.
    2. Anti-cheat indicator image detected:
       Flags pending relog to fight 1 more battle. Never relogs immediately,
       and never executes during battle.
       
    Returns True ONLY if a blocking action occurred (e.g. 2nd captcha solved).
    Returns False when flagging anti-cheat so exploration and 1 more battle can proceed.
    """
    global _anti_cheat_pending_relog, _last_anti_cheat_sound_time, _anti_cheat_relogin_func
    if relogin_func:
        _anti_cheat_relogin_func = relogin_func

    # 1. Check 2nd captcha popup box (Priority: modal blocking dialog)
    # Search for detect_captcha banner in dialog header region
    (_, x_captcha, y_captcha) = dm.FindPic(300, 150, 750, 350, r'anti_cheat\detect_captcha.bmp', '101010', 0.8, 0)
    if x_captcha < 0:
        # Fullscreen search for detect_captcha banner
        (_, x_captcha, y_captcha) = dm.FindPic(0, 0, 1024, 768, r'anti_cheat\detect_captcha.bmp', '101010', 0.8, 0)
    if x_captcha < 0:
        # Check for OK button in captcha dialog button region (350, 450, 550, 530)
        (_, x_ok, y_ok) = dm.FindPic(350, 450, 550, 530, r'anti_cheat\ok.bmp', '101010', 0.75, 0)
        if x_ok >= 0:
            x_captcha, y_captcha = x_ok, y_ok
    if x_captcha < 0:
        # Fallback check for renewal asset in dialog region or fullscreen
        (_, x_captcha, y_captcha) = dm.FindPic(350, 415, 600, 560, r'anti_cheat\renewal.bmp', '101010', 0.7, 0)
    if x_captcha < 0:
        (_, x_captcha, y_captcha) = dm.FindPic(0, 0, 1024, 768, r'anti_cheat\renewal.bmp', '101010', 0.7, 0)

    if x_captcha >= 0:
        print(f'[Anti-Cheat] 🚨 2nd Captcha dialog detected (asset matched at ({x_captcha}, {y_captcha}))!')
        print('[Anti-Cheat] Playing alert sound and solving 2nd captcha automatically...')
        play_alert_sound(dm)
        handle_captcha(dm, x_captcha, y_captcha)
        return True

    # 2. Check anti-cheat banner indicator (Non-blocking: fights 1 more battle then relogs)
    (_, x_ac, y_ac) = dm.FindPic(0, 0, 1024, 768, r'anti_cheat\anti_cheat.bmp|anti_cheat\anti_cheat_roof.bmp', '101010', 0.75, 0)
    if x_ac >= 0:
        now = time.time()
        if not _anti_cheat_pending_relog:
            _anti_cheat_pending_relog = True
            _last_anti_cheat_sound_time = now
            print(f'[Anti-Cheat] 🚨 Anti-cheat detected at ({x_ac}, {y_ac})!')
            print('[Anti-Cheat] 🔔 Alert sound triggered. Will fight 1 more battle before relogging (will not relog during battle).')
            play_alert_sound(dm)
        elif now - _last_anti_cheat_sound_time > 15.0:
            _last_anti_cheat_sound_time = now
            print(f'[Anti-Cheat] 🚨 Anti-cheat flagged at ({x_ac}, {y_ac}). Waiting for 1 battle to finish before relog...')
            play_alert_sound(dm)

        # Return False so the bot continues to search for monster and fights 1 more battle.
        return False

    # # 3. Check horse stamp indicator (missing horse buff on overworld)
    # if not is_in_battle(dm):
    #     (_, x_bread, _) = dm.FindPic(50, 650, 93, 689, r'anti_cheat\bread.bmp', '101010', 0.75, 0)
    #     if x_bread > 0:
    #         (_, x_horse, _) = dm.FindPic(599, 21, 650, 49, r'anti_cheat\horse.bmp', '101010', 0.75, 0)
    #         if x_horse <= 0:
    #             # Brief verification delay to avoid single-frame UI flicker false alarm
    #             time.sleep(0.1)
    #             (_, x_horse_verify, _) = dm.FindPic(599, 21, 650, 49, r'anti_cheat\horse.bmp', '101010', 0.75, 0)
    #             if x_horse_verify <= 0:
    #                 now = time.time()
    #                 if not _anti_cheat_pending_relog:
    #                     _anti_cheat_pending_relog = True
    #                     _last_anti_cheat_sound_time = now
    #                     print('[Anti-Cheat] 🚨 Anti-cheat detected: Horse stamp missing on overworld!')
    #                     print('[Anti-Cheat] 🔔 Alert sound triggered. Will fight 1 more battle before relogging.')
    #                     play_alert_sound(dm)
    #                 elif now - _last_anti_cheat_sound_time > 15.0:
    #                     _last_anti_cheat_sound_time = now
    #                     print('[Anti-Cheat] 🚨 Anti-cheat flagged (missing horse stamp). Waiting for 1 battle to finish before relog...')
    #                     play_alert_sound(dm)
    #                 return False

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
    - An alive mercenary has HP > 0 (red HP bar, or green HP bar if poisoned/debuffed).
    - A DEAD mercenary has HP = 0 (no red, no green on HP bar).
    - If a mercenary has low HP (e.g. 5% HP remaining), red HP pixels are still present (>= 6).
    
    Returns:
        dead_slots: list of dead slot numbers (1-indexed: 2 to 12 by default).
    """
    # The mercenary sidebar is hidden during battle; only check on overworld
    if is_in_battle(dm):
        return []

    # Use unique filename per process to avoid multi-instance file collisions
    pid = os.getpid()
    temp_path = os.path.join(dm.getPath(), f'temp_merc_sidebar_{pid}.bmp')
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

        dead_slots = []
        x_low = 4 if w >= 50 else 2
        x_high = min(w - 2, 52)

        # Do not include main character (slot 0) by default; only check mercenary slots (1 to 11 -> slots 2 to 12)
        start_index = 0 if include_main_character else 1
        for i in range(start_index, 12):
            slot_num = i + 1

            # Check portrait area to skip empty / unassigned mercenary slots
            slot_y_start = max(0, int(round(i * 41.0)))
            slot_y_end = min(h, int(round(i * 41.0 + 35)))
            portrait = img[slot_y_start:slot_y_end, x_low:x_high]
            if portrait.size == 0:
                continue

            std_val = float(np.std(portrait))
            mean_val = float(np.mean(portrait))
            if std_val < 15.0 or mean_val < 20.0:
                # Uniform/empty background -> no mercenary in this slot
                continue

            # HP bar location:
            # In the 500px sidebar, each slot is 41px tall. The HP bar center is at 37 + i * 41.0
            # (Slot 1: y=37, Slot 2: y=78, Slot 3: y=119, ..., Slot 12: y=488)
            # We sample a vertical band of 7 rows centered on the HP bar
            hp_y_center = int(round(37 + i * 41.0))
            y_low = max(0, hp_y_center - 3)
            y_high = min(h, hp_y_center + 4)

            hp_strip = img[y_low:y_high, x_low:x_high]
            if hp_strip.size == 0:
                continue

            r = hp_strip[:, :, 2].astype(int)
            g = hp_strip[:, :, 1].astype(int)
            b = hp_strip[:, :, 0].astype(int)

            # Red HP bar in Gersang: pure crimson red (184, 26, 26)
            red_mask = (r > 140) & (g < 80) & (b < 80) & (r > g * 1.5) & (r > b * 1.5)
            # Green HP bar in Gersang: poisoned / debuffed status
            green_mask = (g > 120) & (r < 90) & (b < 90) & (g > r * 1.4)

            red_pixels = int(np.sum(red_mask))
            green_pixels = int(np.sum(green_mask))

            # A mercenary is alive if their HP bar has visible red or green pixels (HP > 0).
            # When DEAD (HP = 0), both red and green pixels are completely absent (< 6).
            has_alive_hp = (red_pixels >= 6) or (green_pixels >= 6)

            if not has_alive_hp:
                dead_slots.append(slot_num)

        if dead_slots:
            print(f'[Revival] ⚠️ Dead mercenary detected in slots: {dead_slots}')

        return dead_slots
    except Exception as e:
        print(f'[Revival] Error checking mercenary sidebar: {e}')
        return []
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


def is_mercenary_dead(dm, drake_images=None):
    """
    Checks if any mercenary is dead (HP = 0, no red/green HP bar).
    Returns (is_dead: bool, dead_slots: list[int]).
    """
    x1, y1, x2, y2 = MERCENARY_SIDEBAR_REGION
    dead_slots = detect_dead_mercenary_slots(dm, x1, y1, x2, y2)
    if dead_slots:
        return True, dead_slots

    return False, []


_last_alt_1_time = 0


def press_alt_1(dm, min_interval=1.0):
    """
    Press Alt+1 to consume quick-slot revival item (half-chicken soup).
    """
    global _last_alt_1_time
    now = time.time()
    elapsed = now - _last_alt_1_time
    if elapsed < min_interval:
        wait_ms = int((min_interval - elapsed) * 1000)
        dm.Delay(wait_ms)

    print('[Revival] 🍗 Pressing Alt+1 to consume revival item...')
    dm.KeyDown(18)   # Alt
    dm.Delay(150)
    dm.KeyPress(49)  # '1'
    dm.Delay(150)
    dm.KeyUp(18)     # Alt
    dm.Delay(300)
    # press 1 again
    dm.KeyPress(49)  # '1'
    dm.Delay(150)
    _last_alt_1_time = time.time()
    return True


def revive_mercenaries_via_inventory(dm, dead_slots=None):
    """
    Fallback: Opens inventory ('i'), searches for revival.bmp (half-chicken soup),
    and right-clicks it on each dead mercenary (keys 2-12).
    """
    print('[Revival] 🎒 Opening inventory (i) to revive dead mercenaries...')
    dm.KeyPress(73)  # 'i' key
    dm.Delay(500)

    # Search for revival.bmp in inventory
    (_, rx, ry) = dm.FindPic(0, 0, 1024, 768, 'revival.bmp|drake_revival_item.bmp', '101010', 0.7, 0)
    if rx <= 0:
        # Default top-left inventory slot coordinate
        rx, ry = 600, 150
        print(f'[Revival] revival.bmp / drake_revival_item.bmp template not found, using default slot ({rx}, {ry})')
    else:
        print(f'[Revival] Found revival item at ({rx}, {ry})')

    target_slots = dead_slots if dead_slots else list(range(2, 13))
    for slot_num in target_slots:
        key = MERCENARY_SLOT_KEYS.get(slot_num)
        if key:
            dm.KeyPress(key)
            dm.Delay(100)
            dm.MoveTo(rx, ry)
            dm.Delay(80)
            dm.RightClick()
            dm.Delay(100)

    # Close inventory
    dm.KeyPress(73)  # 'i' key
    dm.Delay(500)
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
    """Revives dead mercenaries via ensure_mercenaries_recovered."""
    ensure_mercenaries_recovered(dm)


def check_dead_mercenary(dm, drake_images=None, max_attempts=2):
    """
    Checks if any mercenary is dead and revives them.
    Can only be executed outside of battle.
    Returns True if alive/revived, False if dead mercenaries could not be recovered.
    """
    if is_in_battle(dm):
        return True
    return ensure_mercenaries_recovered(dm, drake_images=drake_images, max_attempts=max_attempts)


def ensure_mercenaries_recovered(dm, drake_images=None, max_attempts=2):
    """
    Ensures dead mercenaries are revived.
    Can only be executed outside of battle.
    First tries Alt+1 (quick-slot soup).
    If mercenaries remain dead, falls back to inventory revival.
    Returns True if all mercenaries are confirmed alive, False if any remain dead.
    """
    # Mercenary revival can only be checked/performed when not in battle
    if is_in_battle(dm):
        return True

    is_dead, dead_slots = is_mercenary_dead(dm, drake_images)
    if not is_dead:
        # press 1 first before continue checking
        return True

    print(f'[Revival] ⚠️ Dead mercenary detected (slots: {dead_slots}). Reviving...')

    # Method 1: Alt+1 quick-slot revival
    for attempt in range(max_attempts):
        press_alt_1(dm, min_interval=1.0)
        dm.Delay(1200)  # Allow time for animation and HP bar update

        still_dead, remaining_slots = is_mercenary_dead(dm, drake_images)
        if not still_dead:
            print('[Revival] ✅ All mercenaries confirmed recovered and alive via Alt+1.')
            return True
        print(f'[Revival] ⚠️ Mercenaries still dead after Alt+1 attempt {attempt+1}/{max_attempts} (slots: {remaining_slots}).')

    still_dead, remaining_slots = is_mercenary_dead(dm, drake_images)
    if not still_dead:
        print('[Revival] ✅ All mercenaries confirmed recovered and alive via inventory.')
        return True

    print(f'[Revival] ⛔ Mercenaries still dead (remaining slots: {remaining_slots})!')
    return False


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
    while time.time() - start_time < 10:
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


# ---------------------------------------------------------------------------
# Opposite Direction Monster Detection & Execution (Shared Combat Routine)
# ---------------------------------------------------------------------------
# Condition 1: East / North-East opposite area
OPPOSITE_MONSTER_REGION = (546, 101, 938, 294)
OPPOSITE_TARGET_POSITION = (961, 100)
OPPOSITE_MONSTER_IMAGES = '|'.join(
    [r'ikan_tol\ikan_tol.bmp'] +
    [rf'ikan_tol\ikan_tol_{i}.bmp' for i in range(1, 5)] +
    [rf'ikan_tol\ikan_tol_q{i}.bmp' for i in range(1, 5)]
)

# Condition 2: West / North-West opposite area
OPPOSITE_MONSTER_REGION_2 = (183, 93, 465, 374)
OPPOSITE_TARGET_POSITION_2 = (50, 600)
OPPOSITE_MONSTER_IMAGES_2 = '|'.join(
    [r'ikan_tol\ikan_tol2.bmp'] +
    [rf'ikan_tol\ikan_tol2_{i}.bmp' for i in range(1, 5)] +
    [rf'ikan_tol\ikan_tol2_q{i}.bmp' for i in range(1, 5)]
)


def _default_send_key(dm, key, hold_ms=35, delay_after_ms=35):
    """Reliably send a key press in background mode."""
    dm.KeyDown(key)
    dm.Delay(hold_ms)
    dm.KeyUp(key)
    dm.Delay(delay_after_ms)


def _default_initiation_battle(dm):
    """Default preparation aura skills (Q, W)."""
    dm.Delay(35)
    _default_send_key(dm, 81, 35, 35)   # Q
    _default_send_key(dm, 87, 35, 35)   # W
    dm.Delay(35)


def _default_execute_skill_loop(dm):
    """Default mercenary attack skill loop."""
    for key in [50, 51, 52, 53, 54]:
        _default_send_key(dm, key, 35, 35)
        _default_send_key(dm, 69, 35, 35)
        _default_send_key(dm, 69, 35, 35)


def check_and_execute_opposite_monster(
    dm,
    initiation_func=None,
    skill_loop_func=None,
    duration=15,
    sim=0.8,
) -> bool:
    """
    Global battle handler: checks for monsters in opposite direction regions.
    Condition 1: Check region (546, 101, 938, 294) -> move cursor to (961, 100) -> execute battle skills.
    Condition 2: Check region (183, 93, 465, 374) -> move cursor to (139, 584) -> execute battle skills.

    Can be shared across all bots and modules. Accepts custom callbacks for character-specific skill sequences.
    Returns True if a monster was found and attacked, False otherwise.
    """
    init_combat = initiation_func or _default_initiation_battle
    exec_skills = skill_loop_func or _default_execute_skill_loop

    # Condition 1: East / North-East opposite area
    (x1, y1, x2, y2) = OPPOSITE_MONSTER_REGION
    (r, opp_x, opp_y) = dm.FindPic(x1, y1, x2, y2, OPPOSITE_MONSTER_IMAGES, '050505', sim, 0)
    if opp_x > 0 and opp_y > 0:
        print(f'[Opposite Monster 1] Found monster at ({opp_x}, {opp_y}) in region {OPPOSITE_MONSTER_REGION}')
        print(f'[Opposite Monster 1] Moving cursor to {OPPOSITE_TARGET_POSITION} and executing battle skill...')
        dm.MoveTo(OPPOSITE_TARGET_POSITION[0], OPPOSITE_TARGET_POSITION[1])
        dm.Delay(50)
        init_combat(dm)
        dm.Delay(50)
        exec_skills(dm)
        dm.Delay(50)
        time.sleep(duration)
        return True

    # Condition 2: West / North-West opposite area (183, 93, 465, 374)
    (x2_1, y2_1, x2_2, y2_2) = OPPOSITE_MONSTER_REGION_2
    (r2, opp2_x, opp2_y) = dm.FindPic(x2_1, y2_1, x2_2, y2_2, OPPOSITE_MONSTER_IMAGES_2, '050505', sim, 0)
    if opp2_x > 0 and opp2_y > 0:
        print(f'[Opposite Monster 2] Found monster at ({opp2_x}, {opp2_y}) in region {OPPOSITE_MONSTER_REGION_2}')
        print(f'[Opposite Monster 2] Moving cursor to {OPPOSITE_TARGET_POSITION_2} and executing battle skill...')
        dm.MoveTo(OPPOSITE_TARGET_POSITION_2[0], OPPOSITE_TARGET_POSITION_2[1])
        dm.Delay(50)
        init_combat(dm)
        dm.Delay(50)
        exec_skills(dm)
        dm.Delay(50)
        time.sleep(duration)
        return True

    return False

