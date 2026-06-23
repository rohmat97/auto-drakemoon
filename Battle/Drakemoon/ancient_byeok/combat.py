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
    dm.MoveTo(904, 472)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(600, 450)
    dm.Delay(200)
    dm.KeyDown(40)
    time.sleep(0.3)
    dm.KeyUp(40)
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
    dm.MoveTo(50, 358)
    dm.Delay(50)
    dm.KeyDown(37)
    time.sleep(0.15)
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
    dm.MoveTo(462, 50)
    dm.Delay(50)
    # press right 2 times arrow up 1 time
    dm.KeyDown(39)
    time.sleep(0.1)
    dm.KeyUp(39)
    dm.Delay(50)
    dm.KeyDown(39)
    time.sleep(0.1)
    dm.KeyUp(39)
    dm.Delay(50)
    dm.KeyDown(38)
    time.sleep(0.1)
    dm.KeyUp(38)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_south_east(dm):
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
    dm.MoveTo(250, 376)
    dm.Delay(50)
    dm.KeyDown(39)
    time.sleep(0.35)
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
    dm.MoveTo(164, 449)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(8, 449)
    time.sleep(0.33)
    dm.MoveTo(50, 376)
    dm.Delay(50)
    dm.KeyDown(39)
    time.sleep(0.1)
    dm.KeyUp(39)
    dm.Delay(50)
    dm.KeyDown(39)
    time.sleep(0.1)
    dm.KeyUp(39)
    dm.Delay(50)
    dm.KeyDown(40)
    time.sleep(0.1)
    dm.KeyUp(40)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
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
    dm.MoveTo(497, 164)
    dm.Delay(50)
    # press arrow up 2 times
    dm.KeyDown(38)
    time.sleep(0.1)
    dm.KeyUp(38)
    dm.Delay(50)
    dm.KeyDown(38)
    time.sleep(0.1)
    dm.KeyUp(38)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_west_east(dm):
    dm.MoveTo(1022, 352)
    time.sleep(0.66)
    dm.MoveTo(525, 342)
    dm.Delay(50)
    dm.MoveTo(425, 375)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.KeyDown(39)
    time.sleep(0.4)
    dm.KeyUp(39)
    dm.MoveTo(675, 425)
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
    dm.MoveTo(180, 646)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    # press arrow down 1 times
    dm.KeyDown(40)
    time.sleep(0.1)
    dm.KeyUp(40)
    dm.Delay(50)
    # add press arrow right 2 times arrow bottom 1 times
    time.sleep(0.1)
    dm.KeyUp(39)
    dm.Delay(50)
    dm.KeyDown(40)
    time.sleep(0.1)
    dm.KeyUp(40)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_west_north(dm):
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
    dm.MoveTo(250, 5)
    time.sleep(0.33)
    dm.MoveTo(350, 100)
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
    dm.MoveTo(923, 74)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(1022, 128)
    time.sleep(0.33)
    dm.MoveTo(755, 200)
    dm.Delay(50)
    # press right 1 times
    dm.KeyDown(39)
    time.sleep(0.1)
    dm.KeyUp(39)
    dm.Delay(50)
    # press bottom 1 times
    dm.KeyDown(40)
    time.sleep(0.1)
    dm.KeyUp(40)
    dm.Delay(50)
    dm.KeyDown(40)
    time.sleep(0.1)
    dm.KeyUp(40)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_north_south(dm):
    dm.MoveTo(480, 762)
    time.sleep(0.66)
    dm.MoveTo(667, 303)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.MoveTo(488, 571)
    dm.Delay(50)
    dm.KeyDown(40)
    time.sleep(0.1)
    dm.KeyUp(40)
    dm.Delay(50)
    dm.KeyDown(40)
    time.sleep(0.1)
    dm.KeyUp(40)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_north_west(dm):
    dm.MoveTo(483, 788)
    time.sleep(0.66)
    dm.MoveTo(570, 229)
    dm.Delay(50)
    dm.MoveTo(201, 80)
    dm.Delay(50)
    dm.MoveTo(50, 150)
    dm.Delay(50)
    dm.KeyPress(81)
    dm.Delay(50)
    dm.KeyPress(87)
    dm.Delay(50)
    dm.KeyDown(40)
    time.sleep(0.1)
    dm.KeyUp(40)
    dm.Delay(50)
    dm.KeyDown(37)
    time.sleep(0.1)
    dm.KeyUp(37)
    dm.Delay(50)
    # press left 2 times
    dm.KeyDown(37)
    time.sleep(0.1)
    dm.KeyUp(37)
    dm.Delay(50)
    dm.KeyDown(37)
    time.sleep(0.1)
    dm.KeyUp(37)
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
}

def execute_battle_strategy(dm, direction, monster_dir):
    strategy = STRATEGIES.get((direction, monster_dir))
    if strategy:
        strategy(dm)
        return True
    return False
