"""Base monster class.

The original movement, cooldown, idle-wander, collision, and attack timing
logic is preserved. The only structural change is that ``attack`` is now a
formal abstract method, because concrete monsters already provide their own
implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import math
import random

from ..Entity.base import Entity
from ..Config.settings import MonsterConfig, Settings


class Monster(Entity, ABC):
    """Base class for all monster types."""

    def __init__(
        self,
        x: float,
        y: float,
        hp: int,
        damage: int,
        attack_range: int,
        speed: float,
        cooldown: int,
        color: tuple,
        size: int,
        screen_width: int = Settings.SCREEN_WIDTH,
        screen_height: int = Settings.SCREEN_HEIGHT,
    ):
        super().__init__(x, y, hp, speed, color, size, screen_width, screen_height)
        self._damage = damage
        self._attack_range = attack_range
        self._cooldown = cooldown
        self._current_cooldown = 0

        # Idle-wander state. Preserves the original cooldown-in-range behavior.
        self._wander_target_x = x
        self._wander_target_y = y
        self._wander_timer = 0

    @property
    def damage(self) -> int:
        return self._damage

    @property
    def attack_range(self) -> int:
        return self._attack_range

    @property
    def cooldown(self) -> int:
        return self._cooldown

    @property
    def current_cooldown(self) -> int:
        return self._current_cooldown

    @property
    def can_attack(self) -> bool:
        return self._current_cooldown <= 0

    def update(self, target, projectiles: list, tile_map=None):
        """Update movement and attack state for one frame."""
        if not self.is_alive():
            return

        if self._current_cooldown > 0:
            self._current_cooldown -= 1

        dist = self.distance_to(target)

        if dist <= self._attack_range:
            if self._current_cooldown <= 0:
                self.attack(target, projectiles)
                self._current_cooldown = self._cooldown
            else:
                self._idle_wander(tile_map)
        else:
            self.move_towards(target, tile_map)

    @abstractmethod
    def attack(self, target, projectiles: list):
        """Perform this monster's attack. Implemented by subclasses."""
        raise NotImplementedError

    def move_towards(self, target, tile_map=None):
        """Move directly toward the target."""
        dist = self.distance_to(target)
        if dist == 0:
            return
        dx = (target.x - self._x) / dist
        dy = (target.y - self._y) / dist
        self._move_by_with_map_collision(dx * self._speed, dy * self._speed, tile_map)

    def _move_by_with_map_collision(self, dx: float, dy: float, tile_map=None):
        if tile_map is None:
            self._x += dx
            self._y += dy
            self.clamp_to_screen()
            return

        original_x, original_y = self._x, self._y

        self._x = original_x + dx
        if not self._fits_tile_map(tile_map):
            self._x = original_x

        self._y = original_y + dy
        if not self._fits_tile_map(tile_map):
            self._y = original_y

        self.clamp_to_screen()
        if not self._fits_tile_map(tile_map):
            self._x, self._y = original_x, original_y

    def _fits_tile_map(self, tile_map) -> bool:
        rect_fits = getattr(tile_map, "is_pixel_rect_walkable", None)
        if callable(rect_fits):
            return bool(rect_fits(self.get_rect(), include_exit=False))
        return True

    def _idle_wander(self, tile_map=None):
        """Move slowly around while in range but still on cooldown."""
        wander_radius = MonsterConfig.IDLE_WANDER_RADIUS
        wander_speed = self._speed * MonsterConfig.IDLE_WANDER_SPEED_RATIO

        self._wander_timer -= 1
        if self._wander_timer <= 0:
            angle = random.uniform(0, 2 * math.pi)
            self._wander_target_x = self._x + math.cos(angle) * wander_radius
            self._wander_target_y = self._y + math.sin(angle) * wander_radius
            self._wander_timer = random.randint(20, 50)

        dist = math.sqrt(
            (self._wander_target_x - self._x) ** 2
            + (self._wander_target_y - self._y) ** 2
        )
        if dist > 2:
            dx = (self._wander_target_x - self._x) / dist
            dy = (self._wander_target_y - self._y) / dist
            self._move_by_with_map_collision(dx * wander_speed, dy * wander_speed, tile_map)

    def separate_from_others(self, monsters: list, tile_map=None):
        """Resolve AABB overlap against other live monsters."""
        if not self.is_alive():
            return
        original_x, original_y = self._x, self._y
        for other in monsters:
            if other is self or not other.is_alive():
                continue
            if self.collides_with(other):
                Entity.resolve_aabb_collision(self, other, 0.5, 0.5)
        self.clamp_to_screen()
        if tile_map is not None and not self._fits_tile_map(tile_map):
            self._x, self._y = original_x, original_y

    def draw(self, surface):
        if not self.is_alive():
            return
        super().draw(surface)
