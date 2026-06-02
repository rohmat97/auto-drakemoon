# utils.py - Automation Helper Utilities

import os
import sys
import time
import keyboard
import winsound
from tkinter import messagebox
import config


def check_hardware_authorization():
    pass


def move_game_window(dm):
    hwnd = dm.FindWindow('', 'Gersang')
    if hwnd == 0:
        messagebox.showerror('Error', "Gersang game window not found, please start the game first!")
        sys.exit(1)
    dm.MoveWindow(hwnd, 0, 0)
    print("Moved 'Gersang' window to top-left (0, 0)")
    dm.Delay(500)


def check_revive(dm):
    if config.paused:
        return False
    (r, x, y) = dm.FindPic(549, 446, 581, 474, 'revivedrake.bmp', '050505', 0.8, 0)
    if x > 0:
        print('Main character revived successfully')
        dm.MoveTo(x, y)
        dm.Delay(100)
        dm.LeftClick()
        dm.Delay(200)
        dm.LeftClick()
        dm.Delay(200)
        return True
    return False


def has_non_black_in_region(dm, x1, y1, x2, y2, direction_name, threshold=0.025):
    '''
    Use non-black pixel ratio to determine if there are monsters in the region
    threshold: Non-black pixel ratio threshold, default 2.5%
    '''
    non_black_count = 0
    total_points = 0
    step = 2
    for py in range(y1, y2 + 1, step):
        for px in range(x1, x2 + 1, step):
            color = dm.GetColor(px, py)
            total_points += 1
            if color != '080808' and color != '':
                non_black_count += 1

    if total_points == 0:
        return False
    ratio = non_black_count / total_points
    has_non_black = ratio > threshold
    if direction_name:
        status = '[Monsters Found]' if has_non_black else '[No Monsters]'
        print(f'''   └ {direction_name:4} Region ({x1},{y1})-({x2},{y2}) → {status}  (Non-black: {non_black_count}/{total_points} ≈ {ratio:.1%})''')
    return has_non_black


def check_formation(dm, region1, region2):
    (r1, x1, y1) = dm.FindPic(region1[0], region1[1], region1[2], region1[3], '080808.bmp', '050505', 1, 0)
    (r2, x2, y2) = dm.FindPic(region2[0], region2[1], region2[2], region2[3], '080808.bmp', '050505', 1, 0)
    if x1 > 0 and x2 > 0:
        return True
    return False


def execute_skill_loop(dm):
    dm.KeyPress(50)
    dm.Delay(50)
    dm.KeyPress(69)
    dm.Delay(50)
    dm.KeyPress(69)
    dm.Delay(50)
    dm.KeyPress(51)
    dm.Delay(50)
    dm.KeyPress(69)
    dm.Delay(50)
    dm.KeyPress(69)
    dm.Delay(50)


def check_and_refill_satiety(dm):
    r1, x1, y1 = dm.FindPic(166, 696, 197, 701, 'food.bmp', '050505', 0.8, 0)
    r2, x2, y2 = dm.FindPic(0, 0, 1714, 1912, 'bread.bmp', '050505', 0.8, 0)
    if x1 > 0:
        print('Satiety is sufficient')
        return True
    elif x2 > 0:
        print('Increasing satiety')
        dm.KeyDown(18)
        dm.KeyPress(50)
        dm.KeyUp(18)
        return True
    return False


def is_satiety_depleted(dm):
    r3, x3, y3 = dm.FindPic(585, 444, 620, 472, 'emptyfooddrake.bmp', '050505', 0.8, 0)
    if x3 > 0:
        print('Satiety depleted, script paused')
        config.paused = True
        return True
    return False


def recover_dead_mercenaries_if_needed(dm):
    r_rev, x_rev, _ = dm.FindPic(549, 446, 581, 474, 'revivedrake.bmp', '050505', 0.8, 0)
    if x_rev <= 0:
        r_special, x_special, y_special = dm.FindPic(1, 66, 82, 534, 'drake1.bmp|drake2.bmp|drake3.bmp|drake5.bmp|drake6.bmp|drake7.bmp|drake8.bmp|drake9.bmp|drake10.bmp|drake11.bmp|drake88.bmp', '050505', 0.8, 0)
        if x_special > 0:
            print('Detected dead mercenary, using half chicken soup')
            dm.KeyDown(18)
            dm.KeyPress(49)
            dm.KeyPress(49)
            dm.KeyUp(18)
            return True
    return False


def check_anti_cheat(dm):
    r_horse, x_horse, _ = dm.FindPic(602, 47, 653, 75, 'horse.bmp', '050505', 0.8, 0)
    r_bread, x_bread, _ = dm.FindPic(53, 676, 96, 715, 'bread.bmp', '050505', 0.8, 0)
    if x_horse <= 0 and x_bread > 0:
        print('Detected anti-cheat (Horse token), pausing script')
        try:
            sound_path = os.path.join(dm.getPath(), 'whatsapp.wav')
            if os.path.exists(sound_path):
                winsound.PlaySound(sound_path, winsound.SND_FILENAME)
        except Exception:
            pass
        keyboard.press_and_release('f10')
        return True
    return False


def try_engage_monster(dm):
    r, x, y = dm.FindPic(99, 110, 967, 550, 'ghosttur1.bmp|ghosttur2.bmp|ghosttur3.bmp|ghosttur4.bmp|ghosttur5.bmp|ghosttur6.bmp|ghosttur7.bmp|ghosttur8.bmp|ghosttur9.bmp|ghosttur10.bmp|ghosttur11.bmp|ghosttur12.bmp|ghosttur13.bmp|ghosttur14.bmp|ghosttur15.bmp|', '050505', 0.8, 0)
    if x > 0:
        print(f"Found monster at coordinates: ({x}, {y})")
        dm.MoveTo(x, y)
        dm.Delay(150)
        dm.RightClick()
        dm.Delay(300)
        check_revive(dm)
        recover_dead_mercenaries_if_needed(dm)
        
        print('Waiting to enter battle screen... (max 3 seconds)')
        battle_entered = False
        start_time = time.time()
        attempt = 0
        while time.time() - start_time < 3.5:
            if check_anti_cheat(dm):
                break
            
            r_battle, x_battle, y_battle = dm.FindPic(962, 692, 1019, 773, 'battle.bmp', '050505', 0.8, 0)
            if x_battle > 0:
                print('✅ Successfully entered battle screen')
                battle_entered = True
                break
            elif time.time() - start_time > 1.2 and attempt < 3:
                print('Did not enter battle, right-clicking monster again...')
                dm.MoveTo(x, y)
                dm.Delay(100)
                dm.RightClick()
                dm.Delay(300)
                attempt += 1    
            time.sleep(0.08)
            
        if not battle_entered:
            print('⚠️  Still not in battle after 2 clicks, skipping this monster')
            time.sleep(0.8)
            return False
        return True
    return False


def execute_battle_tactic(dm, direction, monster_dir):
    if direction == 'East' and monster_dir == 'South':
        dm.MoveTo(12, 397)
        time.sleep(0.53)
        dm.MoveTo(514, 367)
        dm.Delay(50)
        dm.MoveTo(904, 472)
        dm.Delay(50)
        dm.KeyPress(81)
        dm.Delay(50)
        dm.KeyPress(87)
        dm.Delay(50)
        dm.MoveTo(650, 568)
        dm.Delay(200)
        dm.KeyDown(40)
        time.sleep(0.3)
        dm.KeyUp(40)
        dm.Delay(50)
        execute_skill_loop(dm)
        dm.Delay(50)
        time.sleep(8)
        
    elif direction == 'East' and monster_dir == 'West':
        dm.MoveTo(12, 397)
        time.sleep(0.57)
        dm.MoveTo(514, 367)
        dm.Delay(50)
        dm.KeyPress(81)
        dm.Delay(50)
        dm.KeyPress(87)
        dm.Delay(50)
        dm.MoveTo(153, 358)
        dm.Delay(50)
        dm.KeyDown(37)
        time.sleep(0.15)
        dm.KeyUp(37)
        dm.Delay(50)
        execute_skill_loop(dm)
        dm.Delay(50)
        time.sleep(8)
        
    elif direction == 'East' and monster_dir == 'North':
        dm.MoveTo(12, 397)
        time.sleep(0.53)
        dm.MoveTo(514, 367)
        dm.Delay(50)
        dm.MoveTo(954, 223)
        dm.Delay(50)
        dm.KeyPress(81)
        dm.Delay(50)
        dm.KeyPress(87)
        dm.Delay(50)
        dm.MoveTo(662, 76)
        dm.Delay(50)
        execute_skill_loop(dm)
        dm.Delay(50)
        time.sleep(8)
        
    elif direction == 'South' and monster_dir == 'East':
        dm.MoveTo(490, 36)
        time.sleep(0.53)
        dm.MoveTo(460, 398)
        dm.Delay(50)
        dm.MoveTo(803, 504)
        dm.Delay(50)
        dm.KeyPress(81)
        dm.Delay(50)
        dm.KeyPress(87)
        dm.Delay(50)
        dm.MoveTo(1000, 478)
        time.sleep(0.33)
        dm.MoveTo(178, 476)
        dm.Delay(50)
        dm.KeyDown(39)
        time.sleep(0.35)
        dm.KeyUp(39)
        dm.Delay(50)
        execute_skill_loop(dm)
        dm.Delay(50)
        time.sleep(8)
        
    elif direction == 'South' and monster_dir == 'West':
        dm.MoveTo(490, 36)
        time.sleep(0.53)
        dm.MoveTo(460, 398)
        dm.Delay(50)
        dm.MoveTo(164, 449)
        dm.Delay(50)
        dm.KeyPress(81)
        dm.Delay(50)
        dm.KeyPress(87)
        dm.Delay(50)
        dm.MoveTo(8, 449)
        time.sleep(0.33)
        dm.MoveTo(399, 531)
        dm.Delay(50)
        execute_skill_loop(dm)
        dm.Delay(50)
        time.sleep(8)
        
    elif direction == 'South' and monster_dir == 'North':
        dm.MoveTo(490, 36)
        time.sleep(0.57)
        dm.MoveTo(460, 398)
        dm.Delay(50)
        dm.MoveTo(497, 373)
        dm.Delay(50)
        dm.KeyPress(81)
        dm.Delay(50)
        dm.KeyPress(87)
        dm.Delay(50)
        dm.MoveTo(477, 250)
        dm.Delay(50)
        execute_skill_loop(dm)
        dm.Delay(50)
        time.sleep(8)
        
    elif direction == 'West' and monster_dir == 'East':
        dm.MoveTo(1025, 378)
        time.sleep(0.66)
        dm.MoveTo(356, 368)
        dm.Delay(50)
        dm.KeyPress(81)
        dm.Delay(50)
        dm.KeyPress(87)
        dm.Delay(50)
        dm.MoveTo(513, 375)
        dm.Delay(50)
        dm.KeyDown(39)
        time.sleep(0.4)
        dm.KeyUp(39)
        dm.Delay(50)
        execute_skill_loop(dm)
        dm.Delay(50)
        time.sleep(8)
        
    elif direction == 'West' and monster_dir == 'South':
        dm.MoveTo(1025, 378)
        time.sleep(0.66)
        dm.MoveTo(356, 368)
        dm.Delay(50)
        dm.MoveTo(150, 646)
        dm.Delay(50)
        dm.KeyPress(81)
        dm.Delay(50)
        dm.KeyPress(87)
        dm.Delay(50)
        execute_skill_loop(dm)
        dm.Delay(50)
        time.sleep(8)
        
    elif direction == 'West' and monster_dir == 'North':
        dm.MoveTo(1025, 378)
        time.sleep(0.66)
        dm.MoveTo(356, 368)
        dm.Delay(50)
        dm.MoveTo(123, 147)
        dm.Delay(50)
        dm.KeyPress(81)
        dm.Delay(50)
        dm.KeyPress(87)
        dm.Delay(50)
        dm.MoveTo(154, 101)
        dm.Delay(50)
        execute_skill_loop(dm)
        dm.Delay(50)
        time.sleep(8)
        
    elif direction == 'North' and monster_dir == 'East':
        dm.MoveTo(483, 788)
        time.sleep(0.66)
        dm.MoveTo(670, 329)
        dm.Delay(50)
        dm.MoveTo(923, 74)
        dm.Delay(50)
        dm.KeyPress(81)
        dm.Delay(50)
        dm.KeyPress(87)
        dm.Delay(50)
        dm.MoveTo(1006, 128)
        time.sleep(0.33)
        dm.MoveTo(777, 201)
        dm.Delay(50)
        execute_skill_loop(dm)
        dm.Delay(50)
        time.sleep(8)
        
    elif direction == 'North' and monster_dir == 'South':
        dm.MoveTo(483, 788)
        time.sleep(0.66)
        dm.MoveTo(670, 329)
        dm.Delay(50)
        dm.KeyPress(81)
        dm.Delay(50)
        dm.KeyPress(87)
        dm.Delay(50)
        dm.MoveTo(508, 571)
        dm.Delay(50)
        execute_skill_loop(dm)
        dm.Delay(50)
        time.sleep(8)
        
    elif direction == 'North' and monster_dir == 'West':
        dm.MoveTo(483, 788)
        time.sleep(0.66)
        dm.MoveTo(670, 329)
        dm.Delay(50)
        dm.MoveTo(201, 80)
        dm.Delay(50)
        dm.KeyPress(81)
        dm.Delay(50)
        dm.KeyPress(87)
        dm.Delay(50)
        dm.MoveTo(39, 100)
        dm.Delay(50)
        dm.KeyDown(40)
        time.sleep(0.1)
        dm.KeyUp(40)
        dm.Delay(50)
        dm.KeyDown(37)
        time.sleep(0.1)
        dm.KeyUp(37)
        dm.Delay(50)
        execute_skill_loop(dm)
        dm.Delay(50)
        time.sleep(8)
