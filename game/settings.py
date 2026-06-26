"""Central game configuration.

This module is the single source of truth for window size, map size, HUD size,
FPS, tile size, and other global display constants.

Important design rule:
    Feature modules should import size/config values from here directly or
    through their own compatibility aliases. They should not redefine window,
    map, or tile dimensions independently.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DisplaySettings:
    """Resolution and layout settings for the game window.

    The playable map is tile-based, so its pixel size is derived from
    ``map_columns * tile_size`` and ``map_rows * tile_size``. The debug/HUD panel
    is placed to the right of the playable map.

    To change the game resolution safely, edit these four layout values:
        - tile_size
        - map_columns
        - map_rows
        - hud_width

    The derived values below keep all modules in sync.
    """

    tile_size: int = 31
    map_columns: int = 36
    map_rows: int = 24
    hud_width: int = 300
    fps: int = 60

    @property
    def map_width(self) -> int:
        return self.map_columns * self.tile_size

    @property
    def map_height(self) -> int:
        return self.map_rows * self.tile_size

    @property
    def window_width(self) -> int:
        return self.map_width + self.hud_width

    @property
    def window_height(self) -> int:
        return self.map_height

    @property
    def map_size(self) -> tuple[int, int]:
        return self.map_width, self.map_height

    @property
    def window_size(self) -> tuple[int, int]:
        return self.window_width, self.window_height


DISPLAY = DisplaySettings()

# ---------------------------------------------------------------------------
# Backwards-compatible constants
# ---------------------------------------------------------------------------
# Use these names throughout the project. They are intentionally aliases to
# DISPLAY so existing imports remain stable after the config centralization.

TILE_SIZE = DISPLAY.tile_size
MAP_COLUMNS = DISPLAY.map_columns
MAP_ROWS = DISPLAY.map_rows
MAP_WIDTH = DISPLAY.map_width
MAP_HEIGHT = DISPLAY.map_height
HUD_WIDTH = DISPLAY.hud_width
SCREEN_WIDTH = DISPLAY.window_width
SCREEN_HEIGHT = DISPLAY.window_height
FPS = DISPLAY.fps

# Player/gameplay constants
PLAYER_SIZE = 40

# Runtime/debug constants
DEBUG = True
BACKGROUND_COLOR = (0, 0, 0)


def get_map_size() -> tuple[int, int]:
    """Return the playable map size in pixels."""
    return DISPLAY.map_size


def get_window_size() -> tuple[int, int]:
    """Return the full game window size in pixels, including the HUD."""
    return DISPLAY.window_size
