# config.py

# Authorization configurations
AUTHORIZED_HARDWARE_ID = '3528f4a89e829d46405972781ac4863f3b2916bb9f03e84a5a6b7a3eca6e2d25'

# Game configurations
GAME_TITLE = 'Gersang'
DM_REG_KEY = 'hkaiscript44c3dffb21a432409f0d422e1a8dcc35'
DM_REG_CODE = 'sqDvF'

# Battle regions and configurations
FORMATION_REGIONS = {
    'East': [(954, 154, 988, 242), (954, 154, 988, 242)],
    'South': [(940, 461, 998, 497), (23, 494, 66, 558)],
    'West': [(13, 105, 33, 165), (14, 560, 48, 623)],
    'North': [(935, 140, 1004, 248), (31, 163, 117, 280)],
    "NorthWest": [(379, 269, 663, 458), (379, 269, 663, 458)],
    # "NorthEast": [(361, 269, 645, 458), (361, 269, 645, 458)],
    "SouthEast": [(880, 280, 1005, 470), (980, 430, 1005, 470)],
    # "SouthWest": [(19, 430, 44, 470), (19, 430, 44, 470)]
}

MONSTER_DIRECTION_REGIONS = {
    'East': (145, 732, 165, 738),
    'South': (115, 761, 135, 767),
    'West': (85, 727, 105, 733),
    'North': (115, 702, 135, 708),
    "NorthWest": (95, 712, 115, 718),
    # "NorthEast": (135, 724, 155, 727),
    "SouthEast": (135, 742, 155, 748),
    # "SouthWest": (95, 754, 115, 757),
}

MONSTER_CHECKS = {
    'East': ['South', 'West', 'North',],
    'South': ['East', 'West', 'North',],
    'West': ['East', 'South', 'North',],
    'North': ['East', 'South', 'West',],
    "NorthWest": ["SouthEast"],
    # "NorthEast": ["SouthWest",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    "SouthEast": ["NorthWest"],
    # "SouthWest": ["NorthEast",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "NorthEastSouthWest": ["NorthWest", "SouthEast",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "NorthWestSouthEast": ["NorthEast", "SouthWest",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "EastSouthWest": ["NorthWest", "SouthEast",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "EastNorthWest": ["NorthEast", "SouthWest",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "SouthEastWest": ["NorthWest", "SouthWest",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "SouthWestWest": ["NorthEast", "SouthEast",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "NorthEastWest": ["NorthWest", "SouthEast",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "NorthWestWest": ["NorthEast", "SouthWest",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "NorthEastSouth": ["NorthWest", "SouthEast",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "NorthWestSouth": ["NorthEast", "SouthWest",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "EastNorth": ["NorthWest", "SouthEast",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "EastSouth": ["NorthWest", "SouthEast",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "WestNorth": ["NorthEast", "SouthWest",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "WestSouth": ["NorthEast", "SouthWest",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "NorthEastSouthWestNorth": ["NorthWest", "SouthEast",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "NorthWestSouthEastNorth": ["NorthEast", "SouthWest",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "EastSouthWestNorth": ["NorthWest", "SouthEast",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "EastNorthWestNorth": ["NorthEast", "SouthWest",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "SouthEastWestNorth": ["NorthWest", "SouthWest",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "SouthWestWestNorth": ["NorthEast", "SouthEast",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "NorthEastWestNorth": ["NorthWest", "SouthEast",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    # "NorthWestWestNorth": ["NorthEast", "SouthWest",'East', 'South', 'West', 'North', 'NorthWest', 'SouthEast'],
    
}

