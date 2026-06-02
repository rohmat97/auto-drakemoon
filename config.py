# config.py - Shared Configuration and State

AUTHORIZED_HARDWARE_ID = '3528f4a89e829d46405972781ac4863f3b2916bb9f03e84a5a6b7a3eca6e2d25'
paused = False

FORMATION_REGIONS = {
    'East': [
        (952, 166, 997, 283),
        (988, 463, 1005, 489)],
    'South': [
        (943, 487, 1001, 523),
        (26, 520, 69, 584)],
    'West': [
        (16, 131, 36, 191),
        (17, 586, 51, 649)],
    'North': [
        (938, 166, 1007, 274),
        (34, 189, 120, 306)]
}

MONSTER_DIRECTION_REGIONS = {
    'East': (175, 739, 192, 748),
    'South': (120, 756, 139, 765),
    'West': (79, 740, 86, 754),
    'North': (124, 715, 139, 730)
}

MONSTER_CHECKS = {
    'East': ['South', 'West', 'North'],
    'South': ['East', 'West', 'North'],
    'West': ['East', 'South', 'North'],
    'North': ['East', 'South', 'West']
}
