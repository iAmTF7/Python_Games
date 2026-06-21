"""Projectile fired by ranged monsters."""

from __future__ import annotations

import math
from typing import Tuple

import pygame

from ..Config.settings import MonsterConfig, Settings


class Projectile:
    """Magic projectile used by ``RangedMonster``."""

    def __init__(
        self,
        x: float,
        y: float,
        target_x: float,
        target_y: float,
        damage: int,
        speed: float = MonsterConfig.PROJECTILE_SPEED,
        screen_width: int = Settings.SCREEN_WIDTH,
        screen_height: int = Settings.SCREEN_HEIGHT,
    ):
        self._x = x
        self._y = y
        self._damage = damage
        self._speed = speed
        self._radius = MonsterConfig.PROJECTILE_RADIUS
        self._screen_width = screen_width
        self._screen_height = screen_height

        angle = math.atan2(target_y - y, target_x - x)
        self._dx = math.cos(angle) * speed
        self._dy = math.sin(angle) * speed

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def position(self) -> Tuple[float, float]:
        return self._x, self._y

    @property
    def damage(self) -> int:
        return self._damage

    @property
    def speed(self) -> float:
        return self._speed

    @property
    def radius(self) -> int:
        return self._radius

    @property
    def velocity(self) -> Tuple[float, float]:
        return self._dx, self._dy

    def get_rect(self) -> pygame.Rect:
        """Return a square rect around the circular projectile."""
        return pygame.Rect(
            self._x - self._radius,
            self._y - self._radius,
            self._radius * 2,
            self._radius * 2,
        )

    def update(self):
        self._x += self._dx
        self._y += self._dy

    def is_out_of_bounds(self) -> bool:
        margin = self._radius
        return (
            self._x < -margin
            or self._x > self._screen_width + margin
            or self._y < -margin
            or self._y > self._screen_height + margin
        )

    def is_alive(self) -> bool:
        """Shared-system compatibility alias."""
        return not self.is_out_of_bounds()

    def check_hit(self, target) -> bool:
        dist = math.sqrt((self._x - target.x) ** 2 + (self._y - target.y) ** 2)
        return dist < target.size / 2 + self._radius

    def draw(self, surface: pygame.Surface):
        pos = (int(self._x), int(self._y))
        pygame.draw.circle(surface, MonsterConfig.PROJECTILE_COLOR, pos, self._radius)
        pygame.draw.circle(
            surface,
            MonsterConfig.PROJECTILE_BORDER_COLOR,
            pos,
            self._radius,
            1,
        )
