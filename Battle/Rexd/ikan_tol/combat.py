# combat.py
import time

def check_revive(dm, is_paused_func=None):
    if is_paused_func and is_paused_func():
        return False
    (r, x, y) = dm.FindPic(0, 0, 1024, 768, 'revivedrake.bmp', '202020', 0.8, 0)
    if x > 0:
        print(f'[Revival] ⚠️ Main character revive button OK found at ({x}, {y})!')
        dm.MoveTo(x, y)
        dm.Delay(100)
        dm.LeftClick()
        dm.Delay(300)
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

_MONSTER_REGION_CACHE = {}

def has_non_black_in_region(dm, x1, y1, x2, y2, direction_name, threshold=0.015, step=2):
    '''
    Use non-black pixel ratio to determine if there are monsters in the region.
    Points and thresholds are precomputed and cached in memory.
    Uses early-exit as soon as threshold is met to avoid unnecessary COM calls.
    '''
    cache_key = (x1, y1, x2, y2, step, threshold)
    if cache_key not in _MONSTER_REGION_CACHE:
        pts = tuple((px, py) for py in range(y1, y2 + 1, step) for px in range(x1, x2 + 1, step))
        total_points = len(pts)
        min_required = max(1, int(total_points * threshold))
        _MONSTER_REGION_CACHE[cache_key] = (pts, min_required, total_points)
    else:
        pts, min_required, total_points = _MONSTER_REGION_CACHE[cache_key]

    if total_points == 0:
        return False

    non_black_count = 0
    get_color = dm.GetColor  # Local reference cache for faster loop execution
    for px, py in pts:
        color = get_color(px, py)
        if is_pixel_active(color):
            non_black_count += 1
            if non_black_count >= min_required:
                if direction_name:
                    print(f'''   └ {direction_name:4} Region ({x1},{y1})-({x2},{y2}) → [Monsters Found] (Early exit: {non_black_count}/{total_points})''')
                return True

    return False

def check_formation(dm, region1, region2):
    (r1, x1, y1) = dm.FindPic(region1[0], region1[1], region1[2], region1[3], '080808.bmp', '050505', 0.975, 0)
    (r2, x2, y2) = dm.FindPic(region2[0], region2[1], region2[2], region2[3], '080808.bmp', '050505', 0.975, 0)
    if x1 > 0 and x2 > 0:
        return True
    return False

WIDE_MAP_IMAGES_DEFAULT = '|'.join(
    [rf'tomb\wide_map{i}.bmp' for i in range(1, 5)] +
    [rf'tomb\wide_map{i}_{s}.bmp' for i in range(1, 5) for s in range(1, 4)]
)

def check_wide_map(dm, pic_names=WIDE_MAP_IMAGES_DEFAULT, sim=0.75):
    '''
    Check if the current battle map is a wide map by searching for wide map landmark images.
    Returns True if found, False otherwise.
    '''
    (r, x, y) = dm.FindPic(0, 0, 1024, 768, pic_names, '101010', sim, 0)
    if x > 0 and y > 0:
        pic_list = pic_names.split('|')
        detected_asset = pic_list[r] if 0 <= r < len(pic_list) else 'landmark'
        print(f'[Wide Map] Detected {detected_asset} at ({x}, {y})')
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
    for key in [50, 51, 52, 53, 54]:
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
    pan_camera(dm, 9, 371, 0.4)
    dm.Delay(50)
    pan_camera(dm, 371, 767, 0.4)
    dm.Delay(50)
    dm.MoveTo(975, 150)
    dm.Delay(50)
    initiation_battle(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_east_west(dm):
    pan_camera(dm, 9, 371, 0.18)
    dm.Delay(50)
    initiation_battle(dm)
    dm.Delay(50)
    dm.MoveTo(475, 375)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_east_north(dm):
    # send_key(dm, 27, 35, 35)
    # dm.Delay(200)
    # send_key(dm, 27, 35, 35)
    pan_camera(dm, 9, 371, 0.15)
    dm.Delay(50)
    pan_camera(dm, 625, 0, 0.1)
    dm.Delay(50)
    initiation_battle(dm)
    dm.Delay(50)
    dm.MoveTo(525, 550)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_south_east(dm):
    pan_camera(dm, 487, 0, 0.25)
    dm.Delay(50)
    pan_camera(dm, 1023, 322, 0.15)
    dm.Delay(50)
    dm.MoveTo(525, 500)
    dm.Delay(50)
    initiation_battle(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_south_west(dm):
    pan_camera(dm, 487, 0, 0.3)
    dm.Delay(50)
    pan_camera(dm, 8, 449, 0.25)
    dm.Delay(50)
    dm.MoveTo(650, 500)
    dm.Delay(50)
    initiation_battle(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_south_north(dm):
    pan_camera(dm, 487, 0, 0.5)
    dm.Delay(50)
    dm.MoveTo(475, 475)
    dm.Delay(50)
    initiation_battle(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_west_east(dm):
    pan_camera(dm, 1023, 352, 0.35)
    dm.Delay(50)
    dm.MoveTo(500, 375)
    dm.Delay(50) 
    initiation_battle(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_west_south(dm):
    pan_camera(dm, 1023, 352, 0.25)
    dm.Delay(50)
    pan_camera(dm, 275, 767, 0.3)
    dm.Delay(50)
    dm.MoveTo(350, 275)
    dm.Delay(50)
    initiation_battle(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_west_north(dm):
    pan_camera(dm, 1023, 352, 0.25)
    dm.Delay(50)
    pan_camera(dm, 250, 10, 0.25)
    dm.Delay(50)
    dm.MoveTo(350, 550)
    dm.Delay(50)
    initiation_battle(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_north_east(dm):
    pan_camera(dm, 480, 767, 0.25)
    pan_camera(dm, 1023, 128, 0.10)
    dm.Delay(50)
    dm.MoveTo(725, 401)
    dm.Delay(50)
    initiation_battle(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_north_south(dm):
    pan_camera(dm, 440, 767, 0.5)
    dm.Delay(50)
    dm.MoveTo(475, 350)
    dm.Delay(50)
    initiation_battle(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_north_west(dm):
    pan_camera(dm, 483, 767, 0.25)
    dm.Delay(50)
    pan_camera(dm, 0, 150, 0.15)
    dm.Delay(50)
    dm.MoveTo(550, 225)
    dm.Delay(50)
    initiation_battle(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_WestSouth_NorthEast(dm):
    pan_camera(dm, 1023, 0, 0.20)
    dm.Delay(50)
    initiation_battle(dm)
    dm.Delay(50)
    dm.MoveTo(980, 50)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_NorthEast_WestSouth(dm):
    pan_camera(dm, 0, 767, 0.15)
    dm.Delay(50)
    dm.MoveTo(150, 625)
    dm.Delay(50)
    initiation_battle(dm)
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
    ('WestSouth', 'NorthEast'): strategy_WestSouth_NorthEast,
    ('NorthEast', 'WestSouth'): strategy_NorthEast_WestSouth,
}

def execute_battle_strategy(dm, direction, monster_dir):
    strategy = STRATEGIES.get((direction, monster_dir))
    if strategy:
        strategy(dm)
        return True
    return False


# Re-export global opposite monster detection from game_actions
try:
    from game_actions import (
        check_and_execute_opposite_monster,
        OPPOSITE_MONSTER_REGION,
        OPPOSITE_TARGET_POSITION,
        OPPOSITE_MONSTER_IMAGES,
        OPPOSITE_MONSTER_REGION_2,
        OPPOSITE_TARGET_POSITION_2,
        OPPOSITE_MONSTER_IMAGES_2,
    )
except ImportError:
    pass

