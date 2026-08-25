# window_manager.py

import sys
from tkinter import messagebox
from config import GAME_TITLE

def move_game_window(dm):
    hwnd = dm.FindWindow('', GAME_TITLE)
    if hwnd == 0:
        messagebox.showerror('Error', f"Game window '{GAME_TITLE}' not found, please start the game first!")
        sys.exit(1)
    # dm.MoveWindow(hwnd, 0, 0)
    print(f"Moved '{GAME_TITLE}' window to top-left corner (0, 0)")
    dm.Delay(500)
    return hwnd

def bind_game_window(dm, hwnd):
    dm_ret = dm.BindWindowEx(
        hwnd, 'gdi', 
        'dx.mouse.position.lock.api|dx.mouse.position.lock.message|dx.mouse.clip.lock.api|dx.mouse.input.lock.api|dx.mouse.state.api|dx.mouse.api|dx.mouse.cursor', 
        'dx.keypad.input.lock.api|dx.keypad.state.api|dx.keypad.api|dx.keypad.raw.input', 
        '', 101
    )
    return dm_ret
