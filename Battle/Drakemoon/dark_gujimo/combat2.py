import time
from Battle.Drakemoon.dark_gujimo.combat import initiation_battle

def execute_skill_loop(dm):
    for key in [50, 51]:
        dm.KeyPress(key)
        dm.Delay(50)
        dm.KeyPress(69)
        dm.Delay(50)
        dm.KeyPress(69)
        dm.Delay(50)

def strategy_east_south(dm):
    dm.MoveTo(9, 371)
    time.sleep(0.45)
    dm.MoveTo(511, 341)
    dm.Delay(50)
    dm.MoveTo(904, 472)
    dm.Delay(50)
    initiation_battle(dm)
    dm.MoveTo(600, 250)
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
    time.sleep(0.60)
    dm.MoveTo(275, 358)
    initiation_battle(dm)
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
    initiation_battle(dm)
    dm.MoveTo(575, 50)
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
    initiation_battle(dm)
    dm.MoveTo(550, 476)
    dm.Delay(50)
    dm.KeyDown(39)
    time.sleep(0.35)
    dm.KeyUp(39)
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
    initiation_battle(dm)
    dm.MoveTo(8, 449)
    time.sleep(0.33)
    dm.MoveTo(600, 550)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_south_north(dm):
    dm.MoveTo(487, 10)
    time.sleep(0.70)
    dm.MoveTo(497, 373)
    dm.Delay(50)
    initiation_battle(dm)
    dm.MoveTo(525, 500)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_west_east(dm):
    dm.MoveTo(1022, 352)
    time.sleep(0.50)
    dm.MoveTo(525, 342)
    dm.Delay(50)
    dm.MoveTo(425, 375)
    dm.Delay(50)
    dm.KeyDown(39)
    time.sleep(0.4)
    dm.KeyUp(39)
    dm.MoveTo(225, 425)
    dm.Delay(50)
    initiation_battle(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_west_south(dm):
    dm.MoveTo(1022, 352)
    time.sleep(0.50)
    dm.MoveTo(353, 442)
    dm.Delay(50)
    dm.MoveTo(350, 646)
    dm.Delay(50)
    initiation_battle(dm)
    dm.KeyDown(40)
    dm.KeyUp(40)
    dm.Delay(50)
    dm.KeyDown(40)
    dm.KeyUp(40)
    dm.Delay(50)
    dm.KeyDown(40)
    dm.KeyUp(40)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_west_north(dm):
    dm.MoveTo(1022, 352)
    time.sleep(0.60)
    dm.MoveTo(353, 342)
    dm.Delay(50)
    dm.MoveTo(123, 147)
    dm.Delay(50)
    initiation_battle(dm)
    dm.MoveTo(250, 5)
    time.sleep(0.20)
    dm.MoveTo(50, 350)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_north_east(dm):
    dm.MoveTo(480, 762)
    time.sleep(0.50)
    dm.MoveTo(667, 303)
    dm.Delay(50)
    dm.MoveTo(923, 74)
    dm.Delay(50)
    dm.MoveTo(1022, 128)
    time.sleep(0.33)
    dm.MoveTo(700, 301)
    dm.Delay(50)
    initiation_battle(dm)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)
   

def strategy_north_south(dm):
    dm.MoveTo(480, 762)
    time.sleep(0.60)
    dm.Delay(50)
    dm.MoveTo(628, 425)
    dm.Delay(50)
    initiation_battle(dm)
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
    time.sleep(0.1)
    dm.MoveTo(225, 200)
    dm.Delay(50)
    initiation_battle(dm)
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

def execute_battle_strategy2(dm, direction, monster_dir):
    strategy = STRATEGIES2.get((direction, monster_dir))
    if strategy:
        strategy(dm)
        return True
    return False
