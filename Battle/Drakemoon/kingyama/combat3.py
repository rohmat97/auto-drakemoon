import time

def execute_skill_loop(dm):
    for key in [50, 51, 52, 53, 54,55]:
        dm.KeyPress(key)
        dm.Delay(50)
        dm.KeyPress(69)
        dm.Delay(50)
        dm.KeyPress(69)
        dm.Delay(50)


def strategy_east_south(dm):
    dm.MoveTo(9, 371)
    time.sleep(0.45)
    dm.MoveTo(371, 1022)
    time.sleep(0.10)
    dm.MoveTo(500, 640)

    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_east_west(dm):
    dm.MoveTo(9, 371)
    time.sleep(0.65)
    dm.MoveTo(125, 358)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_east_north(dm):
    dm.MoveTo(9, 371)
    time.sleep(0.53)
    dm.MoveTo(511, 341)
    dm.Delay(50)
    dm.MoveTo(625, 0)
    time.sleep(0.15)
    dm.MoveTo(625, 120)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_south_east(dm):
    dm.MoveTo(487, 10)
    time.sleep(0.53)
    dm.Delay(50)
    dm.MoveTo(1022, 322)
    time.sleep(0.33)
    dm.MoveTo(550, 550)

    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   
   

def strategy_south_west(dm):
    dm.MoveTo(487, 10)
    time.sleep(0.53)
    dm.Delay(50)
    dm.MoveTo(8, 449)
    time.sleep(0.33)
    dm.MoveTo(435, 525)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_south_north(dm):
    dm.MoveTo(487, 10)
    time.sleep(0.70)
    dm.MoveTo(525, 200)

    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_west_east(dm):
    dm.MoveTo(1022, 352)
    dm.Delay(850)
    dm.MoveTo(225, 375)

    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_west_south(dm):
    dm.MoveTo(1022, 352)
    time.sleep(0.50)
    dm.MoveTo(353, 442)
    dm.Delay(50)
    dm.MoveTo(275, 646)
    dm.Delay(50)
    dm.MoveTo(275, 1022)
    time.sleep(0.25)
    dm.MoveTo(225, 555)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_west_north(dm):
    dm.MoveTo(1022, 352)
    time.sleep(0.45)
    dm.Delay(50)
    dm.MoveTo(250, 5)
    time.sleep(0.33)
    dm.MoveTo(520, 350)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_north_east(dm):
    dm.MoveTo(480, 762)
    time.sleep(0.45)
    dm.MoveTo(1022, 128)
    time.sleep(0.33)
    dm.MoveTo(500, 301)

    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_north_south(dm):
    dm.MoveTo(480, 762)
    time.sleep(0.60)
    dm.Delay(50)
    dm.MoveTo(500, 625)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_north_west(dm):
    dm.MoveTo(483, 788)
    time.sleep(0.60)
    dm.MoveTo(570, 229)
    dm.Delay(50)
    dm.MoveTo(201, 80)
    dm.Delay(50)
    dm.MoveTo(0, 150)
    dm.Delay(250)
    dm.MoveTo(300, 125)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)


STRATEGIES2 = {
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

def execute_battle_strategy3(dm, direction, monster_dir):
    strategy = STRATEGIES2.get((direction, monster_dir))
    if strategy:
        strategy(dm)
        return True
    return False
