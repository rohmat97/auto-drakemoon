# capture_community.py — Capture the Community popup from the game window
# 
# HOW TO USE:
# 1. Make sure the game is running and the Community popup is visible on screen
# 2. Run this script: python capture_community.py
# 3. The script will capture the full screen and save it as full_screen.bmp
# 4. It will also show you the mouse coordinates so you can identify the region
# 5. After you identify the region, update CROP_REGION below and run again with --crop

import os
import sys
import time

# Add the project root for shared modules
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

from PyGameAuto.Dm import RegDm
from config import DM_REG_KEY, DM_REG_CODE
from window_manager import move_game_window, bind_game_window

def main():
    dm = RegDm.reg()
    ret = dm.reg(DM_REG_KEY, DM_REG_CODE)
    print('DM registration result:', ret)

    hwnd = move_game_window(dm)
    dm_ret = bind_game_window(dm, hwnd)
    if dm_ret != 1:
        print(f'Window binding failed, error code: {dm_ret}')
        sys.exit(1)
    print('Window binding successful')

    if getattr(sys, 'frozen', None):
        basedir = sys._MEIPASS
    else:
        basedir = _PROJECT_ROOT
    resource_dir = os.path.join(basedir, 'Resource')
    dm.setPath(resource_dir)

    # Step 1: Capture full screen for reference
    full_path = os.path.join(resource_dir, 'debug_fullscreen.bmp')
    dm.Capture(0, 0, 1024, 768, full_path)
    print(f'Full screen captured to: {full_path}')
    print('Open this image to find the exact coordinates of the Community popup.')
    print()

    # Step 2: If --crop flag is passed, crop a specific region
    if '--crop' in sys.argv:
        # ============================================================
        # EDIT THESE VALUES to match the Community popup location!
        # Format: (x1, y1, x2, y2)
        # Look at debug_fullscreen.bmp to find the coordinates
        # ============================================================
        x1, y1, x2, y2 = 0, 0, 200, 30  # <-- CHANGE THESE!
        
        crop_path = os.path.join(resource_dir, 'community.bmp')
        dm.Capture(x1, y1, x2, y2, crop_path)
        print(f'Community popup cropped and saved to: {crop_path}')
        print('Done! The community.bmp is ready to use.')
    else:
        print('Next steps:')
        print('1. Open debug_fullscreen.bmp in an image editor (Paint, etc.)')
        print('2. Find the Community popup and note its coordinates (x1, y1, x2, y2)')
        print('3. Edit CROP_REGION in this script with those coordinates')
        print('4. Run again with: python capture_community.py --crop')
        print()
        print('Or use the interactive mode below...')
        print()
        
        # Interactive mode: let user input coordinates
        try:
            coords = input('Enter crop coordinates as x1,y1,x2,y2 (or press Enter to skip): ').strip()
            if coords:
                parts = [int(c.strip()) for c in coords.split(',')]
                if len(parts) == 4:
                    x1, y1, x2, y2 = parts
                    crop_path = os.path.join(resource_dir, 'community.bmp')
                    dm.Capture(x1, y1, x2, y2, crop_path)
                    print(f'Community popup cropped and saved to: {crop_path}')
                    print('Done! The community.bmp is ready to use.')
                else:
                    print('Invalid format. Expected 4 numbers separated by commas.')
        except (ValueError, EOFError):
            print('Skipped interactive crop.')

    dm.UnBindWindow()
    print('Cleanup complete.')

if __name__ == '__main__':
    main()
