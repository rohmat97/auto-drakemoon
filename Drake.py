# Drake.py - Entry Point and Main Automation Loop

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import time
import keyboard
import gc
from PyGameAuto.Dm import RegDm
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

import config
import utils


def create_login_window():
    
    def on_start():
        run_main_script()

    on_start()


def run_main_script():
    utils.check_hardware_authorization()
    dm = RegDm.reg()
    dm.SetShowErrorMsg(0)
    ret = dm.reg('hkaiscript44c3dffb21a432409f0d422e1a8dcc35', 'sqDvF')
    print('DaMo Registration Result:', ret)
    print('DaMo Version:', dm.ver())
    utils.move_game_window(dm)
    
    if getattr(sys, 'frozen', None):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
        print('Current Path:', basedir)
    path = os.path.join(basedir, 'Resource')
    print('Resource Path:', path)
    dm.setPath(path)
    
    config.paused = False
    
    def on_f10_press(event):
        if event.name == 'f10':
            config.paused = not config.paused
            if config.paused:
                print('All commands paused, press F10 to resume...')
            else:
                print('All commands resumed...')

    keyboard.on_press_key('f10', on_f10_press)
    
    try:
        try:
            while True:
                gc.collect()
                utils.check_revive(dm)
                if config.paused:
                    time.sleep(0.5)
                    continue
                
                utils.check_and_refill_satiety(dm)
                
                if utils.is_satiety_depleted(dm):
                    continue
                
                utils.try_engage_monster(dm)
                
                r_battle, x_battle, y_battle = dm.FindPic(962, 692, 1019, 773, 'battle.bmp', '050505', 0.8, 0)
                if x_battle > 0:
                    print('Entered battle screen')
                    action_executed = False
                    
                    while True:
                        gc.collect()
                        utils.check_revive(dm)
                        if config.paused:
                            time.sleep(1)
                            continue
                        
                        if action_executed:
                            print('Pressing Esc 4 times to exit')
                            for _ in range(4):
                                dm.KeyPress(27)
                                dm.Delay(70)
                            time.sleep(3)
                            break
                            
                        for direction, regions in config.FORMATION_REGIONS.items():
                            if action_executed:
                                break
                                
                            if utils.check_formation(dm, regions[0], regions[1]):
                                print(f'Detected formation position: {direction}')
                                time.sleep(0.1)
                                
                                for monster_dir in config.MONSTER_CHECKS[direction]:
                                    x1, y1, x2, y2 = config.MONSTER_DIRECTION_REGIONS[monster_dir]
                                    if utils.has_non_black_in_region(dm, x1, y1, x2, y2, monster_dir, threshold=0.03):
                                        print(f'Executing command → Formation:{direction} | Monster:{monster_dir}')
                                        utils.execute_battle_tactic(dm, direction, monster_dir)
                                        action_executed = True
                                        break
                                        
                        r_battle, x_battle, y_battle = dm.FindPic(962, 692, 1019, 773, 'battle.bmp', '050505', 0.8, 0)
                        if x_battle <= 0:
                            print('Battle screen ended')
                            utils.check_revive(dm)
                            utils.recover_dead_mercenaries_if_needed(dm)
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
