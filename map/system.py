"""Map system adapter for the shared game loop."""

from __future__ import annotations

from typing import Any

import pygame

from core.base import BaseSystem

from .tilemap import TileMap


class MapSystem(BaseSystem):
    """BaseSystem adapter for using TileMap with GameState."""

    def __init__(self, tile_map: TileMap | None = None) -> None:
        self.tile_map = tile_map or TileMap()

    def handle_event(self, event: Any, state: Any) -> None:
        pass

    def update(self, state: Any) -> None:
        state.tile_map = self.tile_map
        player = getattr(state, "player", None)
        if player is None or not pygame.get_init():
            return

        keys = pygame.key.get_pressed()
        self.tile_map.update_player_from_keys(player, keys)

        px = getattr(player, "map_x", None)
        py = getattr(player, "map_y", None)
        if px is not None and py is not None and self.tile_map.maybe_advance_level(px, py):
            self.tile_map.place_player_at_start(player)

    def draw(self, surface: pygame.Surface, state: Any) -> None:
        self.tile_map.draw(surface)
