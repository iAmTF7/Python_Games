"""
Module ranged.py - Quái tầm xa (RangedMonster)
Kế thừa từ Monster, override attack() để bắn đạn, override move_towards() để giữ khoảng cách.
Cầm "súng" (vẽ đơn giản: 1 thanh súng quay theo hướng bắn) giống player.

OOP Principles:
    - Kế thừa (Inheritance): RangedMonster → Monster → Entity
    - Đa hình (Polymorphism): override attack(), move_towards(), draw()
"""

import math

import pygame

from .base import Monster
from ..Combat.projectile import Projectile
from ..Config.settings import Colors, MonsterConfig, Settings


class RangedMonster(Monster):
    """
    Quái tầm xa - giữ khoảng cách và bắn đạn bằng súng.

    Kế thừa (Inheritance): Monster → Entity
    Đa hình (Polymorphism):
        - attack(): bắn Projectile
        - move_towards(): giữ khoảng cách an toàn
        - draw(): vẽ hình vuông tím + súng cầm trên tay
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
            screen_height=screen_height,
            detect_range=MonsterConfig.RANGED_DETECT_RANGE,
        )
        # Hướng cầm súng (đơn vị vector), cập nhật mỗi khi di chuyển/bắn.
        self._facing_x = 0.0
        self._facing_y = 1.0

    def _update_facing(self, target):
        """Cập nhật hướng súng đang chỉ về phía mục tiêu."""
        dx = target.x - self._x
        dy = target.y - self._y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            self._facing_x = dx / dist
            self._facing_y = dy / dist

    def move_towards(self, target):
        """
        Đa hình (Polymorphism): Di chuyển thông minh - giữ khoảng cách.
        - Xa quá → tiến lại gần
        - Gần quá → lùi ra xa (giữ safe distance)
        - Trong khoảng tốt → đứng yên

        Args:
            target: Mục tiêu di chuyển tới/lùi ra
        """
        self._update_facing(target)
        dist = self.distance_to(target)

        if dist > self._attack_range:
            # Xa quá → tiến lại gần
            super().move_towards(target)
        elif dist < self._attack_range - MonsterConfig.RANGED_SAFE_DISTANCE:
            # Gần quá → lùi ra xa
            if dist == 0:
                return
            dx = (self._x - target.x) / dist
            dy = (self._y - target.y) / dist
            self._x += dx * self._speed
            self._y += dy * self._speed

    def attack(self, target, projectiles: list):
        """
        Đa hình (Polymorphism): Tấn công tầm xa - bắn súng.
        Tạo Projectile bay về phía target (giữ nguyên cơ chế cũ, chỉ đổi
        hình ảnh quái thành cầm súng).

        Args:
            target: Mục tiêu bắn
            projectiles: Danh sách đạn (thêm đạn mới vào)
        """
        self._update_facing(target)

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
        Đa hình (Polymorphism): Vẽ quái tầm xa cầm súng.
        Hình vuông tím + thanh súng đơn giản chỉ theo hướng bắn.

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

        # Vẽ súng: 1 thanh đơn giản từ tâm quái, theo hướng đang nhắm.
        gun_end_x = self._x + self._facing_x * MonsterConfig.RANGED_GUN_LENGTH
        gun_end_y = self._y + self._facing_y * MonsterConfig.RANGED_GUN_LENGTH
        pygame.draw.line(
            surface, MonsterConfig.RANGED_GUN_COLOR,
            (int(self._x), int(self._y)),
            (int(gun_end_x), int(gun_end_y)), 5
        )
        # Đầu nòng súng
        pygame.draw.circle(surface, Colors.BLACK,
                           (int(gun_end_x), int(gun_end_y)), 3)

        self._draw_health_bar(surface)
