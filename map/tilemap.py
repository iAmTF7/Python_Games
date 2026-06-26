"""Runtime tile-map object."""

from __future__ import annotations

import math
from typing import Any

import pygame

from .constants import (
    EXIT,
    EXIT_COLOR,
    FLOOR,
    FLOOR_COLOR,
    LOCKED_EXIT_COLOR,
    PLAYER_MARKER_COLOR,
    PLAYER_RADIUS,
    SPEED,
    WALL,
    WALL_COLOR,
)
from .generator import MapGenerator
from .geometry import clamp
from .models import MapConfig, MapData


class TileMap:
    """Runtime map object that owns grid, collision, movement, and drawing."""

    def __init__(
        self,
        level: int = 0,
        config: MapConfig | None = None,
        generator: MapGenerator | None = None,
    ) -> None:
        self.config = config or MapConfig()
        self.generator = generator or MapGenerator(self.config)
        self.level = level
        self.grid: list[list[int]] = []
        self.rooms: list[pygame.Rect] = []
        self.start_pos: tuple[int, int] = (0, 0)
        self.exit_pos: tuple[int, int] = (0, 0)
        self.exit_open: bool = True
        self.load_level(level)

    @property
    def width(self) -> int:
        return self.config.width

    @property
    def height(self) -> int:
        return self.config.height

    @property
    def tile_size(self) -> int:
        return self.config.tile_size

    @property
    def screen_size(self) -> tuple[int, int]:
        return self.width * self.tile_size, self.height * self.tile_size

    def load_level(self, level: int) -> MapData:
        self.level = level
        data = self.generator.generate(level)
        self.grid = data.grid
        self.rooms = data.rooms
        self.start_pos = data.start_pos
        self.exit_pos = data.exit_pos
        self.exit_open = True
        return data

    def close_exit(self) -> None:
        """Close the room exit until the current enemy set is cleared."""
        ex, ey = self.exit_pos
        self.grid[ey][ex] = WALL
        self.exit_open = False

    def open_exit(self) -> None:
        """Open the room exit so the player can advance to the next room."""
        ex, ey = self.exit_pos
        self.grid[ey][ex] = EXIT
        self.exit_open = True

    def tile_at(self, tx: int, ty: int) -> int | None:
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.grid[ty][tx]
        return None

    def is_wall_at(self, tx: int, ty: int) -> bool:
        return 0 <= tx < self.width and 0 <= ty < self.height and self.grid[ty][tx] == WALL

    def is_exit_at(self, tx: int, ty: int) -> bool:
        return 0 <= tx < self.width and 0 <= ty < self.height and self.grid[ty][tx] == EXIT

    def is_walkable_tile(self, tx: int, ty: int, *, include_exit: bool = True) -> bool:
        """Return True when a tile can be occupied by gameplay entities."""
        tile = self.tile_at(tx, ty)
        return tile == FLOOR or (include_exit and tile == EXIT)

    def iter_walkable_tiles(self, clearance: int = 0, *, include_exit: bool = True):
        """Yield walkable tile coordinates with optional wall clearance.

        ``clearance=1`` means the tile and its 8 neighbors must all be
        walkable.  This is useful for spawning pixel-sized monsters because
        their centered rect can straddle nearby tiles.
        """
        clearance = max(0, int(clearance))
        for ty in range(self.height):
            for tx in range(self.width):
                if not self.is_walkable_tile(tx, ty, include_exit=include_exit):
                    continue

                clear = True
                for cy in range(ty - clearance, ty + clearance + 1):
                    for cx in range(tx - clearance, tx + clearance + 1):
                        if not self.is_walkable_tile(cx, cy, include_exit=include_exit):
                            clear = False
                            break
                    if not clear:
                        break

                if clear:
                    yield tx, ty

    def is_pixel_rect_walkable(self, rect: pygame.Rect, *, include_exit: bool = True) -> bool:
        """Return True when every tile touched by ``rect`` is walkable."""
        left = math.floor(rect.left / self.tile_size)
        right = math.floor((rect.right - 1) / self.tile_size)
        top = math.floor(rect.top / self.tile_size)
        bottom = math.floor((rect.bottom - 1) / self.tile_size)

        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                if not self.is_walkable_tile(tx, ty, include_exit=include_exit):
                    return False
        return True

    def tile_rect(self, tx: int, ty: int) -> pygame.Rect:
        """Return the pixel-space rectangle occupied by one map tile."""
        return pygame.Rect(
            tx * self.tile_size,
            ty * self.tile_size,
            self.tile_size,
            self.tile_size,
        )

    def iter_wall_rects_between(
        self,
        start_pos: tuple[float, float],
        end_pos: tuple[float, float],
        *,
        padding_tiles: int = 1,
    ):
        """Yield wall tile rects near the pixel-space line segment.

        Checking only the line's bounding box keeps line-of-sight tests cheap
        while still catching nearby blockers around diagonal shots.
        """
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        left = max(0, math.floor(min(start_x, end_x) / self.tile_size) - padding_tiles)
        right = min(
            self.width - 1,
            math.floor(max(start_x, end_x) / self.tile_size) + padding_tiles,
        )
        top = max(0, math.floor(min(start_y, end_y) / self.tile_size) - padding_tiles)
        bottom = min(
            self.height - 1,
            math.floor(max(start_y, end_y) / self.tile_size) + padding_tiles,
        )

        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                if self.is_wall_at(tx, ty):
                    yield self.tile_rect(tx, ty)

    def has_line_of_sight(
        self,
        start_pos: tuple[float, float],
        end_pos: tuple[float, float],
    ) -> bool:
        """Return True if no wall tile blocks the line between two pixels.

        This is intended for enemy vision/aim checks: ranged monsters should
        not detect or shoot the player through closed walls.
        """
        start = (int(start_pos[0]), int(start_pos[1]))
        end = (int(end_pos[0]), int(end_pos[1]))
        if start == end:
            return True

        for wall_rect in self.iter_wall_rects_between(start, end):
            if wall_rect.clipline(start, end):
                return False
        return True

    def collides(self, px: float, py: float, radius: float = PLAYER_RADIUS) -> bool:
        left = math.floor(px - radius)
        right = math.floor(px + radius)
        top = math.floor(py - radius)
        bottom = math.floor(py + radius)

        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                if not self.is_wall_at(tx, ty):
                    continue

                closest_x = clamp(px, tx, tx + 1)
                closest_y = clamp(py, ty, ty + 1)

                dx = px - closest_x
                dy = py - closest_y
                if dx * dx + dy * dy < radius * radius:
                    return True

        return False

    def find_max_safe_move(self, px: float, py: float, dx: float, dy: float, radius: float = PLAYER_RADIUS):
        low = 0.0
        high = dx if dx != 0 else dy

        for _ in range(8):
            mid = (low + high) / 2.0
            test_x = px + mid if dx != 0 else px
            test_y = py + mid if dy != 0 else py
            if self.collides(test_x, test_y, radius):
                high = mid
            else:
                low = mid

        return px + low if dx != 0 else py + low

    def move_player(self, px: float, py: float, dx: float, dy: float, radius: float = PLAYER_RADIUS) -> tuple[float, float]:
        if dx != 0:
            target_x = px + dx
            if self.collides(target_x, py, radius):
                px = self.find_max_safe_move(px, py, dx, 0, radius)
            else:
                px = target_x

        if dy != 0:
            target_y = py + dy
            if self.collides(px, target_y, radius):
                py = self.find_max_safe_move(px, py, 0, dy, radius)
            else:
                py = target_y

        return px, py

    def reached_exit(self, px: float, py: float) -> bool:
        return (
            self.exit_open
            and int(px) == self.exit_pos[0]
            and int(py) == self.exit_pos[1]
            and self.is_exit_at(self.exit_pos[0], self.exit_pos[1])
        )

    def maybe_advance_level(self, px: float, py: float) -> bool:
        if not self.reached_exit(px, py):
            return False
        self.load_level(self.level + 1)
        return True

    def start_pixel_center(self) -> tuple[int, int]:
        return self.tile_to_pixel_center(*self.start_pos)

    def tile_to_pixel_center(self, tx: float, ty: float) -> tuple[int, int]:
        return int(tx * self.tile_size), int(ty * self.tile_size)

    def place_player_at_start(self, player: Any) -> None:
        if hasattr(player, "set_tile_position"):
            player.set_tile_position(self.start_pos[0], self.start_pos[1], self.tile_size)
            return

        if hasattr(player, "rect"):
            player.rect.center = self.start_pixel_center()

    def update_player_from_keys(self, player: Any, keys: Any, speed: float = SPEED) -> None:
        dx = keys[pygame.K_d] - keys[pygame.K_a]
        dy = keys[pygame.K_s] - keys[pygame.K_w]

        if hasattr(player, "move_on_map"):
            player.move_on_map(dx * speed, dy * speed, self, self.tile_size)
            return

        px = getattr(player, "map_x", self.start_pos[0])
        py = getattr(player, "map_y", self.start_pos[1])
        px, py = self.move_player(px, py, dx * speed, dy * speed)
        player.map_x = px
        player.map_y = py
        if hasattr(player, "rect"):
            player.rect.center = self.tile_to_pixel_center(px, py)

    def draw(self, surface: pygame.Surface) -> None:
        for y, row in enumerate(self.grid):
            for x, tile in enumerate(row):
                if tile == FLOOR:
                    color = FLOOR_COLOR
                elif tile == EXIT:
                    color = EXIT_COLOR
                elif (x, y) == self.exit_pos and not self.exit_open:
                    color = LOCKED_EXIT_COLOR
                else:
                    color = WALL_COLOR
                pygame.draw.rect(
                    surface,
                    color,
                    (x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size),
                )

    def draw_player_marker(self, surface: pygame.Surface, px: float, py: float, radius: float = PLAYER_RADIUS) -> None:
        pygame.draw.circle(
            surface,
            PLAYER_MARKER_COLOR,
            (int(px * self.tile_size), int(py * self.tile_size)),
            int(radius * self.tile_size),
        )
