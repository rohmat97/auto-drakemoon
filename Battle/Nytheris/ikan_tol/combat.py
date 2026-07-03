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

def has_non_black_in_region(dm, x1, y1, x2, y2, direction_name, threshold=0.015):
    '''
    Use non-black pixel ratio to determine if there are monsters in the region
    threshold: Non-black pixel ratio threshold, default 1.5%
    '''
    non_black_count = 0
    total_points = 0
    step = 2
    get_color = dm.GetColor  # Local reference cache for faster loop execution
    for py in range(y1, y2 + 1, step):
        for px in range(x1, x2 + 1, step):
            color = get_color(px, py)
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
    for key in [50, 51, 52, 53, 54]:
        dm.KeyPress(key)
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
    dm.MoveTo(750, 625)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
   

def strategy_east_west(dm):
    dm.MoveTo(9, 371)
    time.sleep(0.66)
    dm.MoveTo(511, 341)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(200, 358)
    dm.Delay(50)
    dm.KeyDown(37)
    dm.Delay(50)
    dm.KeyUp(37)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_east_north(dm):
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
    dm.MoveTo(582, 50)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_south_east(dm):
    dm.MoveTo(487, 20)
    time.sleep(0.53)
    dm.MoveTo(457, 372)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(803, 504)
    dm.Delay(50)
    dm.MoveTo(904, 406)
    dm.Delay(50)
    # press arrow right 
    for i in range(2):
        dm.KeyDown(39)
        dm.Delay(50)
        dm.KeyUp(39)
        dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
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
    dm.MoveTo(164, 400)
    dm.Delay(50)
    dm.KeyDown(37)
    dm.Delay(50)
    dm.KeyUp(37)
    dm.Delay(50)
    dm.KeyDown(37)
    dm.Delay(50)
    dm.KeyUp(37)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_south_north(dm):
    dm.MoveTo(487, 10)
    time.sleep(0.60)
    dm.MoveTo(372, 454)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(557, 154)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_west_east(dm):
    dm.MoveTo(1022, 352)
    time.sleep(0.66)
    dm.MoveTo(425, 342)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(850, 325)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyDown(39) 
    dm.Delay(50)
    dm.KeyUp(39)
    dm.Delay(50)
       
    execute_skill_loop(dm)
    dm.Delay(50)
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
    dm.MoveTo(200, 646)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_west_north(dm):
    dm.MoveTo(1022, 352)
    time.sleep(0.77)
    dm.MoveTo(353, 342)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(123, 147)
    dm.Delay(50)
    dm.MoveTo(100, 100)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_north_east(dm):
    dm.MoveTo(480, 762)
    time.sleep(0.66)
    dm.MoveTo(667, 303)
    dm.Delay(50)
    dm.MoveTo(623, 74)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(1022, 128)
    time.sleep(0.15)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.MoveTo(725, 251)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_north_south(dm):
    dm.MoveTo(480, 762)
    time.sleep(0.66)
    dm.MoveTo(372, 372)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(478, 625)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_north_west(dm):
    dm.MoveTo(483, 888)
    time.sleep(0.50)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(80, 80)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    
def strategy_WestSouth_NorthEast(dm):
    dm.MoveTo(1024, 0)
    time.sleep(0.1)
    dm.MoveTo(780, 250)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(980, 50)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    
def strategy_NorthEast_WestSouth(dm):
    dm.MoveTo(0, 800)
    time.sleep(0.25)
    dm.MoveTo(372, 302)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(150, 625)
    dm.Delay(50)
    execute_skill_loop(dm)
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
