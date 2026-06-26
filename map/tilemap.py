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
<<<<<<< HEAD
=======

>>>>>>> Tuyên
        self.grid: list[list[int]] = []
        self.rooms: list[pygame.Rect] = []
        self.start_pos: tuple[int, int] = (0, 0)
        self.exit_pos: tuple[int, int] = (0, 0)
        self.exit_open: bool = True
<<<<<<< HEAD
=======

>>>>>>> Tuyên
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
<<<<<<< HEAD
=======

>>>>>>> Tuyên
        self.grid = data.grid
        self.rooms = data.rooms
        self.start_pos = data.start_pos
        self.exit_pos = data.exit_pos
        self.exit_open = True
<<<<<<< HEAD
        return data

    def close_exit(self) -> None:
        """Close the room exit until the current enemy set is cleared."""
=======

        return data

    def close_exit(self) -> None:
>>>>>>> Tuyên
        ex, ey = self.exit_pos
        self.grid[ey][ex] = WALL
        self.exit_open = False

    def open_exit(self) -> None:
<<<<<<< HEAD
        """Open the room exit so the player can advance to the next room."""
=======
>>>>>>> Tuyên
        ex, ey = self.exit_pos
        self.grid[ey][ex] = EXIT
        self.exit_open = True

    def tile_at(self, tx: int, ty: int) -> int | None:
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.grid[ty][tx]
<<<<<<< HEAD
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
=======

        return None

    def is_wall_at(self, tx: int, ty: int) -> bool:
        return (
            0 <= tx < self.width
            and 0 <= ty < self.height
            and self.grid[ty][tx] == WALL
        )

    def is_exit_at(self, tx: int, ty: int) -> bool:
        return (
            0 <= tx < self.width
            and 0 <= ty < self.height
            and self.grid[ty][tx] == EXIT
        )

    def is_walkable_tile(
        self,
        tx: int,
        ty: int,
        *,
        include_exit: bool = True,
    ) -> bool:
        tile = self.tile_at(tx, ty)
        return tile == FLOOR or (include_exit and tile == EXIT)

    def iter_walkable_tiles(
        self,
        clearance: int = 0,
        *,
        include_exit: bool = True,
    ):
        clearance = max(0, int(clearance))

>>>>>>> Tuyên
        for ty in range(self.height):
            for tx in range(self.width):
                if not self.is_walkable_tile(tx, ty, include_exit=include_exit):
                    continue

                clear = True
<<<<<<< HEAD
=======

>>>>>>> Tuyên
                for cy in range(ty - clearance, ty + clearance + 1):
                    for cx in range(tx - clearance, tx + clearance + 1):
                        if not self.is_walkable_tile(cx, cy, include_exit=include_exit):
                            clear = False
                            break
<<<<<<< HEAD
=======

>>>>>>> Tuyên
                    if not clear:
                        break

                if clear:
                    yield tx, ty

<<<<<<< HEAD
    def is_pixel_rect_walkable(self, rect: pygame.Rect, *, include_exit: bool = True) -> bool:
        """Return True when every tile touched by ``rect`` is walkable."""
        left = math.floor(rect.left / self.tile_size)
        right = math.floor((rect.right - 1) / self.tile_size)
        top = math.floor(rect.top / self.tile_size)
        bottom = math.floor((rect.bottom - 1) / self.tile_size)
=======
    def is_pixel_rect_walkable(
        self,
        rect: pygame.Rect,
        *,
        include_exit: bool = True,
    ) -> bool:
        """
        Return True when every tile touched by rect is walkable.

        Quan trọng:
        - Dùng rect pixel để check player/projectile.
        - Thu nhỏ hitbox nhẹ để player không bị dính mép tường.
        """
        test_rect = rect.copy()

        if test_rect.width > 8 and test_rect.height > 8:
            test_rect = test_rect.inflate(-4, -4)

        left = math.floor(test_rect.left / self.tile_size)
        right = math.floor((test_rect.right - 1) / self.tile_size)
        top = math.floor(test_rect.top / self.tile_size)
        bottom = math.floor((test_rect.bottom - 1) / self.tile_size)
>>>>>>> Tuyên

        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                if not self.is_walkable_tile(tx, ty, include_exit=include_exit):
                    return False
<<<<<<< HEAD
        return True

    def tile_rect(self, tx: int, ty: int) -> pygame.Rect:
        """Return the pixel-space rectangle occupied by one map tile."""
=======

        return True

    def tile_rect(self, tx: int, ty: int) -> pygame.Rect:
>>>>>>> Tuyên
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
<<<<<<< HEAD
        """Yield wall tile rects near the pixel-space line segment.

        Checking only the line's bounding box keeps line-of-sight tests cheap
        while still catching nearby blockers around diagonal shots.
        """
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        left = max(0, math.floor(min(start_x, end_x) / self.tile_size) - padding_tiles)
=======
        start_x, start_y = start_pos
        end_x, end_y = end_pos

        left = max(
            0,
            math.floor(min(start_x, end_x) / self.tile_size) - padding_tiles,
        )

>>>>>>> Tuyên
        right = min(
            self.width - 1,
            math.floor(max(start_x, end_x) / self.tile_size) + padding_tiles,
        )
<<<<<<< HEAD
        top = max(0, math.floor(min(start_y, end_y) / self.tile_size) - padding_tiles)
=======

        top = max(
            0,
            math.floor(min(start_y, end_y) / self.tile_size) - padding_tiles,
        )

>>>>>>> Tuyên
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
<<<<<<< HEAD
        """Return True if no wall tile blocks the line between two pixels.

        This is intended for enemy vision/aim checks: ranged monsters should
        not detect or shoot the player through closed walls.
        """
        start = (int(start_pos[0]), int(start_pos[1]))
        end = (int(end_pos[0]), int(end_pos[1]))
=======
        start = (int(start_pos[0]), int(start_pos[1]))
        end = (int(end_pos[0]), int(end_pos[1]))

>>>>>>> Tuyên
        if start == end:
            return True

        for wall_rect in self.iter_wall_rects_between(start, end):
            if wall_rect.clipline(start, end):
                return False
<<<<<<< HEAD
        return True

    def collides(self, px: float, py: float, radius: float = PLAYER_RADIUS) -> bool:
        left = math.floor(px - radius)
        right = math.floor(px + radius)
        top = math.floor(py - radius)
        bottom = math.floor(py + radius)
=======

        return True

    def collides(
        self,
        px: float,
        py: float,
        radius: float = PLAYER_RADIUS,
    ) -> bool:
        """
        Tile-space circle collision giữ lại để tương thích code cũ.
        Movement chính nên dùng move_player_rect().
        """
        skin = 0.04
        check_radius = max(0.01, radius - skin)

        left = math.floor(px - check_radius)
        right = math.floor(px + check_radius)
        top = math.floor(py - check_radius)
        bottom = math.floor(py + check_radius)
>>>>>>> Tuyên

        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                if not self.is_wall_at(tx, ty):
                    continue

                closest_x = clamp(px, tx, tx + 1)
                closest_y = clamp(py, ty, ty + 1)

                dx = px - closest_x
                dy = py - closest_y
<<<<<<< HEAD
                if dx * dx + dy * dy < radius * radius:
=======

                if dx * dx + dy * dy < check_radius * check_radius:
>>>>>>> Tuyên
                    return True

        return False

<<<<<<< HEAD
    def find_max_safe_move(self, px: float, py: float, dx: float, dy: float, radius: float = PLAYER_RADIUS):
        low = 0.0
        high = dx if dx != 0 else dy

        for _ in range(8):
            mid = (low + high) / 2.0
            test_x = px + mid if dx != 0 else px
            test_y = py + mid if dy != 0 else py
=======
    def find_max_safe_move(
        self,
        px: float,
        py: float,
        dx: float,
        dy: float,
        radius: float = PLAYER_RADIUS,
    ):
        """
        Fallback tile-space movement.

        Fix lỗi cũ:
        high không được dùng dx/dy trực tiếp vì dx/dy có thể âm.
        Dùng hệ số 0.0 -> 1.0 cho mọi hướng.
        """
        low = 0.0
        high = 1.0

        for _ in range(10):
            mid = (low + high) / 2.0

            test_x = px + dx * mid
            test_y = py + dy * mid

>>>>>>> Tuyên
            if self.collides(test_x, test_y, radius):
                high = mid
            else:
                low = mid

<<<<<<< HEAD
        return px + low if dx != 0 else py + low

    def move_player(self, px: float, py: float, dx: float, dy: float, radius: float = PLAYER_RADIUS) -> tuple[float, float]:
        if dx != 0:
            target_x = px + dx
            if self.collides(target_x, py, radius):
                px = self.find_max_safe_move(px, py, dx, 0, radius)
=======
        return px + dx * low, py + dy * low

    def move_player(
        self,
        px: float,
        py: float,
        dx: float,
        dy: float,
        radius: float = PLAYER_RADIUS,
    ) -> tuple[float, float]:
        """
        Fallback tile-space movement.
        Player chính bên debug nên dùng update_player_from_keys -> move_player_rect.
        """
        if dx != 0:
            target_x = px + dx

            if self.collides(target_x, py, radius):
                px, _ = self.find_max_safe_move(px, py, dx, 0, radius)
>>>>>>> Tuyên
            else:
                px = target_x

        if dy != 0:
            target_y = py + dy
<<<<<<< HEAD
            if self.collides(px, target_y, radius):
                py = self.find_max_safe_move(px, py, 0, dy, radius)
=======

            if self.collides(px, target_y, radius):
                _, py = self.find_max_safe_move(px, py, 0, dy, radius)
>>>>>>> Tuyên
            else:
                py = target_y

        return px, py

<<<<<<< HEAD
=======
    def move_player_rect(
        self,
        player: Any,
        dx: float,
        dy: float,
        screen_rect: pygame.Rect | None = None,
    ) -> None:
        """
        Pixel-space rect movement.

        Đây là fix chính cho lỗi kẹt tường:
        - Di chuyển X và Y riêng.
        - Nếu đụng tường ở trục nào thì rollback trục đó.
        - Player vẫn trượt được dọc theo tường.
        """
        if not hasattr(player, "rect"):
            return

        rect = player.rect

        move_x = int(round(dx))
        move_y = int(round(dy))

        if move_x != 0:
            old_x = rect.x
            rect.x += move_x

            if screen_rect is not None:
                rect.clamp_ip(screen_rect)

            if not self.is_pixel_rect_walkable(rect, include_exit=True):
                rect.x = old_x

        if move_y != 0:
            old_y = rect.y
            rect.y += move_y

            if screen_rect is not None:
                rect.clamp_ip(screen_rect)

            if not self.is_pixel_rect_walkable(rect, include_exit=True):
                rect.y = old_y

        self.sync_player_from_rect(player)

    def sync_player_from_rect(self, player: Any) -> None:
        if not hasattr(player, "rect"):
            return

        if hasattr(player, "map_x"):
            player.map_x = player.rect.centerx / self.tile_size

        if hasattr(player, "map_y"):
            player.map_y = player.rect.centery / self.tile_size

>>>>>>> Tuyên
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
<<<<<<< HEAD
=======

>>>>>>> Tuyên
        self.load_level(self.level + 1)
        return True

    def start_pixel_center(self) -> tuple[int, int]:
        return self.tile_to_pixel_center(*self.start_pos)

    def tile_to_pixel_center(self, tx: float, ty: float) -> tuple[int, int]:
<<<<<<< HEAD
        return int(tx * self.tile_size), int(ty * self.tile_size)

    def place_player_at_start(self, player: Any) -> None:
        if hasattr(player, "set_tile_position"):
            player.set_tile_position(self.start_pos[0], self.start_pos[1], self.tile_size)
=======
        """
        Fix lỗi cũ:
        Cũ trả tx * tile_size, tức là góc tile.
        Đúng phải là tâm tile.
        """
        return (
            int((tx + 0.5) * self.tile_size),
            int((ty + 0.5) * self.tile_size),
        )

    def place_player_at_start(self, player: Any) -> None:
        if hasattr(player, "set_tile_position"):
            player.set_tile_position(
                self.start_pos[0],
                self.start_pos[1],
                self.tile_size,
            )
>>>>>>> Tuyên
            return

        if hasattr(player, "rect"):
            player.rect.center = self.start_pixel_center()

<<<<<<< HEAD
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
=======
        if hasattr(player, "map_x"):
            player.map_x = self.start_pos[0] + 0.5

        if hasattr(player, "map_y"):
            player.map_y = self.start_pos[1] + 0.5

    def update_player_from_keys(
        self,
        player: Any,
        keys: Any,
        speed: float = SPEED,
    ) -> None:
        dx = keys[pygame.K_d] - keys[pygame.K_a]
        dy = keys[pygame.K_s] - keys[pygame.K_w]

        if dx == 0 and dy == 0:
            return

        if dx != 0 and dy != 0:
            factor = 0.7071
            dx *= factor
            dy *= factor

        # SPEED trong project cũ thường là tile-space.
        # Nếu speed nhỏ hơn 1, đổi sang pixel-speed.
        if abs(speed) <= 1:
            pixel_speed = speed * self.tile_size
        else:
            pixel_speed = speed

        dx *= pixel_speed
        dy *= pixel_speed

        screen_rect = pygame.Rect(
            0,
            0,
            self.screen_size[0],
            self.screen_size[1],
        )

        # Quan trọng:
        # Không gọi player.move_on_map ở đây nữa.
        # move_on_map cũ là một nguồn gây lệch rect/map_x/map_y và kẹt tường.
        self.move_player_rect(
            player,
            dx,
            dy,
            screen_rect,
        )
>>>>>>> Tuyên

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
<<<<<<< HEAD
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
=======

                pygame.draw.rect(
                    surface,
                    color,
                    (
                        x * self.tile_size,
                        y * self.tile_size,
                        self.tile_size,
                        self.tile_size,
                    ),
                )

    def draw_player_marker(
        self,
        surface: pygame.Surface,
        px: float,
        py: float,
        radius: float = PLAYER_RADIUS,
    ) -> None:
        pygame.draw.circle(
            surface,
            PLAYER_MARKER_COLOR,
            (
                int(px * self.tile_size),
                int(py * self.tile_size),
            ),
            int(radius * self.tile_size),
        )
>>>>>>> Tuyên
