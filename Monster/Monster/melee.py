"""
Module melee.py - Quái cận chiến (MeleeMonster)
Kế thừa từ Monster, override attack() để đánh trực tiếp.

OOP Principles:
    - Kế thừa (Inheritance): MeleeMonster → Monster → Entity
    - Đa hình (Polymorphism): override attack(), draw()
"""

import pygame

from .base import Monster
from ..Config.settings import Colors, MonsterConfig, Settings


class MeleeMonster(Monster):
    """
    Quái cận chiến - tiến lại gần và gây sát thương trực tiếp.

    Kế thừa (Inheritance): Monster → Entity
    Đa hình (Polymorphism):
        - attack(): đánh cận chiến (take_damage trực tiếp)
        - draw(): vẽ hình vuông đỏ + dấu X
    """

    def __init__(self, x: float, y: float,
                 screen_width: int = Settings.SCREEN_WIDTH,
                 screen_height: int = Settings.SCREEN_HEIGHT):
        """
        Khởi tạo quái cận chiến.

        Args:
            x, y: Vị trí spawn
            screen_width: Chiều rộng màn hình
            screen_height: Chiều cao màn hình
        """
        super().__init__(
            x, y,
            hp=MonsterConfig.MELEE_HP,
            damage=MonsterConfig.MELEE_DAMAGE,
            attack_range=MonsterConfig.MELEE_ATTACK_RANGE,
            speed=MonsterConfig.MELEE_SPEED,
            cooldown=MonsterConfig.MELEE_COOLDOWN,
            color=MonsterConfig.MELEE_COLOR,
            size=MonsterConfig.MELEE_SIZE,
            screen_width=screen_width,
            screen_height=screen_height
        )

    def attack(self, target, projectiles: list):
        """
        Đa hình (Polymorphism): Tấn công cận chiến.
        Gây sát thương trực tiếp lên target.

        Args:
            target: Mục tiêu tấn công
            projectiles: Không dùng (chỉ để giữ interface chung)
        """
        target.take_damage(self._damage)

    def draw(self, surface: pygame.Surface):
        """
        Đa hình (Polymorphism): Vẽ quái cận chiến.
        Hình vuông đỏ + dấu X + vòng tấn công khi đang attack.

        Args:
            surface: Surface pygame để vẽ lên
        """
        if not self.is_alive():
            return

        # Vẽ vòng tròn tầm đánh khi đang tấn công
        if self._current_cooldown > self._cooldown - 10:
            attack_surface = pygame.Surface(
                (self._attack_range * 2 + 4, self._attack_range * 2 + 4),
                pygame.SRCALPHA
            )
            center = (self._attack_range + 2, self._attack_range + 2)
            # Vòng tròn đỏ mờ (fill)
            pygame.draw.circle(
                attack_surface, Colors.ATTACK_CIRCLE_FILL,
                center, self._attack_range, 0
            )
            # Viền vòng tròn đỏ
            pygame.draw.circle(
                attack_surface, Colors.ATTACK_CIRCLE_BORDER,
                center, self._attack_range, 2
            )
            surface.blit(
                attack_surface,
                (int(self._x) - self._attack_range - 2,
                 int(self._y) - self._attack_range - 2)
            )

        # Vẽ thân quái (hình vuông đỏ)
        rect = pygame.Rect(
            self._x - self._size / 2,
            self._y - self._size / 2,
            self._size, self._size
        )
        pygame.draw.rect(surface, self._color, rect)

        # Vẽ dấu X để phân biệt loại quái
        pygame.draw.line(surface, Colors.BLACK,
                         (self._x - 8, self._y - 8),
                         (self._x + 8, self._y + 8), 2)
        pygame.draw.line(surface, Colors.BLACK,
                         (self._x + 8, self._y - 8),
                         (self._x - 8, self._y + 8), 2)

        self._draw_health_bar(surface)
