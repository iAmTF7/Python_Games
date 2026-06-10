"""
Module projectile.py - Đạn ma thuật của quái tầm xa

OOP Principles:
    - Đóng gói (Encapsulation): thuộc tính private + @property
    - Bug #5 đã sửa: tăng radius từ 6 → 8, thêm is_out_of_bounds()
"""

import pygame
import math

from ..Config.settings import MonsterConfig, Settings


class Projectile:
    """
    Đạn ma thuật bắn bởi quái tầm xa (RangedMonster).

    Đóng gói (Encapsulation):
        - Tất cả thuộc tính dùng _private
        - Truy cập qua @property getter
        - Bug #5: tăng radius, thêm method kiểm tra out of bounds
    """

    def __init__(self, x: float, y: float,
                 target_x: float, target_y: float,
                 damage: int,
                 speed: float = MonsterConfig.PROJECTILE_SPEED,
                 screen_width: int = Settings.SCREEN_WIDTH,
                 screen_height: int = Settings.SCREEN_HEIGHT):
        """
        Khởi tạo đạn.

        Args:
            x, y: Vị trí xuất phát (vị trí quái bắn)
            target_x, target_y: Vị trí mục tiêu
            damage: Sát thương gây ra
            speed: Tốc độ bay
            screen_width: Chiều rộng màn hình
            screen_height: Chiều cao màn hình
        """
        self._x = x
        self._y = y
        self._damage = damage
        self._speed = speed
        self._radius = MonsterConfig.PROJECTILE_RADIUS  # Bug #5: 8 thay vì 6
        self._screen_width = screen_width
        self._screen_height = screen_height

        # Tính hướng bay dựa trên góc atan2
        angle = math.atan2(target_y - y, target_x - x)
        self._dx = math.cos(angle) * speed
        self._dy = math.sin(angle) * speed

    # === PROPERTY GETTERS (Đóng gói) ===

    @property
    def x(self) -> float:
        """Tọa độ X hiện tại"""
        return self._x

    @property
    def y(self) -> float:
        """Tọa độ Y hiện tại"""
        return self._y

    @property
    def damage(self) -> int:
        """Sát thương của đạn"""
        return self._damage

    @property
    def radius(self) -> int:
        """Bán kính đạn (bug #5: tăng lên 8)"""
        return self._radius

    # === LOGIC ===

    def update(self):
        """Cập nhật vị trí đạn theo hướng bay"""
        self._x += self._dx
        self._y += self._dy

    def is_out_of_bounds(self) -> bool:
        """
        Kiểm tra đạn đã ra ngoài màn hình chưa.

        Returns:
            True nếu đạn đã ra ngoài màn hình
        """
        margin = self._radius
        return (self._x < -margin or
                self._x > self._screen_width + margin or
                self._y < -margin or
                self._y > self._screen_height + margin)

    def check_hit(self, target) -> bool:
        """
        Kiểm tra đạn có trúng mục tiêu không (va chạm hình tròn).

        Args:
            target: Entity mục tiêu (cần có x, y, size)

        Returns:
            True nếu đạn trúng mục tiêu
        """
        dist = math.sqrt((self._x - target.x) ** 2 + (self._y - target.y) ** 2)
        return dist < target.size / 2 + self._radius

    # === RENDERING ===

    def draw(self, surface: pygame.Surface):
        """
        Vẽ đạn (hình tròn vàng có viền cam).

        Args:
            surface: Surface pygame để vẽ lên
        """
        pos = (int(self._x), int(self._y))
        pygame.draw.circle(surface, MonsterConfig.PROJECTILE_COLOR,
                           pos, self._radius)
        pygame.draw.circle(surface, MonsterConfig.PROJECTILE_BORDER_COLOR,
                           pos, self._radius, 1)
