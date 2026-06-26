"""Dungeon map generation."""

from __future__ import annotations

import random

import pygame

from .constants import EXIT, FLOOR, WALL
from .models import MapConfig, MapData, RandomLike


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

    def _carve_corridor_tile(self, grid: list[list[int]], x: int, y: int) -> None:
        """Carve a 3x3 corridor cell so entity-sized rects can pass through."""
        for yy in range(y - 1, y + 2):
            if yy < 0 or yy >= self.config.height:
                continue
            for xx in range(x - 1, x + 2):
                if 0 <= xx < self.config.width:
                    grid[yy][xx] = FLOOR

    def _connect_rooms(self, grid: list[list[int]], rooms: list[pygame.Rect]) -> None:
        for i in range(1, len(rooms)):
            x1, y1 = rooms[i - 1].center
            x2, y2 = rooms[i].center

            if self.rng.choice([True, False]):
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    self._carve_corridor_tile(grid, x, y1)
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    self._carve_corridor_tile(grid, x2, y)
            else:
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    self._carve_corridor_tile(grid, x1, y)
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    self._carve_corridor_tile(grid, x, y2)
