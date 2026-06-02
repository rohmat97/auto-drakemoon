# Source Generated with Decompyle++ / restored from bytecode disassembly
# File: Drake假龜天_後台.py (Python 3.8)

import os
import sys
import time
import keyboard
from PyGameAuto.Dm import RegDm
import tkinter as tk
import wmi
from tkinter import ttk, messagebox
import webbrowser
import uuid
import hashlib
import winsound

AUTHORIZED_HARDWARE_ID = '3528f4a89e829d46405972781ac4863f3b2916bb9f03e84a5a6b7a3eca6e2d25'

def get_composite_hardware_id():
    c = wmi.WMI()
    disk_serial = c.Win32_DiskDrive()[0].SerialNumber.strip() if c.Win32_DiskDrive() else '未知'
    mac = ':'.join(['{:02x}'.format(uuid.getnode() >> i & 255) for i in range(0, 48, 8)][::-1])
    composite = f"{disk_serial}-{mac}"
    return hashlib.sha256(composite.encode()).hexdigest()

def check_hardware_authorization():
    current_id = get_composite_hardware_id()
    if current_id != AUTHORIZED_HARDWARE_ID:
        messagebox.showerror('錯誤', f'未授權的設備！\n你的硬體 ID: {current_id}\n請聯繫管理員授權。')
        sys.exit(1)

def move_game_window(dm):
    hwnd = dm.FindWindow('', 'Gersang')
    if hwnd == 0:
        messagebox.showerror('錯誤', "未找到 'Gersang' 遊戲視窗，請先啟動遊戲！")
        sys.exit(1)
    dm.MoveWindow(hwnd, 0, 0)
    print("已將 'Gersang' 視窗移動到左上角 (0, 0)")
    dm.Delay(500)
    return hwnd

def check_revive(dm):
    if paused:
        return False
    (r, x, y) = dm.FindPic(546, 420, 578, 448, 'revivedrake.bmp', '050505', 0.8, 0)
    if x > 0:
        print('主角復活成功')
        dm.MoveTo(x, y)
        dm.Delay(100)
        dm.LeftClick()
        dm.Delay(200)
        return True
    return False

def has_non_black_in_region(dm, x1, y1, x2, y2, direction_name, threshold=0.025):
    """
    使用非黑點比例判斷區域是否有怪物
    threshold: 非黑點比例閾值，預設 2.5%
    """
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
        status = '【有怪物】' if has_non_black else '【無怪物】'
        print(f"   └ {direction_name:4} 區域 ({x1},{y1})-({x2},{y2}) → {status}  (非黑: {non_black_count}/{total_points} ≈ {ratio:.1%})")
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
    run_main_script()
    # def on_start():
    #     root.destroy()
    #     run_main_script()

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
    
    # welcome_label = ttk.Label(frame, text='歡迎使用程式', font=('Arial', 16))
    # welcome_label.pack(pady=20)
    
    # start_button = ttk.Button(frame, text='啟動程式', command=on_start)
    # start_button.pack(pady=10)
    
    # note_label = tk.Label(frame, text='有關費用/問題查詢\ntelegram: hkaiscript', bg='#2F4F4F', fg='#B0C4DE', justify='center', font=('Arial', 10))
    # note_label.pack(pady=20)
    # note_label.config(cursor='hand2')
    # note_label.bind('<Button-1>', lambda e: webbrowser.open('https://t.me/hkaiscript'))
    
    # root.mainloop()

def run_main_script(stop_seconds=(0,)):
    global paused
    dm = RegDm.reg()
    ret = dm.reg('hkaiscript44c3dffb21a432409f0d422e1a8dcc35', 'sqDvF')
    print('大漠註冊結果:', ret)
    print('大漠版本:', dm.ver())
    hwnd = move_game_window(dm)
    
    dm_ret = dm.BindWindowEx(hwnd, 'gdi', 
                             'dx.mouse.position.lock.api|dx.mouse.position.lock.message|dx.mouse.clip.lock.api|dx.mouse.input.lock.api|dx.mouse.state.api|dx.mouse.api|dx.mouse.cursor', 
                             'dx.keypad.input.lock.api|dx.keypad.state.api|dx.keypad.api|dx.keypad.raw.input', 
                             '', 101)
    if dm_ret != 1:
        messagebox.showerror('錯誤', f'視窗綁定失敗，錯誤碼: {dm_ret}')
        sys.exit(1)
        
    print('視窗綁定成功，啟動後台模式')
    
    if getattr(sys, 'frozen', None):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
        
    path = os.path.join(basedir, 'Resource')
    dm.setPath(path)
    paused = False
    
    def on_f10_press(event=None):
        global paused
        if event.name == 'f10':
            paused = not paused
            if paused:
                print('所有指令已暫停，按 F10 繼續...')
                dm.UnBindWindow()
            else:
                print('所有指令已繼續...')
                dm.BindWindowEx(hwnd, 'gdi', 
                                 'dx.mouse.position.lock.api|dx.mouse.position.lock.message|dx.mouse.clip.lock.api|dx.mouse.input.lock.api|dx.mouse.state.api|dx.mouse.api|dx.mouse.cursor', 
                                 'dx.keypad.input.lock.api|dx.keypad.state.api|dx.keypad.api|dx.keypad.raw.input', 
                                 '', 101)

    keyboard.on_press_key('f10', on_f10_press)
    
    formation_regions = {
        '東': [(949, 140, 994, 257), (985, 437, 1002, 463)],
        '南': [(940, 461, 998, 497), (23, 494, 66, 558)],
        '西': [(13, 105, 33, 165), (14, 560, 48, 623)],
        '北': [(935, 140, 1004, 248), (31, 163, 117, 280)]
    }
    
    monster_direction_regions = {
        '東': (172, 713, 189, 722),
        '南': (117, 730, 136, 739),
        '西': (76, 714, 83, 728),
        '北': (121, 689, 136, 704)
    }
    
    monster_checks = {
        '東': ['南', '西', '北'],
        '南': ['東', '西', '北'],
        '西': ['東', '南', '北'],
        '北': ['東', '南', '西']
    }
    
    try:
        try:
            while True:
                check_revive(dm)
                if paused:
                    time.sleep(0.5)
                    continue
                    
                (r1, x1, y1) = dm.FindPic(52, 649, 246, 684, 'food.bmp', '050505', 0.8, 0)
                (r2, x2, y2) = dm.FindPic(43, 644, 101, 692, 'bread.bmp', '050505', 0.8, 0)
                
                if x1 > 0:
                    print('飽滿度足夠')
                elif x2 > 0:
                    print('增加飽滿度')
                    dm.KeyDown(18)
                    dm.KeyPress(50)
                    dm.KeyUp(18)
                    
                (r3, x3, y3) = dm.FindPic(582, 418, 617, 446, 'emptyfooddrake.bmp', '050505', 0.8, 0)
                if x3 > 0:
                    print('檢測到飽滿度耗盡，腳本暫停')
                    paused = True
                    continue
                    
                (r, x, y) = dm.FindPic(96, 84, 964, 524, 
                                       'ghosttur1.bmp|ghosttur2.bmp|ghosttur3.bmp|ghosttur4.bmp|ghosttur5.bmp|ghosttur6.bmp|ghosttur7.bmp|ghosttur8.bmp|ghosttur9.bmp|ghosttur10.bmp|ghosttur11.bmp|ghosttur12.bmp|ghosttur13.bmp|ghosttur14.bmp|ghosttur15.bmp|', 
                                       '050505', 0.8, 0)
                
                if x > 0:
                    check_revive(dm)
                    print(f'找到怪物 座標: ({x}, {y})')
                    dm.MoveTo(x, y)
                    dm.Delay(150)
                    dm.RightClick()
                    dm.Delay(300)
                    check_revive(dm)
                    
                    (r_special, x_special, y_special) = dm.FindPic(0, 0, 108, 499, 'drake1.bmp|drake2.bmp|drake3.bmp|drake5.bmp|drake6.bmp|drake7.bmp|drake8.bmp|drake9.bmp|drake10.bmp|drake11.bmp|drake88.bmp', '050505', 0.8, 0)
                    if x_special > 0:
                        print('檢測到死去傭兵，吃半雞湯')
                        dm.KeyDown(18)
                        dm.KeyPress(49)
                        dm.KeyPress(49)
                        dm.KeyUp(18)
                        
                    print('等待進入戰鬥畫面... (最多3秒)')
                    battle_entered = False
                    start_time = time.time()
                    attempt = 1
                    
                    while time.time() - start_time < 3.5:
                        (r_horse, x_horse, _) = dm.FindPic(599, 21, 650, 49, 'horse.bmp', '050505', 0.8, 0)
                        (r_bread, x_bread, _) = dm.FindPic(50, 650, 93, 689, 'bread.bmp', '050505', 0.8, 0)
                        
                        if x_horse <= 0 and x_bread > 0:
                            print('檢測到防外掛 (馬牌)，暫停腳本')
                            try:
                                sound_path = os.path.join(dm.getPath(), 'whatsapp.wav')
                                if os.path.exists(sound_path):
                                    winsound.PlaySound(sound_path, winsound.SND_FILENAME)
                            except:
                                pass
                            keyboard.press_and_release('f10')
                            break
                            
                        (r_battle, x_battle, y_battle) = dm.FindPic(959, 666, 1016, 747, 'battle.bmp', '050505', 0.8, 0)
                        if x_battle > 0:
                            print('✅ 成功進入戰鬥畫面')
                            battle_entered = True
                            break
                            
                        if time.time() - start_time > 1.2 and attempt == 1:
                            print('未進入戰鬥，重新右鍵點擊怪物...')
                            dm.MoveTo(x, y)
                            dm.Delay(100)
                            dm.RightClick()
                            dm.Delay(300)
                            attempt = 2
                        time.sleep(0.08)
                        
                    if not battle_entered:
                        print('⚠️  兩次點擊仍未進入戰鬥，跳過本次怪物')
                        time.sleep(0.8)
                        continue
                        
                (r, x, y) = dm.FindPic(959, 666, 1016, 747, 'battle.bmp', '050505', 0.8, 0)
                if x > 0:
                    print('進入戰鬥畫面')
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
                                print(f'檢測到陣形位置：{direction}')
                                time.sleep(0.1)
                                
                                for monster_dir in monster_checks[direction]:
                                    (x1, y1, x2, y2) = monster_direction_regions[monster_dir]
                                    if has_non_black_in_region(dm, x1, y1, x2, y2, monster_dir, threshold=0.03):
                                        print(f'執行指令 → 陣形:{direction} | 怪物:{monster_dir}')
                                        
                                        if direction == '東' and monster_dir == '南':
                                            dm.MoveTo(9, 371)
                                            time.sleep(0.53)
                                            dm.MoveTo(511, 341)
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
                                        elif direction == '東' and monster_dir == '西':
                                            dm.MoveTo(9, 371)
                                            time.sleep(0.53)
                                            dm.MoveTo(511, 341)
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
                                        elif direction == '東' and monster_dir == '北':
                                            dm.MoveTo(9, 371)
                                            time.sleep(0.53)
                                            dm.MoveTo(511, 341)
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
                                        elif direction == '南' and monster_dir == '東':
                                            dm.MoveTo(487, 10)
                                            time.sleep(0.53)
                                            dm.MoveTo(457, 372)
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
                                        elif direction == '南' and monster_dir == '西':
                                            dm.MoveTo(487, 10)
                                            time.sleep(0.53)
                                            dm.MoveTo(457, 372)
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
                                        elif direction == '南' and monster_dir == '北':
                                            dm.MoveTo(487, 10)
                                            time.sleep(0.53)
                                            dm.MoveTo(457, 372)
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
                                        elif direction == '西' and monster_dir == '東':
                                            dm.MoveTo(1022, 352)
                                            time.sleep(0.66)
                                            dm.MoveTo(353, 342)
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
                                        elif direction == '西' and monster_dir == '南':
                                            dm.MoveTo(1022, 352)
                                            time.sleep(0.66)
                                            dm.MoveTo(353, 342)
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
                                        elif direction == '西' and monster_dir == '北':
                                            dm.MoveTo(1022, 352)
                                            time.sleep(0.66)
                                            dm.MoveTo(353, 342)
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
                                        elif direction == '北' and monster_dir == '東':
                                            dm.MoveTo(480, 762)
                                            time.sleep(0.66)
                                            dm.MoveTo(667, 303)
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
                                        elif direction == '北' and monster_dir == '南':
                                            dm.MoveTo(480, 762)
                                            time.sleep(0.66)
                                            dm.MoveTo(667, 303)
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
                                        elif direction == '北' and monster_dir == '西':
                                            dm.KeyPress(27)
                                            dm.Delay(70)
                                            dm.KeyPress(27)
                                            dm.Delay(70)
                                            dm.KeyPress(27)
                                            dm.Delay(70)
                                            dm.KeyPress(27)
                                            dm.Delay(70)
                                            
                                        print('按 4 次 Esc 離開')
                                        for _ in range(4):
                                            dm.KeyPress(27)
                                            dm.Delay(70)
                                        time.sleep(3)
                                        action_executed = True
                                        
                        (r_battle_check, x_battle_check, y_battle_check) = dm.FindPic(959, 666, 1016, 747, 'battle.bmp', '050505', 0.8, 0)
                        if x_battle_check <= 0:
                            print('戰鬥畫面結束')
                            check_revive(dm)
                            (r_spec, x_spec, y_spec) = dm.FindPic(0, 0, 108, 499, 'drake1.bmp|drake2.bmp|drake3.bmp|drake5.bmp|drake6.bmp|drake7.bmp|drake8.bmp|drake9.bmp|drake10.bmp|drake11.bmp|drake88.bmp', '050505', 0.8, 0)
                            if x_spec > 0:
                                print('檢測到死去傭兵，吃半雞湯')
                                dm.KeyDown(18)
                                dm.KeyPress(49)
                                dm.KeyPress(49)
                                dm.KeyUp(18)
                            break
                        else:
                            time.sleep(1.0)
                time.sleep(1)
        except KeyboardInterrupt:
            print('程式被中斷。')
    finally:
        keyboard.unhook_all()
        print('清理完成，程式結束。')

if __name__ == '__main__':
    create_login_window()
