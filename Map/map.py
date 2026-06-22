"""Object-oriented map module with legacy-compatible functions.

The old file opened a Pygame window and started its own infinite loop at import
time.  This module now only provides map data, collision, movement, and drawing
helpers.  It can be plugged into the shared Game loop or used directly in tests.

Original mechanics preserved:
- 36x24 map, 32px tiles
- sector-based random room generation
- room connection corridor logic
- fallback room when generation fails
- exit placed in the last room
- circular tile-space player collision
- binary search safe movement against walls
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Any, Iterable, Protocol

import pygame

try:
    from game.base_system import BaseSystem
except ModuleNotFoundError:  # Allows this module to run standalone.
    class BaseSystem:  # type: ignore[no-redef]
        pass


TILE = 32
MAP_W, MAP_H = 36, 24
SCREEN_W, SCREEN_H = MAP_W * TILE, MAP_H * TILE

FLOOR = 0
WALL = 1
EXIT = 2

PLAYER_RADIUS = 0.28  # in tile units
SPEED = 0.1

FLOOR_COLOR = (70, 70, 70)
WALL_COLOR = (25, 25, 25)
EXIT_COLOR = (60, 180, 80)
PLAYER_MARKER_COLOR = (220, 60, 60)


class RandomLike(Protocol):
    def randint(self, a: int, b: int) -> int:
        ...

    def choice(self, sequence):
        ...


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


@dataclass
class MapData:
    grid: list[list[int]]
    rooms: list[pygame.Rect]
    start_pos: tuple[int, int]
    exit_pos: tuple[int, int]


@dataclass(frozen=True)
class MapConfig:
    width: int = MAP_W
    height: int = MAP_H
    tile_size: int = TILE

    # Use fewer, larger sectors so each sector can fit a real combat room.
    # The previous 4x3 split made many random rooms too large for their sector,
    # which often produced only one tiny playable island.
    cols: int = 3
    rows: int = 2
    min_room_w: int = 7
    max_room_w: int = 9
    min_room_h: int = 6
    max_room_h: int = 8

    # Corridors are carved with one extra tile on each side. This makes them
    # readable as hallways instead of cracks and leaves enough clearance for
    # 30px monsters to stand/move through them.
    corridor_half_width: int = 1

    fallback_room: tuple[int, int, int, int] = (3, 3, 12, 8)


class MapGenerator:
    """Generates dungeon maps using the original room/corridor algorithm."""

    def __init__(self, config: MapConfig | None = None, rng: RandomLike | None = None) -> None:
        self.config = config or MapConfig()
        self.rng: RandomLike = rng or random

    def generate(self, level: int = 0) -> MapData:
        cfg = self.config
        grid = [[WALL for _ in range(cfg.width)] for _ in range(cfg.height)]
        rooms: list[pygame.Rect] = []

        sector_w = cfg.width // cfg.cols
        sector_h = cfg.height // cfg.rows

        for sy in range(cfg.rows):
            for sx in range(cfg.cols):
                w = self.rng.randint(cfg.min_room_w, cfg.max_room_w)
                h = self.rng.randint(cfg.min_room_h, cfg.max_room_h)
                min_x = sx * sector_w + 1
                min_y = sy * sector_h + 1
                max_x = min((sx + 1) * sector_w - w - 1, cfg.width - w - 2)
                max_y = min((sy + 1) * sector_h - h - 1, cfg.height - h - 2)

                if max_x < min_x or max_y < min_y:
                    continue

                x = self.rng.randint(min_x, max_x)
                y = self.rng.randint(min_y, max_y)
                room = pygame.Rect(x, y, w, h)

                if any(room.colliderect(other.inflate(1, 1)) for other in rooms):
                    continue

                rooms.append(room)
                self._carve_room(grid, room)

        if not rooms:
            room = pygame.Rect(*cfg.fallback_room)
            rooms.append(room)
            self._carve_room(grid, room)

        rooms.sort(key=lambda room: (room.centery, room.centerx))
        self._connect_rooms(grid, rooms)

        start_room = rooms[0]
        exit_room = rooms[-1]
        start_pos = start_room.center
        exit_x = exit_room.x + exit_room.w // 2
        exit_y = exit_room.y + exit_room.h // 2
        grid[exit_y][exit_x] = EXIT

        return MapData(grid=grid, rooms=rooms, start_pos=start_pos, exit_pos=(exit_x, exit_y))

    def _carve_room(self, grid: list[list[int]], room: pygame.Rect) -> None:
        for yy in range(room.y, room.y + room.h):
            for xx in range(room.x, room.x + room.w):
                grid[yy][xx] = FLOOR

    def _connect_rooms(self, grid: list[list[int]], rooms: list[pygame.Rect]) -> None:
        for i in range(1, len(rooms)):
            x1, y1 = rooms[i - 1].center
            x2, y2 = rooms[i].center

            if self.rng.choice([True, False]):
                self._carve_h_corridor(grid, x1, x2, y1)
                self._carve_v_corridor(grid, y1, y2, x2)
            else:
                self._carve_v_corridor(grid, y1, y2, x1)
                self._carve_h_corridor(grid, x1, x2, y2)

    def _carve_h_corridor(self, grid: list[list[int]], x1: int, x2: int, y: int) -> None:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self._carve_walkable_with_clearance(grid, x, y)

    def _carve_v_corridor(self, grid: list[list[int]], y1: int, y2: int, x: int) -> None:
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self._carve_walkable_with_clearance(grid, x, y)

    def _carve_walkable_with_clearance(self, grid: list[list[int]], cx: int, cy: int) -> None:
        r = self.config.corridor_half_width
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if 0 < xx < self.config.width - 1 and 0 < yy < self.config.height - 1:
                    grid[yy][xx] = FLOOR


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
        return data

    def tile_at(self, tx: int, ty: int) -> int | None:
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.grid[ty][tx]
        return None

    def is_wall_at(self, tx: int, ty: int) -> bool:
        return 0 <= tx < self.width and 0 <= ty < self.height and self.grid[ty][tx] == WALL

    def is_exit_at(self, tx: int, ty: int) -> bool:
        return 0 <= tx < self.width and 0 <= ty < self.height and self.grid[ty][tx] == EXIT

    def is_walkable_at(self, tx: int, ty: int, *, include_exit: bool = True) -> bool:
        if not 0 <= tx < self.width or not 0 <= ty < self.height:
            return False
        tile = self.grid[ty][tx]
        return tile == FLOOR or (include_exit and tile == EXIT)

    def has_walkable_clearance(
        self,
        tx: int,
        ty: int,
        clearance: int = 1,
        *,
        include_exit: bool = True,
    ) -> bool:
        for yy in range(ty - clearance, ty + clearance + 1):
            for xx in range(tx - clearance, tx + clearance + 1):
                if not self.is_walkable_at(xx, yy, include_exit=include_exit):
                    return False
        return True

    def iter_walkable_tiles(
        self,
        *,
        clearance: int = 0,
        include_exit: bool = True,
    ) -> Iterable[tuple[int, int]]:
        for ty, row in enumerate(self.grid):
            for tx, tile in enumerate(row):
                if tile == WALL or (tile == EXIT and not include_exit):
                    continue
                if clearance > 0 and not self.has_walkable_clearance(
                    tx, ty, clearance, include_exit=include_exit
                ):
                    continue
                yield tx, ty

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
        return int(px) == self.exit_pos[0] and int(py) == self.exit_pos[1]

    def maybe_advance_level(self, px: float, py: float) -> bool:
        if not self.reached_exit(px, py):
            return False
        self.load_level(self.level + 1)
        return True

    def start_pixel_center(self) -> tuple[int, int]:
        return self.tile_to_pixel_center(*self.start_pos)

    def tile_to_pixel_center(self, tx: float, ty: float) -> tuple[int, int]:
        return int((tx + 0.5) * self.tile_size), int((ty + 0.5) * self.tile_size)

    def pixel_to_tile(self, px: float, py: float) -> tuple[int, int]:
        return int(px // self.tile_size), int(py // self.tile_size)

    def is_pixel_rect_walkable(
        self,
        rect: pygame.Rect,
        *,
        include_exit: bool = True,
    ) -> bool:
        """Return True only when the whole pixel-space rect fits on walkable map tiles."""
        map_w, map_h = self.screen_size
        if rect.left < 0 or rect.top < 0 or rect.right > map_w or rect.bottom > map_h:
            return False

        left = rect.left // self.tile_size
        right = (rect.right - 1) // self.tile_size
        top = rect.top // self.tile_size
        bottom = (rect.bottom - 1) // self.tile_size

        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                if not self.is_walkable_at(tx, ty, include_exit=include_exit):
                    return False
        return True

    def is_pixel_center_walkable(
        self,
        x: float,
        y: float,
        size: int,
        *,
        include_exit: bool = True,
    ) -> bool:
        rect = pygame.Rect(0, 0, int(size), int(size))
        rect.center = (int(x), int(y))
        return self.is_pixel_rect_walkable(rect, include_exit=include_exit)

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


# ---------------------------------------------------------------------------
# Legacy-compatible module API
# ---------------------------------------------------------------------------
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


def collides(px: float, py: float) -> bool:
    return _default_map.collides(px, py)


def find_max_safe_move(px: float, py: float, dx: float, dy: float):
    return _default_map.find_max_safe_move(px, py, dx, dy)


def move_player(px: float, py: float, dx: float, dy: float):
    return _default_map.move_player(px, py, dx, dy)


__all__ = [
    "EXIT",
    "FLOOR",
    "LEVEL",
    "MAP_H",
    "MAP_W",
    "PLAYER_RADIUS",
    "SCREEN_H",
    "SCREEN_W",
    "SPEED",
    "TILE",
    "WALL",
    "MapConfig",
    "MapData",
    "MapGenerator",
    "MapSystem",
    "TileMap",
    "clamp",
    "collides",
    "exit_pos",
    "find_max_safe_move",
    "game_map",
    "generate_map",
    "is_wall_at",
    "load_level",
    "move_player",
    "player_x",
    "player_y",
    "rooms",
]
