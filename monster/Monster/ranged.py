"""
Module ranged.py - Quái tầm xa (RangedMonster)
Kế thừa từ Monster, override attack() để bắn đạn, override move_towards() để giữ khoảng cách.

OOP Principles:
    - Kế thừa (Inheritance): RangedMonster → Monster → Entity
    - Đa hình (Polymorphism): override attack(), move_towards(), draw()
"""

import pygame

from .base import Monster
from ..Combat.projectile import Projectile
from ..Config.settings import Colors, MonsterConfig, Settings


class RangedMonster(Monster):
    """
    Quái tầm xa - giữ khoảng cách và bắn đạn ma thuật.

    Kế thừa (Inheritance): Monster → Entity
    Đa hình (Polymorphism):
        - attack(): bắn Projectile
        - move_towards(): giữ khoảng cách an toàn
        - draw(): vẽ hình vuông tím + dấu +
    """

    def __init__(self, x: float, y: float,
                 screen_width: int = Settings.SCREEN_WIDTH,
                 screen_height: int = Settings.SCREEN_HEIGHT):
        """
        Khởi tạo quái tầm xa.

        Args:
            x, y: Vị trí spawn
            screen_width: Chiều rộng màn hình
            screen_height: Chiều cao màn hình
        """
        super().__init__(
            x, y,
            hp=MonsterConfig.RANGED_HP,
            damage=MonsterConfig.RANGED_DAMAGE,
            attack_range=MonsterConfig.RANGED_ATTACK_RANGE,
            speed=MonsterConfig.RANGED_SPEED,
            cooldown=MonsterConfig.RANGED_COOLDOWN,
            color=MonsterConfig.RANGED_COLOR,
            size=MonsterConfig.RANGED_SIZE,
            screen_width=screen_width,
            screen_height=screen_height
        )

    def move_towards(self, target, tile_map=None):
        """
        Đa hình (Polymorphism): Di chuyển thông minh - giữ khoảng cách.
        - Xa quá → tiến lại gần
        - Gần quá → lùi ra xa (giữ safe distance)
        - Trong khoảng tốt → đứng yên

        Args:
            target: Mục tiêu di chuyển tới/lùi ra
        """
        dist = self.distance_to(target)

        if dist > self._attack_range:
            # Xa quá → tiến lại gần
            super().move_towards(target, tile_map)
        elif dist < self._attack_range - MonsterConfig.RANGED_SAFE_DISTANCE:
            # Gần quá → lùi ra xa
            if dist == 0:
                return
            dx = (self._x - target.x) / dist
            dy = (self._y - target.y) / dist
            self._move_by_with_map_collision(dx * self._speed, dy * self._speed, tile_map)

    def attack(self, target, projectiles: list):
        """
        Đa hình (Polymorphism): Tấn công tầm xa - bắn đạn ma thuật.
        Tạo Projectile bay về phía target.

        Args:
            target: Mục tiêu bắn
            projectiles: Danh sách đạn (thêm đạn mới vào)
        """
        proj = Projectile(
            self._x, self._y,
            target.x, target.y,
            self._damage,
            speed=MonsterConfig.PROJECTILE_SPEED,
            screen_width=self._screen_width,
            screen_height=self._screen_height
        )
        projectiles.append(proj)

    def draw(self, surface: pygame.Surface):
        """
        Đa hình (Polymorphism): Vẽ quái tầm xa.
        Hình vuông tím + dấu +.

        Args:
            surface: Surface pygame để vẽ lên
        """
        if not self.is_alive():
            return

        # Vẽ thân quái (hình vuông tím)
        rect = pygame.Rect(
            self._x - self._size / 2,
            self._y - self._size / 2,
            self._size, self._size
        )
        pygame.draw.rect(surface, self._color, rect)

        # Vẽ dấu + để phân biệt loại quái
        pygame.draw.line(surface, Colors.WHITE,
                         (self._x, self._y - 10),
                         (self._x, self._y + 10), 2)
        pygame.draw.line(surface, Colors.WHITE,
                         (self._x - 10, self._y),
                         (self._x + 10, self._y), 2)

        self._draw_health_bar(surface)
