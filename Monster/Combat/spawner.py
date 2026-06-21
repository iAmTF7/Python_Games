"""Monster factory/spawner."""

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple, Type

from ..Config.settings import Settings


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
    ) -> tuple:
        if existing_positions is None:
            existing_positions = []

        margin = Settings.SPAWN_MARGIN
        min_dist = Settings.SPAWN_MIN_DISTANCE_FROM_TARGET
        min_monster_dist = Settings.SPAWN_MIN_DISTANCE_BETWEEN

        for _ in range(Settings.SPAWN_MAX_ATTEMPTS):
            x = random.randint(margin, self._screen_width - margin)
            y = random.randint(margin, self._screen_height - margin)

            dist = math.sqrt((x - target_x) ** 2 + (y - target_y) ** 2)
            if dist < min_dist:
                continue

            too_close = False
            for mx, my in existing_positions:
                if math.sqrt((x - mx) ** 2 + (y - my) ** 2) < min_monster_dist:
                    too_close = True
                    break

            if not too_close:
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

    def spawn_wave(self, level: int, target_x: float, target_y: float) -> list:
        enemy_count = self.get_enemy_count(level)
        monsters = []
        existing_positions = []

        for _ in range(enemy_count):
            x, y = self.get_spawn_position(target_x, target_y, existing_positions)
            monster = self.create_random_monster(x, y, level)
            if monster:
                monsters.append(monster)
                existing_positions.append((x, y))

        return monsters

    def reset_fallback(self):
        self._fallback_index = 0
