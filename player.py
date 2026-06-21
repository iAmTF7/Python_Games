"""Canonical player object for the project.

This replaces the old loose stat-container with a real game object while keeping
all original player fields intact for the Item and Level modules.

Original fields preserved:
- level, exp, exp_need, stat_points
- max_hp, hp, max_armor, armor, max_energy, energy
- damage, speed
- hp_regen, armor_regen, energy_regen
- special_items
- haste_timer, iron_skin_timer, berserk_timer

New fields/methods provide a shared foundation for map, weapon, monster, item,
and level systems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

try:
    import pygame
except ModuleNotFoundError:  # Allows non-Pygame logic/tests to import Player.
    pygame = None  # type: ignore[assignment]


class _FallbackRect:
    """Tiny pygame.Rect fallback used only when pygame is unavailable."""

    def __init__(self, x: int, y: int, w: int, h: int) -> None:
        self.x = int(x)
        self.y = int(y)
        self.w = int(w)
        self.h = int(h)
        self.width = self.w
        self.height = self.h

    @property
    def left(self) -> int:
        return self.x

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def top(self) -> int:
        return self.y

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @property
    def centerx(self) -> int:
        return self.x + self.w // 2

    @centerx.setter
    def centerx(self, value: int) -> None:
        self.x = int(value) - self.w // 2

    @property
    def centery(self) -> int:
        return self.y + self.h // 2

    @centery.setter
    def centery(self, value: int) -> None:
        self.y = int(value) - self.h // 2

    @property
    def center(self) -> tuple[int, int]:
        return self.centerx, self.centery

    @center.setter
    def center(self, value: tuple[int, int]) -> None:
        self.centerx, self.centery = value

    def move_ip(self, dx: int, dy: int) -> None:
        self.x += int(dx)
        self.y += int(dy)

    def colliderect(self, other: Any) -> bool:
        return not (
            self.right <= other.left
            or self.left >= other.right
            or self.bottom <= other.top
            or self.top >= other.bottom
        )

    def copy(self):
        return _FallbackRect(self.x, self.y, self.w, self.h)


class _FallbackVector2:
    """Tiny pygame.Vector2 fallback used only when pygame is unavailable."""

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)

    def length(self) -> float:
        return (self.x * self.x + self.y * self.y) ** 0.5

    def normalize(self):
        length = self.length()
        if length == 0:
            return _FallbackVector2(0, 0)
        return _FallbackVector2(self.x / length, self.y / length)

    def update(self, x: float, y: float) -> None:
        self.x = float(x)
        self.y = float(y)

    def __iter__(self):
        yield self.x
        yield self.y


@dataclass(frozen=True)
class PlayerConfig:
    """Default player values.

    Values match the original ``player.py`` stat container unless noted.
    """

    x: int = 100
    y: int = 100
    width: int = 40
    height: int = 40

    level: int = 1
    exp: int = 0
    exp_need: int = 100
    stat_points: int = 0

    max_hp: int = 100
    hp: int = 100
    max_armor: int = 50
    armor: int = 50
    max_energy: int = 100
    energy: int = 100

    damage: int = 25
    speed: float = 6


class Player:
    """Single canonical player object used by every gameplay module."""

    def __init__(
        self,
        x: int = 100,
        y: int = 100,
        width: int = 40,
        height: int = 40,
        config: PlayerConfig | None = None,
    ) -> None:
        cfg = config or PlayerConfig(x=x, y=y, width=width, height=height)

        # Runtime body / movement state.
        rect_cls = pygame.Rect if pygame else _FallbackRect
        vector_cls = pygame.Vector2 if pygame else _FallbackVector2
        self.rect = rect_cls(cfg.x, cfg.y, cfg.width, cfg.height)
        self.direction = vector_cls(0, 1)

        # Tile-space position used by the map module.  Pixel-space modules use rect.
        self.map_x: float = self.rect.centerx / 32
        self.map_y: float = self.rect.centery / 32

        # Level.
        self.level = cfg.level
        self.exp = cfg.exp
        self.exp_need = cfg.exp_need
        self.stat_points = cfg.stat_points

        # Stats.
        self.max_hp = cfg.max_hp
        self.hp = cfg.hp

        self.max_armor = cfg.max_armor
        self.armor = cfg.armor

        self.max_energy = cfg.max_energy
        self.energy = cfg.energy

        self.damage = cfg.damage
        self.speed = cfg.speed

        # Regen.
        self.hp_regen = 0
        self.armor_regen = 0
        self.energy_regen = 0

        # Special Items.
        self.special_items: list[str] = []

        # Buffs.
        self.haste_timer = 0
        self.iron_skin_timer = 0
        self.berserk_timer = 0

        # General runtime flags.
        self.alive = True
        self.invincible = False

    # ------------------------------------------------------------------
    # Position helpers
    # ------------------------------------------------------------------
    @property
    def x(self) -> int:
        """Center X position, matching monster/entity coordinate semantics."""
        return self.rect.centerx

    @x.setter
    def x(self, value: int) -> None:
        self.rect.centerx = int(value)

    @property
    def y(self) -> int:
        """Center Y position, matching monster/entity coordinate semantics."""
        return self.rect.centery

    @y.setter
    def y(self, value: int) -> None:
        self.rect.centery = int(value)

    @property
    def left(self) -> int:
        return self.rect.x

    @left.setter
    def left(self, value: int) -> None:
        self.rect.x = int(value)

    @property
    def top(self) -> int:
        return self.rect.y

    @top.setter
    def top(self, value: int) -> None:
        self.rect.y = int(value)

    @property
    def size(self) -> int:
        return max(self.rect.width, self.rect.height)

    @property
    def center(self):
        return self.rect.center

    @center.setter
    def center(self, value) -> None:
        self.rect.center = value

    def get_rect(self):
        return self.rect

    def set_position(self, x: int, y: int, *, center: bool = False) -> None:
        if center:
            self.rect.center = (int(x), int(y))
        else:
            self.rect.x = int(x)
            self.rect.y = int(y)

    def set_tile_position(self, tx: float, ty: float, tile_size: int = 32) -> None:
        """Set both tile-space and pixel-space position."""
        self.map_x = float(tx)
        self.map_y = float(ty)
        self.rect.center = (int(tx * tile_size), int(ty * tile_size))

    def sync_tile_position_from_rect(self, tile_size: int = 32) -> None:
        self.map_x = self.rect.centerx / tile_size
        self.map_y = self.rect.centery / tile_size

    def sync_rect_from_tile_position(self, tile_size: int = 32) -> None:
        self.rect.center = (int(self.map_x * tile_size), int(self.map_y * tile_size))

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------
    def set_direction(self, dx: float, dy: float) -> None:
        vector_cls = pygame.Vector2 if pygame else _FallbackVector2
        direction = vector_cls(dx, dy)
        if direction.length() > 0:
            direction = direction.normalize()
            self.direction = direction

    def move_pixels(self, dx: float, dy: float) -> None:
        if dx or dy:
            self.set_direction(dx, dy)
        self.rect.x += int(dx)
        self.rect.y += int(dy)

    def move_on_map(self, dx: float, dy: float, tile_map: Any, tile_size: int = 32) -> None:
        """Move in tile-space using a TileMap-compatible collision object."""
        if dx or dy:
            self.set_direction(dx, dy)
        self.map_x, self.map_y = tile_map.move_player(self.map_x, self.map_y, dx, dy)
        self.sync_rect_from_tile_position(tile_size)

    # ------------------------------------------------------------------
    # Survival/stat helpers
    # ------------------------------------------------------------------
    def is_alive(self) -> bool:
        return self.alive and self.hp > 0

    def take_damage(self, amount: int | float, *, use_armor: bool = True) -> int | float:
        """Damage the player and return the amount that reached HP.

        Armor-first damage is provided as a standard player behavior. Existing
        modules that directly mutate ``hp`` still remain compatible.
        """
        if self.invincible or amount <= 0:
            return 0

        remaining = amount
        if use_armor and self.armor > 0:
            absorbed = min(self.armor, remaining)
            self.armor -= absorbed
            remaining -= absorbed

        if remaining > 0:
            self.hp = max(0, self.hp - remaining)

        if self.hp <= 0:
            self.alive = False

        return remaining

    def heal(self, amount: int | float) -> None:
        self.hp = min(self.max_hp, self.hp + amount)
        if self.hp > 0:
            self.alive = True

    def restore_armor(self, amount: int | float) -> None:
        self.armor = min(self.max_armor, self.armor + amount)

    def restore_energy(self, amount: int | float) -> None:
        self.energy = min(self.max_energy, self.energy + amount)

    def spend_energy(self, amount: int | float) -> bool:
        if self.energy < amount:
            return False
        self.energy -= amount
        return True

    def restore_full(self) -> None:
        self.hp = self.max_hp
        self.armor = self.max_armor
        self.energy = self.max_energy
        self.alive = True

    def add_special_item(self, item_type: str) -> bool:
        if item_type in self.special_items:
            return False
        self.special_items.append(item_type)
        return True

    def has_special_item(self, item_type: str) -> bool:
        return item_type in self.special_items

    def update_regen(self) -> None:
        """Apply one regen tick. Call this only at your chosen regen cadence."""
        if self.hp_regen:
            self.heal(self.hp_regen)
        if self.armor_regen:
            self.restore_armor(self.armor_regen)
        if self.energy_regen:
            self.restore_energy(self.energy_regen)

    def update_buffs(self) -> None:
        self.haste_timer = max(0, self.haste_timer - 1)
        self.iron_skin_timer = max(0, self.iron_skin_timer - 1)
        self.berserk_timer = max(0, self.berserk_timer - 1)

    def update(self, state: Any = None) -> None:
        self.update_buffs()

    def draw(self, surface: Any, color: tuple[int, int, int] = (0, 200, 255)) -> None:
        if pygame and surface is not None:
            pygame.draw.rect(surface, color, self.rect)

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "exp": self.exp,
            "exp_need": self.exp_need,
            "stat_points": self.stat_points,
            "max_hp": self.max_hp,
            "hp": self.hp,
            "max_armor": self.max_armor,
            "armor": self.armor,
            "max_energy": self.max_energy,
            "energy": self.energy,
            "damage": self.damage,
            "speed": self.speed,
            "special_items": list(self.special_items),
            "alive": self.alive,
        }


__all__ = ["Player", "PlayerConfig"]
