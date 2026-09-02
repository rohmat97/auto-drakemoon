# combat.py
import time

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
    dm.Delay(50)
    pan_camera(dm, 371, 767, 0.10)
    dm.Delay(50)
    dm.MoveTo(750, 375)
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
    dm.MoveTo(725, 250)
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
    pan_camera(dm, 487, 0, 0.375)
    dm.Delay(50)
    pan_camera(dm, 8, 449, 0.25)
    dm.MoveTo(500, 600)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_south_north(dm):
    pan_camera(dm, 487, 0, 0.60)
    dm.MoveTo(425, 525)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_west_east(dm):
    pan_camera(dm, 1023, 352, 0.6)
    dm.MoveTo(225, 425)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_west_south(dm):
    pan_camera(dm, 1023, 352, 0.35)
    dm.Delay(50)
    pan_camera(dm, 275, 767, 0.25)
    dm.MoveTo(150, 325)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_west_north(dm):
    pan_camera(dm, 1023, 352, 0.30)
    dm.Delay(50)
    pan_camera(dm, 250, 0, 0.28)
    dm.MoveTo(250, 450)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_north_east(dm):
    pan_camera(dm, 480, 767, 0.35)
    pan_camera(dm, 1023, 128, 0.28)
    dm.MoveTo(550, 301)
    dm.Delay(50)
    execute_skill_loop(dm)
    dm.Delay(50)

def strategy_north_south(dm):
    pan_camera(dm, 440, 767, 0.45)
    dm.Delay(50)
    dm.MoveTo(550, 400)
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

def execute_battle_strategy3(dm, direction, monster_dir):
    strategy = STRATEGIES.get((direction, monster_dir))
    if strategy:
        strategy(dm)
        return True
    return False

