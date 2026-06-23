"""Monster factory/spawner."""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Tuple, Type

from ..Config.settings import MonsterConfig, Settings


class MonsterSpawner:
    """Create and spawn monsters while preserving the original spawn rules."""

    _FALLBACK_CORNERS = [
        "top_left",
        "top_right",
        "bottom_left",
        "bottom_right",
    ]

    def __init__(
        self,
        screen_width: int = Settings.SCREEN_WIDTH,
        screen_height: int = Settings.SCREEN_HEIGHT,
    ):
        self._screen_width = screen_width
        self._screen_height = screen_height
        self._monster_classes: Dict[str, Type] = {}
        self._fallback_index = 0

    def register_monster_class(self, name: str, cls):
        self._monster_classes[name] = cls

    def register_defaults(self):
        """Register the built-in melee and ranged monster classes."""
        from ..Monster.melee import MeleeMonster
        from ..Monster.ranged import RangedMonster

        self.register_monster_class("melee", MeleeMonster)
        self.register_monster_class("ranged", RangedMonster)
        return self

    @classmethod
    def with_defaults(
        cls,
        screen_width: int = Settings.SCREEN_WIDTH,
        screen_height: int = Settings.SCREEN_HEIGHT,
    ):
        """Convenience constructor with built-in monsters registered."""
        return cls(screen_width, screen_height).register_defaults()

    def create_monster(self, monster_type: str, x: float, y: float):
        cls = self._monster_classes.get(monster_type)
        if cls:
            return cls(
                x,
                y,
                screen_width=self._screen_width,
                screen_height=self._screen_height,
            )
        return None

    def create_random_monster(self, x: float, y: float, level: int):
        ranged_chance = min(0.6, 0.2 + (level - 1) * 0.05)
        if random.random() < ranged_chance:
            return self.create_monster("ranged", x, y)
        return self.create_monster("melee", x, y)

    @property
    def registered_types(self) -> list:
        return list(self._monster_classes.keys())

    def get_enemy_count(self, level: int) -> int:
        return Settings.BASE_ENEMY_COUNT + (level - 1) * Settings.ENEMY_INCREASE_PER_LEVEL

    def get_spawn_position(
        self,
        target_x: float,
        target_y: float,
        existing_positions: List[Tuple[float, float]] = None,
        tile_map: Any | None = None,
    ) -> tuple:
        if existing_positions is None:
            existing_positions = []

        if tile_map is not None:
            return self._get_map_spawn_position(target_x, target_y, existing_positions, tile_map)

        return self._get_screen_spawn_position(target_x, target_y, existing_positions)

    def _get_map_spawn_position(
        self,
        target_x: float,
        target_y: float,
        existing_positions: List[Tuple[float, float]],
        tile_map: Any,
    ) -> tuple:
        candidates = self._map_spawn_candidates(tile_map)
        if not candidates:
            raise RuntimeError("Tile map has no valid monster spawn positions")

        min_dist = Settings.SPAWN_MIN_DISTANCE_FROM_TARGET
        min_monster_dist = Settings.SPAWN_MIN_DISTANCE_BETWEEN

        for required_target_dist, required_monster_dist in (
            (min_dist, min_monster_dist),
            (min_dist * 0.65, min_monster_dist),
            (min_dist * 0.65, min_monster_dist * 0.5),
            (0, 0),
        ):
            for _ in range(Settings.SPAWN_MAX_ATTEMPTS):
                x, y = random.choice(candidates)
                if math.hypot(x - target_x, y - target_y) < required_target_dist:
                    continue
                if self._too_close_to_existing(x, y, existing_positions, required_monster_dist):
                    continue
                return (x, y)

        return random.choice(candidates)

    def _map_spawn_candidates(self, tile_map: Any) -> list[tuple[int, int]]:
        if hasattr(tile_map, "iter_walkable_tiles"):
            tiles = list(tile_map.iter_walkable_tiles(clearance=0, include_exit=False))
        else:
            tiles = []
            grid = getattr(tile_map, "grid", [])
            for ty, row in enumerate(grid):
                for tx, tile in enumerate(row):
                    if tile == 0:
                        tiles.append((tx, ty))

        tile_size = getattr(tile_map, "tile_size", 32)
        monster_size = max(MonsterConfig.MELEE_SIZE, MonsterConfig.RANGED_SIZE)

        candidates: list[tuple[int, int]] = []
        for tx, ty in tiles:
            # Use the actual center of the tile, not the tile's top-left corner.
            # A 30px monster fits inside a 32px floor tile only when centered.
            x = int((tx + 0.5) * tile_size)
            y = int((ty + 0.5) * tile_size)
            if not self._spawn_rect_fits_map(x, y, monster_size, tile_map):
                continue
            candidates.append((x, y))

        return candidates

    def _spawn_rect_fits_map(
        self,
        x: float,
        y: float,
        size: int,
        tile_map: Any,
    ) -> bool:
        map_w = min(self._screen_width, getattr(tile_map, "screen_size", (self._screen_width, self._screen_height))[0])
        map_h = min(self._screen_height, getattr(tile_map, "screen_size", (self._screen_width, self._screen_height))[1])
        half = size / 2
        if x - half < 0 or y - half < 0 or x + half > map_w or y + half > map_h:
            return False

        center_fits = getattr(tile_map, "is_pixel_center_walkable", None)
        if callable(center_fits):
            return bool(center_fits(x, y, size, include_exit=False))

        grid = getattr(tile_map, "grid", [])
        tile_size = getattr(tile_map, "tile_size", 32)
        if not grid:
            return False

        left = int((x - half) // tile_size)
        right = int((x + half - 1) // tile_size)
        top = int((y - half) // tile_size)
        bottom = int((y + half - 1) // tile_size)

        for ty in range(top, bottom + 1):
            if ty < 0 or ty >= len(grid):
                return False
            row = grid[ty]
            for tx in range(left, right + 1):
                if tx < 0 or tx >= len(row) or row[tx] != 0:
                    return False
        return True

    def _get_screen_spawn_position(
        self,
        target_x: float,
        target_y: float,
        existing_positions: List[Tuple[float, float]],
    ) -> tuple:
        margin = Settings.SPAWN_MARGIN
        min_dist = Settings.SPAWN_MIN_DISTANCE_FROM_TARGET
        min_monster_dist = Settings.SPAWN_MIN_DISTANCE_BETWEEN

        for _ in range(Settings.SPAWN_MAX_ATTEMPTS):
            x = random.randint(margin, self._screen_width - margin)
            y = random.randint(margin, self._screen_height - margin)

            if math.hypot(x - target_x, y - target_y) < min_dist:
                continue

            if not self._too_close_to_existing(x, y, existing_positions, min_monster_dist):
                return (x, y)

        corner = self._FALLBACK_CORNERS[self._fallback_index % len(self._FALLBACK_CORNERS)]
        self._fallback_index += 1

        offset_x = random.randint(0, 40)
        offset_y = random.randint(0, 40)

        if corner == "top_left":
            return (margin + offset_x, margin + offset_y)
        if corner == "top_right":
            return (self._screen_width - margin - offset_x, margin + offset_y)
        if corner == "bottom_left":
            return (margin + offset_x, self._screen_height - margin - offset_y)
        return (
            self._screen_width - margin - offset_x,
            self._screen_height - margin - offset_y,
        )

    @staticmethod
    def _too_close_to_existing(
        x: float,
        y: float,
        existing_positions: List[Tuple[float, float]],
        min_distance: float,
    ) -> bool:
        return any(math.hypot(x - mx, y - my) < min_distance for mx, my in existing_positions)

    def spawn_wave(
        self,
        level: int,
        target_x: float,
        target_y: float,
        tile_map: Any | None = None,
    ) -> list:
        enemy_count = self.get_enemy_count(level)
        monsters = []
        existing_positions = []

        for _ in range(enemy_count):
            x, y = self.get_spawn_position(target_x, target_y, existing_positions, tile_map)
            monster = self.create_random_monster(x, y, level)
            if monster:
                monsters.append(monster)
                existing_positions.append((x, y))

        return monsters

    def reset_fallback(self):
        self._fallback_index = 0
