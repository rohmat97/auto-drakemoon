# combat.py

import time

def check_revive(dm, is_paused_func):
    if is_paused_func():
        return False
    (r, x, y) = dm.FindPic(546, 420, 578, 448, 'revivedrake.bmp', '050505', 0.8, 0)
    if x > 0:
        print('Main character revived successfully')
        dm.MoveTo(x, y)
        dm.Delay(100)
        dm.LeftClick()
        dm.Delay(200)
        return True
    return False



def map_vector_to_direction(dx, dy):
    """Map a 2D minimap vector to a cardinal direction (North, South, East, West).
    Accounts for the 2.2:1 aspect ratio of the minimap diamond."""
    scaled_dy = dy * 2.2
    if abs(scaled_dy) >= abs(dx):
        return 'North' if dy < 0 else 'South'
    else:
        return 'East' if dx > 0 else 'West'

def get_minimap_positions(dm, detected_formation=None):
    """Scan the minimap area using PIL for extreme speed."""
    import os
    try:
        from PIL import Image
    except ImportError:
        print("PIL is not installed. Minimap detection requires PIL for speed.")
        return None, None, None, None

    # Capture minimap area to memory/file
    temp_path = os.path.join(dm.GetBasePath(), 'temp_minimap.bmp')
    dm.Capture(0, 675, 259, 767, temp_path)
    
    if not os.path.exists(temp_path):
        return None, None, None, None
        
    try:
        img = Image.open(temp_path)
        img.load()
    except Exception:
        return None, None, None, None

    dots = 0
    step = 2
    for y in range(0, img.height, step):
        for x in range(0, img.width, step):
            r, g, b = img.getpixel((x, y))
            br = max(r, g, b)
            
            is_dot = False
            if br > 230:
                is_dot = True
            elif r > 120 and g < 90 and b < 90:
                is_dot = True
            elif g > r + 15 or b > r + 15:
                is_dot = True
            
            if is_dot:
                dots += 1
                if dots > 10:
                    return 1, 1, 1, 1

    return None, None, None, None

def get_monster_direction(dm, detected_formation=None):
    '''
    Captures the minimap once, and checks the pre-defined bounding boxes for monster dots.
    This completely avoids K-Means clustering, preventing the minimap camera rectangle from ruining detection.
    Returns the direction name (e.g. 'East') or None if not found.
    '''
    import os
    try:
        from PIL import Image
    except ImportError:
        return None

    # Capture minimap area to memory/file
    temp_path = os.path.join(dm.GetBasePath(), 'temp_minimap.bmp')
    dm.Capture(0, 675, 259, 767, temp_path)
    
    if not os.path.exists(temp_path):
        return None
        
    try:
        img = Image.open(temp_path)
        img.load()
    except Exception:
        return None

    from config import MONSTER_CHECKS, MONSTER_DIRECTION_REGIONS
    valid_dirs = MONSTER_CHECKS.get(detected_formation, ['East', 'South', 'West', 'North'])
    
    best_dir = None
    max_dots = 0
    
    for d in valid_dirs:
        reg = MONSTER_DIRECTION_REGIONS[d]
        x1, y1, x2, y2 = reg
        
        dots_in_region = 0
        for y in range(y1 - 675, y2 - 675 + 1):
            for x in range(x1, x2 + 1):
                if x < 0 or x >= img.width or y < 0 or y >= img.height:
                    continue
                    
                r, g, b = img.getpixel((x, y))
                br = max(r, g, b)
                
                is_dot = False
                if br > 230:
                    is_dot = True
                elif r > 120 and g < 90 and b < 90:
                    is_dot = True
                elif g > r + 15 or b > r + 15:
                    is_dot = True
                    
                if is_dot:
                    dots_in_region += 1
                    
        if dots_in_region > max_dots:
            max_dots = dots_in_region
            best_dir = d

    if best_dir:
        print(f'   └ Target closest to monster cluster: {best_dir} ({max_dots} dots)')
        return best_dir
        
    return None

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
    dm.KeyPress(52)
    dm.Delay(50)
    dm.KeyPress(69)
    dm.Delay(50)
    dm.KeyPress(69)
    dm.Delay(50)
    dm.KeyPress(53)
    dm.Delay(50)
    dm.KeyPress(69)
    dm.Delay(50)
    dm.KeyPress(69)
    dm.Delay(50)
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
    dm.KeyPress(52)
    dm.Delay(50)
    dm.KeyPress(69)
    dm.Delay(50)
    dm.KeyPress(69)
    dm.Delay(50)
    dm.KeyPress(53)
    dm.Delay(50)
    dm.KeyPress(69)
    dm.Delay(50)
    dm.KeyPress(69)
    dm.Delay(50)

# Battle Strategies mapping (direction, monster_dir) -> action function

def strategy_east_south(dm):
    dm.MoveTo(9, 371)
    time.sleep(0.53)
    dm.MoveTo(511, 341)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(904, 472)
    dm.Delay(50)
    dm.MoveTo(500, 450)
    dm.Delay(200)
    dm.KeyDown(40)
    time.sleep(0.3)
    dm.KeyUp(40)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(500)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_east_west(dm):
    dm.MoveTo(12, 397)
    time.sleep(0.75)
    dm.MoveTo(514, 367)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(103, 350)
    dm.Delay(50)
    dm.KeyDown(37)
    time.sleep(0.15)
    dm.KeyUp(37)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(500)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_east_north(dm):
    for _ in range(4):
        dm.KeyPress(27)
        dm.Delay(100)
    # dm.MoveTo(9, 371)
    # time.sleep(0.53)
    # dm.MoveTo(511, 341)
    # dm.Delay(50)
    # dm.KeyPress(81)
    # dm.Delay(50)
    # dm.KeyPress(87)
    # dm.Delay(50)
    # dm.MoveTo(954, 223)
    # dm.Delay(50)
    # dm.MoveTo(562, 9)
    # dm.Delay(50)
    # dm.MoveTo(600, 50)
    # dm.Delay(50)
    # execute_skill_loop(dm)
    # dm.Delay(500)
    # execute_skill_loop(dm)
    # dm.Delay(50)
   

def strategy_south_east(dm):
    dm.MoveTo(487, 10)
    time.sleep(0.53)
    dm.MoveTo(457, 372)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(803, 504)
    dm.Delay(50)
    dm.MoveTo(1000, 478)
    time.sleep(0.33)
    dm.MoveTo(150, 376)
    dm.Delay(50)
    dm.KeyDown(39)
    time.sleep(0.35)
    dm.KeyUp(39)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(500)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_south_west(dm):
    dm.MoveTo(487, 10)
    time.sleep(0.53)
    dm.MoveTo(457, 372)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(164, 449)
    dm.Delay(50)
    dm.MoveTo(8, 449)
    time.sleep(0.15)
    dm.MoveTo(110, 290)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(500)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_south_north(dm):
    dm.MoveTo(487, 10)
    time.sleep(0.66)
    dm.MoveTo(497, 373)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(477, 124)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(500)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_west_east(dm):
    dm.MoveTo(1022, 352)
    time.sleep(0.66)
    dm.MoveTo(353, 342)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(623, 375)
    dm.Delay(50)
    dm.KeyDown(39)
    time.sleep(0.4)
    dm.KeyUp(39)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(500)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_west_south(dm):
    dm.MoveTo(1022, 352)
    time.sleep(0.66)
    dm.MoveTo(353, 442)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(12, 646)
    time.sleep(0.30)
    dm.MoveTo(350, 646)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(500)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_west_north(dm):
    dm.MoveTo(1022, 352)
    time.sleep(0.66)
    dm.MoveTo(353, 342)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(123, 147)
    dm.Delay(50)
    dm.MoveTo(204, 9)
    dm.Delay(60)
    dm.MoveTo(254, 46)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(500)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_north_east(dm):
    dm.MoveTo(480, 762)
    time.sleep(0.66)
    dm.MoveTo(667, 303)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(923, 74)
    dm.Delay(50)
    dm.MoveTo(1006, 128)
    time.sleep(0.33)
    dm.MoveTo(777, 301)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(500)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_north_south(dm):
    dm.MoveTo(480, 762)
    time.sleep(0.73)
    dm.MoveTo(667, 303)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(508, 600)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(500)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_north_west(dm):
    dm.MoveTo(480, 759)
    time.sleep(0.66)
    dm.MoveTo(570, 229)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(201, 80)
    dm.Delay(50)
    dm.MoveTo(40, 100)
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
    dm.Delay(500)
    execute_skill_loop(dm)
    dm.Delay(50)

STRATEGIES = {
    ('East', 'South'): strategy_east_south,
    ('East', 'West'): strategy_east_west,
    ('East', 'North'): strategy_east_north,
    ('South', 'East'): strategy_south_east,
    ('South', 'West'): strategy_south_west,
    ('South', 'North'): strategy_south_north,
    ('West', 'East'): strategy_west_east,
    ('West', 'South'): strategy_west_south,
    ('West', 'North'): strategy_west_north,
    ('North', 'East'): strategy_north_east,
    ('North', 'South'): strategy_north_south,
    ('North', 'West'): strategy_north_west,
}

def execute_battle_strategy(dm, direction, monster_dir):
    strategy = STRATEGIES.get((direction, monster_dir))
    if strategy:
        strategy(dm)
        return True
    return False
