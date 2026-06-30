# config.py

# Authorization configurations
AUTHORIZED_HARDWARE_ID = '3528f4a89e829d46405972781ac4863f3b2916bb9f03e84a5a6b7a3eca6e2d25'

# Game configurations
GAME_TITLE = 'Gersang'
DM_REG_KEY = 'hkaiscript44c3dffb21a432409f0d422e1a8dcc35'
DM_REG_CODE = 'sqDvF'

# Battle regions and configurations
FORMATION_REGIONS = {
    'East': [(949, 140, 994, 257), (985, 437, 1002, 463)],
    'South': [(940, 461, 998, 497), (23, 494, 66, 558)],
    'West': [(13, 105, 33, 165), (14, 560, 48, 623)],
    'North': [(935, 140, 1004, 248), (31, 163, 117, 280)]
}

MONSTER_DIRECTION_REGIONS = {
    'East': (172, 713, 189, 722),
    'South': (117, 730, 136, 739),
    'West': (76, 714, 83, 728),
    'North': (121, 689, 136, 704),
}

MONSTER_CHECKS = {
    'East': ['South', 'West', 'North'],
    'South': ['East', 'West', 'North'],
    'West': ['East', 'South', 'North'],
    'North': ['East', 'South', 'West']
}
