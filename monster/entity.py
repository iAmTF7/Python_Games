"""Base entity class used by the monster module.

This keeps the original mechanic logic intact:
- center-position based x/y coordinates
- square pygame.Rect hitboxes
- AABB collision resolution
- screen clamping
- HP damage/death behavior
"""

from __future__ import annotations

import math
from typing import Tuple

import pygame

from .config import Colors, Settings


class Entity:
    """Base class for movable/damageable game entities."""

    def __init__(
        self,
        x: float,
        y: float,
        hp: int,
        speed: float,
        color: tuple,
        size: int,
        screen_width: int = Settings.SCREEN_WIDTH,
        screen_height: int = Settings.SCREEN_HEIGHT,
    ):
        self._x = x
        self._y = y
        self._hp = hp
        self._max_hp = hp
        self._speed = speed
        self._color = color
        self._size = size
        self._screen_width = screen_width
        self._screen_height = screen_height

    # === Read-only public state ===

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
    def hp(self) -> int:
        return self._hp

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def speed(self) -> float:
        return self._speed

    @property
    def color(self) -> tuple:
        return self._color

    @property
    def size(self) -> int:
        return self._size

    @property
    def screen_width(self) -> int:
        return self._screen_width

    @property
    def screen_height(self) -> int:
        return self._screen_height

    @property
    def rect(self) -> pygame.Rect:
        """Alias for get_rect(), useful for shared systems."""
        return self.get_rect()

    # === Position helpers ===

    def set_position(self, x: float, y: float, clamp: bool = True):
        """Move entity center to a specific position."""
        self._x = x
        self._y = y
        if clamp:
            self.clamp_to_screen()

    def move_by(self, dx: float, dy: float, clamp: bool = True):
        """Move entity by an offset."""
        self._x += dx
        self._y += dy
        if clamp:
            self.clamp_to_screen()

    # === Collision ===

    def get_rect(self) -> pygame.Rect:
        """Return the square AABB hitbox centered on the entity."""
        return pygame.Rect(
            self._x - self._size / 2,
            self._y - self._size / 2,
            self._size,
            self._size,
        )

    def collides_with(self, other) -> bool:
        return self.get_rect().colliderect(other.get_rect())

    @staticmethod
    def resolve_aabb_collision(
        entity_a,
        entity_b,
        push_ratio_a: float = 0.5,
        push_ratio_b: float = 0.5,
    ):
        """Push overlapping AABB entities apart on the shallowest axis."""
        rect_a = entity_a.get_rect()
        rect_b = entity_b.get_rect()
        if not rect_a.colliderect(rect_b):
            return

        overlap_x = min(rect_a.right, rect_b.right) - max(rect_a.left, rect_b.left)
        overlap_y = min(rect_a.bottom, rect_b.bottom) - max(rect_a.top, rect_b.top)

        if overlap_x <= 0 or overlap_y <= 0:
            return

        if overlap_x < overlap_y:
            if entity_a._x < entity_b._x:
                entity_a._x -= overlap_x * push_ratio_a
                entity_b._x += overlap_x * push_ratio_b
            else:
                entity_a._x += overlap_x * push_ratio_a
                entity_b._x -= overlap_x * push_ratio_b
        else:
            if entity_a._y < entity_b._y:
                entity_a._y -= overlap_y * push_ratio_a
                entity_b._y += overlap_y * push_ratio_b
            else:
                entity_a._y += overlap_y * push_ratio_a
                entity_b._y -= overlap_y * push_ratio_b

    # === Movement / bounds ===

    def clamp_to_screen(self):
        half = self._size / 2
        self._x = max(half, min(self._screen_width - half, self._x))
        self._y = max(half, min(self._screen_height - half, self._y))

    # === Combat ===

    def take_damage(self, amount: int):
        self._hp -= amount
        if self._hp < 0:
            self._hp = 0

    def heal(self, amount: int):
        self._hp = min(self._max_hp, self._hp + amount)

    def is_alive(self) -> bool:
        return self._hp > 0

    def distance_to(self, other) -> float:
        return math.sqrt((self._x - other.x) ** 2 + (self._y - other.y) ** 2)

    # === Rendering ===

    def draw(self, surface: pygame.Surface):
        rect = pygame.Rect(
            self._x - self._size / 2,
            self._y - self._size / 2,
            self._size,
            self._size,
        )
        pygame.draw.rect(surface, self._color, rect)
        self._draw_health_bar(surface)

    def _draw_health_bar(self, surface: pygame.Surface):
        bar_width = self._size
        bar_height = 5
        fill = (self._hp / self._max_hp) * bar_width if self._max_hp else 0

        outline_rect = pygame.Rect(
            self._x - self._size / 2,
            self._y - self._size / 2 - 10,
            bar_width,
            bar_height,
        )
        fill_rect = pygame.Rect(
            self._x - self._size / 2,
            self._y - self._size / 2 - 10,
            fill,
            bar_height,
        )
        pygame.draw.rect(surface, Colors.HEALTH_BAR_BG, outline_rect)
        pygame.draw.rect(surface, Colors.HEALTH_BAR_FILL, fill_rect)
