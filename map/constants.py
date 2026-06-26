"""Map constants.

The size-related constants are compatibility aliases that point back to
``game.settings``. Change resolution/layout in ``game/settings.py`` only.
"""

from game.settings import MAP_COLUMNS, MAP_ROWS, MAP_WIDTH, MAP_HEIGHT, TILE_SIZE

TILE = TILE_SIZE
MAP_W, MAP_H = MAP_COLUMNS, MAP_ROWS
SCREEN_W, SCREEN_H = MAP_WIDTH, MAP_HEIGHT

FLOOR = 0
WALL = 1
EXIT = 2

PLAYER_RADIUS = 0.28
SPEED = 0.1

FLOOR_COLOR = (70, 70, 70)
WALL_COLOR = (25, 25, 25)
EXIT_COLOR = (60, 180, 80)
LOCKED_EXIT_COLOR = (90, 55, 45)
PLAYER_MARKER_COLOR = (220, 60, 60)
