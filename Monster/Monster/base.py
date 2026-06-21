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

    def update(self, target, projectiles: list):
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
                self._idle_wander()
        else:
            self.move_towards(target)

    @abstractmethod
    def attack(self, target, projectiles: list):
        """Perform this monster's attack. Implemented by subclasses."""
        raise NotImplementedError

    def move_towards(self, target):
        """Move directly toward the target."""
        dist = self.distance_to(target)
        if dist == 0:
            return
        dx = (target.x - self._x) / dist
        dy = (target.y - self._y) / dist
        self._x += dx * self._speed
        self._y += dy * self._speed

    def _idle_wander(self):
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
            self._x += dx * wander_speed
            self._y += dy * wander_speed

        self.clamp_to_screen()

    def separate_from_others(self, monsters: list):
        """Resolve AABB overlap against other live monsters."""
        if not self.is_alive():
            return
        for other in monsters:
            if other is self or not other.is_alive():
                continue
            if self.collides_with(other):
                Entity.resolve_aabb_collision(self, other, 0.5, 0.5)
        self.clamp_to_screen()

    def draw(self, surface):
        if not self.is_alive():
            return
        super().draw(surface)
