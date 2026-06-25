"""Monster factory/spawner."""

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple, Type

import pygame

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
        """Random hóa loại quái theo tỉ lệ melee/ranged.

        Level 1 bắt đầu ở tỉ lệ 6/4 (60% melee, 40% ranged), sau đó tỉ lệ
        ranged tăng dần CHẬM mỗi khi qua màn, nhưng có trần thấp (50%) để
        không bao giờ lấn lướt melee và làm màn sau quá khó.
        """
        ranged_chance = min(
            Settings.RANGED_CHANCE_MAX,
            Settings.RANGED_CHANCE_BASE
            + (level - 1) * Settings.RANGED_CHANCE_INCREASE_PER_LEVEL,
        )
        if random.random() < ranged_chance:
            return self.create_monster("ranged", x, y)
        return self.create_monster("melee", x, y)

    @property
    def registered_types(self) -> list:
        return list(self._monster_classes.keys())

    def get_enemy_count(self, level: int) -> int:
        level = max(1, int(level))
        count = Settings.BASE_ENEMY_COUNT + (level - 1) * Settings.ENEMY_INCREASE_PER_LEVEL
        return min(Settings.MAX_ENEMY_COUNT, count)

    def _spawn_rect(self, x: float, y: float) -> pygame.Rect:
        size = max(MonsterConfig.MELEE_SIZE, MonsterConfig.RANGED_SIZE)
        return pygame.Rect(x - size / 2, y - size / 2, size, size)

    def _is_far_enough(
        self,
        x: float,
        y: float,
        target_x: float,
        target_y: float,
        existing_positions: List[Tuple[float, float]],
    ) -> bool:
        min_dist = Settings.SPAWN_MIN_DISTANCE_FROM_TARGET
        min_monster_dist = Settings.SPAWN_MIN_DISTANCE_BETWEEN

        if math.dist((x, y), (target_x, target_y)) < min_dist:
            return False

        for mx, my in existing_positions:
            if math.dist((x, y), (mx, my)) < min_monster_dist:
                return False

        return True

    def _get_map_spawn_position(
        self,
        target_x: float,
        target_y: float,
        existing_positions: List[Tuple[float, float]],
        tile_map,
    ) -> tuple | None:
        candidates = list(tile_map.iter_walkable_tiles(clearance=1, include_exit=False))
        random.shuffle(candidates)

        best_position = None
        best_score = -1.0

        for tx, ty in candidates:
            x, y = tile_map.tile_to_pixel_center(tx, ty)
            if not tile_map.is_pixel_rect_walkable(self._spawn_rect(x, y), include_exit=False):
                continue

            target_dist = math.dist((x, y), (target_x, target_y))
            monster_dist = min(
                (math.dist((x, y), pos) for pos in existing_positions),
                default=float("inf"),
            )
            score = target_dist + min(monster_dist, Settings.SPAWN_MIN_DISTANCE_BETWEEN)

            if score > best_score:
                best_position = (x, y)
                best_score = score

            if self._is_far_enough(x, y, target_x, target_y, existing_positions):
                return (x, y)

        return best_position

    def get_spawn_position(
        self,
        target_x: float,
        target_y: float,
        existing_positions: List[Tuple[float, float]] = None,
        tile_map=None,
    ) -> tuple:
        if existing_positions is None:
            existing_positions = []

        if tile_map is not None:
            map_position = self._get_map_spawn_position(
                target_x, target_y, existing_positions, tile_map
            )
            if map_position is not None:
                return map_position

        margin = Settings.SPAWN_MARGIN

        for _ in range(Settings.SPAWN_MAX_ATTEMPTS):
            x = random.randint(margin, self._screen_width - margin)
            y = random.randint(margin, self._screen_height - margin)

            if self._is_far_enough(x, y, target_x, target_y, existing_positions):
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

    def spawn_wave(
        self, level: int, target_x: float, target_y: float, tile_map=None
    ) -> list:
        enemy_count = self.get_enemy_count(level)
        monsters = []
        existing_positions = []

        for _ in range(enemy_count):
            x, y = self.get_spawn_position(
                target_x, target_y, existing_positions, tile_map
            )
            monster = self.create_random_monster(x, y, level)
            if monster:
                monsters.append(monster)
                existing_positions.append((x, y))

        return monsters

    def reset_fallback(self):
        self._fallback_index = 0
