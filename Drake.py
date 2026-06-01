import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import time
import keyboard
from PyGameAuto.Dm import RegDm
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import uuid
import hashlib
import winsound

AUTHORIZED_HARDWARE_ID = '3528f4a89e829d46405972781ac4863f3b2916bb9f03e84a5a6b7a3eca6e2d25'
paused = False


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
    if paused:
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


def has_non_black_in_region(dm, x1, y1, x2, y2, direction_name, threshold = 0.025):
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


def create_login_window():
    
    def on_start():
        # root.destroy()
        run_main_script()

    on_start()
    # root = tk.Tk()
    # root.title('Discord')
    # root.geometry('350x300')
    # root.resizable(False, False)
    # root.configure(bg='#2F4F4F')
    # style = ttk.Style()
    # style.theme_use('default')
    # style.configure('TLabel', background='#2F4F4F', foreground='white', font=('Arial', 12))
    # style.configure('TButton', background='#468282', foreground='white', font=('Arial', 10, 'bold'))
    # style.map('TButton', background=[('active', '#5A9A9A')])
    # frame = ttk.Frame(root, padding=20)
    # frame.pack(expand=True)
    # welcome_label = ttk.Label(frame, text='Welcome to the Program', font=('Arial', 16))
    # welcome_label.pack(pady=20)
    # start_button = ttk.Button(frame, text='Start Program', command=on_start)
    # start_button.pack(pady=10)
    # note_label = tk.Label(frame, text='For fees/inquiries\nTelegram: hkaiscript', bg='#2F4F4F', fg='#B0C4DE', justify='center', font=('Arial', 10))
    # note_label.pack(pady=20)
    # note_label.config(cursor='hand2')
    # note_label.bind('<Button-1>', (lambda e: webbrowser.open('https://t.me/hkaiscript')))
    # root.mainloop()


def run_main_script():
    global paused
    check_hardware_authorization()
    dm = RegDm.reg()
    dm.SetShowErrorMsg(0)
    ret = dm.reg('hkaiscript44c3dffb21a432409f0d422e1a8dcc35', 'sqDvF')
    print('DaMo Registration Result:', ret)
    print('DaMo Version:', dm.ver())
    move_game_window(dm)
    if getattr(sys, 'frozen', None):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
        print('Current Path:', basedir)
    path = os.path.join(basedir, 'Resource')
    print('Resource Path:', path)
    dm.setPath(path)
    paused = False
    
    def on_f10_press(event):
        global paused
        if event.name == 'f10':
            paused = not paused
            if paused:
                print('All commands paused, press F10 to resume...')
            else:
                print('All commands resumed...')

    keyboard.on_press_key('f10', on_f10_press)
    
    formation_regions = {
        'East': [
            (952, 166, 997, 283),
            (988, 463, 1005, 489)],
        'South': [
            (943, 487, 1001, 523),
            (26, 520, 69, 584)],
        'West': [
            (16, 131, 36, 191),
            (17, 586, 51, 649)],
        'North': [
            (938, 166, 1007, 274),
            (34, 189, 120, 306)]
    }
    monster_direction_regions = {
        'East': (175, 739, 192, 748),
        'South': (120, 756, 139, 765),
        'West': (79, 740, 86, 754),
        'North': (124, 715, 139, 730)
    }
    monster_checks = {
        'East': ['South', 'West', 'North'],
        'South': ['East', 'West', 'North'],
        'West': ['East', 'South', 'North'],
        'North': ['East', 'South', 'West']
    }
    
    try:
        try:
            while True:
                check_revive(dm)
                if paused:
                    time.sleep(0.5)
                    continue
                
                r1, x1, y1 = dm.FindPic(166, 696, 197, 701, 'food.bmp', '050505', 0.8, 0)
                r2, x2, y2 = dm.FindPic(0, 0, 1714, 1912, 'bread.bmp', '050505', 0.8, 0)
                if x1 > 0:
                    print('Satiety is sufficient')
                elif x2 > 0:
                    print('Increasing satiety')
                    dm.KeyDown(18)
                    dm.KeyPress(50)
                    dm.KeyUp(18)
                
                r3, x3, y3 = dm.FindPic(585, 444, 620, 472, 'emptyfooddrake.bmp', '050505', 0.8, 0)
                if x3 > 0:
                    print('Satiety depleted, script paused')
                    paused = True
                    continue
                
                r, x, y = dm.FindPic(99, 110, 967, 550, 'ghosttur1.bmp|ghosttur2.bmp|ghosttur3.bmp|ghosttur4.bmp|ghosttur5.bmp|ghosttur6.bmp|ghosttur7.bmp|ghosttur8.bmp|ghosttur9.bmp|ghosttur10.bmp|ghosttur11.bmp|ghosttur12.bmp|ghosttur13.bmp|ghosttur14.bmp|ghosttur15.bmp|', '050505', 0.8, 0)
                if x > 0:
                    print(f"Found monster at coordinates: ({x}, {y})")
                    dm.MoveTo(x, y)
                    dm.Delay(150)
                    dm.RightClick()
                    dm.Delay(300)
                    check_revive(dm)
                    
                    r_special, x_special, y_special = dm.FindPic(1, 66, 82, 534, 'drake1.bmp|drake2.bmp|drake3.bmp|drake5.bmp|drake6.bmp|drake7.bmp|drake8.bmp|drake9.bmp|drake10.bmp|drake11.bmp|drake88.bmp', '050505', 0.8, 0)
                    if x_special > 0:
                        print('Detected dead mercenary, using half chicken soup')
                        dm.KeyDown(18)
                        dm.KeyPress(49)
                        dm.KeyPress(49)
                        dm.KeyUp(18)
                        
                    print('Waiting to enter battle screen... (max 3 seconds)')
                    battle_entered = False
                    start_time = time.time()
                    attempt = 1
                    while time.time() - start_time < 3.5:
                        r_horse, x_horse, _ = dm.FindPic(602, 47, 653, 75, 'horse.bmp', '050505', 0.8, 0)
                        r_bread, x_bread, _ = dm.FindPic(53, 676, 96, 715, 'bread.bmp', '050505', 0.8, 0)
                        if x_horse <= 0 and x_bread > 0:
                            print('Detected anti-cheat (Horse token), pausing script')
                            try:
                                sound_path = os.path.join(dm.getPath(), 'whatsapp.wav')
                                if os.path.exists(sound_path):
                                    winsound.PlaySound(sound_path, winsound.SND_FILENAME)
                            except:
                                pass
                            keyboard.press_and_release('f10')
                            break
                        
                        r_battle, x_battle, y_battle = dm.FindPic(962, 692, 1019, 773, 'battle.bmp', '050505', 0.8, 0)
                        if x_battle > 0:
                            print('✅ Successfully entered battle screen')
                            battle_entered = True
                            break
                        
                        elif time.time() - start_time > 1.2 and attempt == 1:
                            print('Did not enter battle, right-clicking monster again...')
                            dm.MoveTo(x, y)
                            dm.Delay(100)
                            dm.RightClick()
                            dm.Delay(300)
                            attempt = 2
                        time.sleep(0.08)
                        
                    if not battle_entered:
                        print('⚠️  Still not in battle after 2 clicks, skipping this monster')
                        time.sleep(0.8)
                        continue
                
                r_battle, x_battle, y_battle = dm.FindPic(962, 692, 1019, 773, 'battle.bmp', '050505', 0.8, 0)
                if x_battle > 0:
                    print('Entered battle screen')
                    action_executed = False
                    
                    while True:
                        check_revive(dm)
                        if paused:
                            time.sleep(1)
                            continue
                        
                        if action_executed:
                            break
                            
                        for direction, regions in formation_regions.items():
                            if action_executed:
                                break
                                
                            if check_formation(dm, regions[0], regions[1]):
                                print(f'Detected formation position: {direction}')
                                time.sleep(0.1)
                                
                                for monster_dir in monster_checks[direction]:
                                    x1, y1, x2, y2 = monster_direction_regions[monster_dir]
                                    if has_non_black_in_region(dm, x1, y1, x2, y2, monster_dir, threshold=0.03):
                                        print(f'Executing command → Formation:{direction} | Monster:{monster_dir}')
                                        
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
                                            time.sleep(12)
                                            
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
                                            time.sleep(12)
                                            
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
                                            time.sleep(12)
                                            
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
                                            time.sleep(12)
                                            
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
                                            time.sleep(12)
                                            
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
                                            time.sleep(12)
                                            
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
                                            time.sleep(12)
                                            
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
                                            time.sleep(12)
                                            
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
                                            time.sleep(12)
                                            
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
                                            time.sleep(12)
                                            
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
                                            time.sleep(12)
                                            
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
                                            time.sleep(12)
                                            
                                        print('Pressing Esc 4 times to exit')
                                        for _ in range(4):
                                            dm.KeyPress(27)
                                            dm.Delay(70)
                                        time.sleep(3)
                                        action_executed = True
                                        
                        r_battle, x_battle, y_battle = dm.FindPic(962, 692, 1019, 773, 'battle.bmp', '050505', 0.8, 0)
                        if x_battle <= 0:
                            print('Battle screen ended')
                            check_revive(dm)
                            
                            r_special, x_special, y_special = dm.FindPic(1, 66, 82, 534, 'drake1.bmp|drake2.bmp|drake3.bmp|drake5.bmp|drake6.bmp|drake7.bmp|drake8.bmp|drake9.bmp|drake10.bmp|drake11.bmp|drake88.bmp', '050505', 0.8, 0)
                            if x_special > 0:
                                print('Detected dead mercenary, using half chicken soup')
                                dm.KeyDown(18)
                                dm.KeyPress(49)
                                dm.KeyPress(49)
                                dm.KeyUp(18)
                            break
                        else:
                            time.sleep(1.0)
                            
                time.sleep(1)
                
        except KeyboardInterrupt:
            print('Program interrupted.')
    finally:
        keyboard.unhook_all()
        print('Cleanup complete, program ended.')


if __name__ == '__main__':
    create_login_window()
