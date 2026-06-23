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
        """Update movement and attack state for one frame.

        ``tile_map`` is optional to keep the older monster-only demos working.
        When supplied, movement that would place the monster inside a wall is
        rolled back so the integrated debug runner can use map collision.
        """
        if not self.is_alive():
            return

        old_x, old_y = self._x, self._y

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

        if tile_map is not None:
            self._keep_inside_walkable_map(tile_map, old_x, old_y)

    def _keep_inside_walkable_map(self, tile_map, old_x: float, old_y: float) -> None:
        if tile_map.is_pixel_rect_walkable(self.get_rect(), include_exit=False):
            return

        new_x, new_y = self._x, self._y

        # Try axis-separated movement before fully rolling back. This gives the
        # monsters a simple wall-slide behavior instead of making them freeze.
        self._x, self._y = new_x, old_y
        if not tile_map.is_pixel_rect_walkable(self.get_rect(), include_exit=False):
            self._x = old_x

        self._x, self._y = self._x, new_y
        if not tile_map.is_pixel_rect_walkable(self.get_rect(), include_exit=False):
            self._y = old_y

        if not tile_map.is_pixel_rect_walkable(self.get_rect(), include_exit=False):
            self._x, self._y = old_x, old_y

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

    def separate_from_others(self, monsters: list, tile_map=None):
        """Resolve AABB overlap against other live monsters.

        "Ô cứng" (solid): lặp lại nhiều vòng (MONSTER_COLLISION_ITERATIONS)
        trong cùng 1 frame để giải hết phần chồng lấn giữa quái với quái,
        giúp quái không còn dính/chùm lên nhau khi đông. Mọi kiểm tra
        tile_map (không đẩy quái xuyên tường) được giữ nguyên ở mỗi vòng.
        """
        if not self.is_alive():
            return

        push_ratio = getattr(Settings, "MONSTER_COLLISION_PUSH", 0.5)
        iterations = getattr(Settings, "MONSTER_COLLISION_ITERATIONS", 1)

        original_self = (self._x, self._y)
        for _ in range(max(1, iterations)):
            moved = False
            for other in monsters:
                if other is self or not other.is_alive():
                    continue
                if self.collides_with(other):
                    old_self = (self._x, self._y)
                    old_other = (other._x, other._y)
                    Entity.resolve_aabb_collision(self, other, push_ratio, push_ratio)
                    if tile_map is not None:
                        if not tile_map.is_pixel_rect_walkable(self.get_rect(), include_exit=False):
                            self._x, self._y = old_self
                        if not tile_map.is_pixel_rect_walkable(other.get_rect(), include_exit=False):
                            other._x, other._y = old_other
                    moved = True

            self.clamp_to_screen()
            if tile_map is not None and not tile_map.is_pixel_rect_walkable(self.get_rect(), include_exit=False):
                self._x, self._y = original_self
                break
            if not moved:
                break

    def draw(self, surface):
        if not self.is_alive():
            return
        super().draw(surface)
