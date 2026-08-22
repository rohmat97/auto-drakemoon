# combat.py
import time

def check_revive(dm, is_paused_func):
    if is_paused_func():
        return False
    (r, x, y) = dm.FindPic(0, 0, 1024, 768, 'revivedrake.bmp', '202020', 0.7, 0)
    if x > 0:
        print('Main character revived successfully')
        dm.MoveTo(x, y)
        dm.Delay(100)
        dm.LeftClick()
        dm.Delay(200)
        return True
    return False

def is_pixel_active(color_hex, dark_threshold=30):
    '''
    Check if a color is a non-black / non-dark pixel.
    Minimap background/fog in Gersang is black ('000000') or dark gray ('080808', etc.).
    Monster and mercenary dots are bright colored pixels (Red, Yellow, Blue, etc.).
    '''
    if not color_hex or len(color_hex) < 6:
        return False
    if color_hex in ('000000', '080808', '050505', '070707', '0a0a0a', '0b0b0b'):
        return False
    try:
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)
        return r > dark_threshold or g > dark_threshold or b > dark_threshold
    except ValueError:
        return False

def has_non_black_in_region(dm, x1, y1, x2, y2, direction_name, threshold=0.015, step=2):
    '''
    Use non-black pixel ratio to determine if there are monsters in the region
    threshold: Non-black pixel ratio threshold, default 1.5%
    step: Pixel sampling step size (default: 2 for good precision)
    '''
    non_black_count = 0
    total_points = 0
    get_color = dm.GetColor  # Local reference cache for faster loop execution
    for py in range(y1, y2 + 1, step):
        for px in range(x1, x2 + 1, step):
            color = get_color(px, py)
            total_points += 1
            if is_pixel_active(color):
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
    (r1, x1, y1) = dm.FindPic(region1[0], region1[1], region1[2], region1[3], '080808.bmp', '050505', 0.975, 0)
    (r2, x2, y2) = dm.FindPic(region2[0], region2[1], region2[2], region2[3], '080808.bmp', '050505', 0.975, 0)
    if x1 > 0 and x2 > 0:
        return True
    return False

def send_key(dm, key, hold_ms=35, delay_after_ms=35):
    '''Reliably send a key press in background mode.'''
    dm.KeyDown(key)
    dm.Delay(hold_ms)
    dm.KeyUp(key)
    dm.Delay(delay_after_ms)

def pan_camera(dm, x, y, duration_sec):
    '''
    Smoothly pan the camera in background mode by streaming MoveTo
    and clamping coordinates within the 1024x768 game screen.
    '''
    cx = max(0, min(1023, int(x)))
    cy = max(0, min(767, int(y)))
    end_time = time.time() + duration_sec
    while time.time() < end_time:
        dm.MoveTo(cx, cy)
        dm.Delay(25)

def execute_skill_loop(dm):
    for key in [50, 51, 52, 53, 54, 55]:
        send_key(dm, key, 35, 35)
        send_key(dm, 69, 35, 35)
        send_key(dm, 69, 35, 35)

def initial_call(dm):
    send_key(dm, 187, 35, 35)  # =
    send_key(dm, 82, 35, 35)   # R
    send_key(dm, 69, 35, 35)   # E
    send_key(dm, 69, 35, 35)   # E

def initiation_battle(dm):
    dm.Delay(35)
    send_key(dm, 81, 35, 35)   # Q
    send_key(dm, 87, 35, 35)   # W
    dm.Delay(35)

# Battle Strategies mapping (direction, monster_dir) -> action function

def strategy_east_south(dm):
    pan_camera(dm, 9, 371, 0.35)
    pan_camera(dm, 371, 767, 0.10)
    dm.MoveTo(750, 500)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_east_west(dm):
    pan_camera(dm, 9, 371, 0.45)
    dm.MoveTo(155, 358)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_east_north(dm):
    pan_camera(dm, 9, 371, 0.43)
    dm.MoveTo(511, 341)
    dm.Delay(50)
    pan_camera(dm, 625, 0, 0.15)
    dm.MoveTo(825, 190)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_south_east(dm):
    pan_camera(dm, 487, 0, 0.43)
    dm.Delay(50)
    pan_camera(dm, 1023, 322, 0.25)
    dm.MoveTo(580, 600)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_south_west(dm):
    pan_camera(dm, 487, 0, 0.45)
    dm.Delay(50)
    pan_camera(dm, 8, 449, 0.25)
    dm.MoveTo(500, 600)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_south_north(dm):
    pan_camera(dm, 487, 0, 0.60)
    dm.MoveTo(497, 425)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_west_east(dm):
    pan_camera(dm, 1023, 352, 0.65)
    dm.MoveTo(450, 375)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_west_south(dm):
    pan_camera(dm, 1023, 352, 0.35)
    dm.Delay(50)
    pan_camera(dm, 275, 767, 0.25)
    dm.MoveTo(225, 305)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_west_north(dm):
    pan_camera(dm, 1023, 352, 0.30)
    dm.Delay(50)
    pan_camera(dm, 250, 0, 0.28)
    dm.MoveTo(250, 350)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_north_east(dm):
    pan_camera(dm, 480, 767, 0.35)
    pan_camera(dm, 1023, 128, 0.28)
    dm.MoveTo(675, 301)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_north_south(dm):
    pan_camera(dm, 440, 767, 0.45)
    dm.Delay(50)
    dm.MoveTo(628, 500)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_north_west(dm):
    pan_camera(dm, 483, 767, 0.40)
    dm.Delay(50)
    pan_camera(dm, 0, 150, 0.25)
    dm.MoveTo(500, 125)
    dm.Delay(50)
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

