"""Resolution/layout consistency checks.

These tests protect the centralized display config so gameplay modules do not
silently drift back to hard-coded map/window sizes.
"""

from game.settings import (
    DISPLAY,
    HUD_WIDTH,
    MAP_COLUMNS,
    MAP_HEIGHT,
    MAP_ROWS,
    MAP_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILE_SIZE,
    get_map_size,
    get_window_size,
)
from map.constants import MAP_H, MAP_W, SCREEN_H, SCREEN_W, TILE
from monster.config import Settings as MonsterSettings


def test_display_settings_are_single_source_for_window_and_map_size():
    assert TILE_SIZE == DISPLAY.tile_size
    assert MAP_COLUMNS == DISPLAY.map_columns
    assert MAP_ROWS == DISPLAY.map_rows
    assert HUD_WIDTH == DISPLAY.hud_width

    assert (MAP_WIDTH, MAP_HEIGHT) == get_map_size()
    assert (SCREEN_WIDTH, SCREEN_HEIGHT) == get_window_size()
    assert SCREEN_WIDTH == MAP_WIDTH + HUD_WIDTH
    assert SCREEN_HEIGHT == MAP_HEIGHT


def test_map_and_monster_size_aliases_follow_game_settings():
    assert TILE == TILE_SIZE
    assert (MAP_W, MAP_H) == (MAP_COLUMNS, MAP_ROWS)
    assert (SCREEN_W, SCREEN_H) == (MAP_WIDTH, MAP_HEIGHT)

    # Monster bounds intentionally use the playable map, not the HUD-inclusive
    # window, so enemies/projectiles stay inside the gameplay area.
    assert MonsterSettings.SCREEN_WIDTH == MAP_WIDTH
    assert MonsterSettings.SCREEN_HEIGHT == MAP_HEIGHT
