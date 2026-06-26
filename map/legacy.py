"""Backward-compatible map module globals and functions."""

from __future__ import annotations

import pygame

from .generator import MapGenerator
from .tilemap import TileMap

_default_map = TileMap(0)
LEVEL = _default_map.level
game_map = _default_map.grid
rooms = _default_map.rooms
player_x, player_y = _default_map.start_pos
exit_pos = _default_map.exit_pos


def _sync_legacy_globals() -> None:
    global LEVEL, game_map, rooms, player_x, player_y, exit_pos
    LEVEL = _default_map.level
    game_map = _default_map.grid
    rooms = _default_map.rooms
    exit_pos = _default_map.exit_pos


def generate_map(level: int = 0):
    """Legacy function returning ``grid, rooms, start_pos, exit_pos``."""
    data = MapGenerator().generate(level)
    return data.grid, data.rooms, data.start_pos, data.exit_pos


def load_level(level: int):
    """Legacy function that reloads the module-level default map."""
    global player_x, player_y
    data = _default_map.load_level(level)
    player_x, player_y = data.start_pos
    _sync_legacy_globals()
    if pygame.get_init():
        try:
            pygame.display.set_caption(f"Map {LEVEL + 1}")
        except pygame.error:
            pass
    return data.grid, data.rooms, data.start_pos, data.exit_pos


def is_wall_at(tx: int, ty: int) -> bool:
    return _default_map.is_wall_at(tx, ty)


def has_line_of_sight(
    start_pos: tuple[float, float],
    end_pos: tuple[float, float],
) -> bool:
    return _default_map.has_line_of_sight(start_pos, end_pos)


def collides(px: float, py: float) -> bool:
    return _default_map.collides(px, py)


def find_max_safe_move(px: float, py: float, dx: float, dy: float):
    return _default_map.find_max_safe_move(px, py, dx, dy)


def move_player(px: float, py: float, dx: float, dy: float):
    return _default_map.move_player(px, py, dx, dy)
