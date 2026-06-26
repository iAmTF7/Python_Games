"""Map data models and protocols."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pygame

from .constants import MAP_H, MAP_W, TILE


class RandomLike(Protocol):
    def randint(self, a: int, b: int) -> int:
        ...

    def choice(self, sequence):
        ...


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
    cols: int = 4
    rows: int = 3
    min_room_w: int = 5
    max_room_w: int = 9
    min_room_h: int = 4
    max_room_h: int = 6
    fallback_room: tuple[int, int, int, int] = (2, 2, 6, 5)
