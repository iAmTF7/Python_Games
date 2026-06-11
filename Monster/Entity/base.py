"""
Module base.py - Lớp thực thể cơ sở (Entity)
Đây là base class cho tất cả đối tượng trong game.

OOP Principles:
    - Đóng gói (Encapsulation): Tất cả thuộc tính dùng _private + @property
    - Kế thừa (Inheritance): Các class con sẽ kế thừa Entity
    - Trừu tượng (Abstraction): Cung cấp interface chung cho mọi entity
"""

import pygame
import math

from ..Config.settings import Colors, Settings


class Entity:
    """
    Lớp cha (base class) cho tất cả thực thể trong game.

    Đóng gói (Encapsulation):
        - Tất cả thuộc tính dùng tiền tố _ (private by convention)
        - Truy cập qua @property getter (read-only bên ngoài)

    Kế thừa (Inheritance):
        - Monster, DummyTarget, v.v. sẽ kế thừa lớp này

    Hỗ trợ va chạm cứng AABB (Axis-Aligned Bounding Box).
    Bug #4 đã sửa: screen_width/height truyền qua constructor,
    không hardcode WIDTH/HEIGHT global.
    """

    def __init__(self, x: float, y: float, hp: int, speed: float,
                 color: tuple, size: int,
                 screen_width: int = Settings.SCREEN_WIDTH,
                 screen_height: int = Settings.SCREEN_HEIGHT):
        """
        Khởi tạo Entity.

        Args:
            x: Tọa độ X ban đầu
            y: Tọa độ Y ban đầu
            hp: Máu tối đa
            speed: Tốc độ di chuyển
            color: Màu sắc hiển thị (tuple RGB)
            size: Kích thước hitbox (pixel)
            screen_width: Chiều rộng màn hình (bug #4: không hardcode)
            screen_height: Chiều cao màn hình (bug #4: không hardcode)
        """
        self._x = x
        self._y = y
        self._hp = hp
        self._max_hp = hp
        self._speed = speed
        self._color = color
        self._size = size
        self._screen_width = screen_width
        self._screen_height = screen_height

    # === PROPERTY GETTERS (Đóng gói - Encapsulation) ===

    @property
    def x(self) -> float:
        """Tọa độ X hiện tại"""
        return self._x

    @property
    def y(self) -> float:
        """Tọa độ Y hiện tại"""
        return self._y

    @property
    def hp(self) -> int:
        """Máu hiện tại"""
        return self._hp

    @property
    def max_hp(self) -> int:
        """Máu tối đa"""
        return self._max_hp

    @property
    def size(self) -> int:
        """Kích thước hitbox"""
        return self._size

    @property
    def screen_width(self) -> int:
        """Chiều rộng màn hình"""
        return self._screen_width

    @property
    def screen_height(self) -> int:
        """Chiều cao màn hình"""
        return self._screen_height

    # === COLLISION (Va chạm AABB) ===

    def get_rect(self) -> pygame.Rect:
        """Trả về hitbox AABB (Axis-Aligned Bounding Box) của entity"""
        return pygame.Rect(
            self._x - self._size / 2,
            self._y - self._size / 2,
            self._size,
            self._size
        )

    def collides_with(self, other) -> bool:
        """
        Kiểm tra va chạm AABB với entity khác.

        Args:
            other: Entity khác cần kiểm tra

        Returns:
            True nếu 2 entity đang chồng lên nhau
        """
        return self.get_rect().colliderect(other.get_rect())

    @staticmethod
    def resolve_aabb_collision(entity_a, entity_b,
                               push_ratio_a: float = 0.5,
                               push_ratio_b: float = 0.5):
        """
        Giải quyết va chạm cứng AABB giữa 2 entity.
        Đẩy chúng ra khỏi nhau theo trục có overlap nhỏ nhất.

        Args:
            entity_a, entity_b: Hai entity đang va chạm
            push_ratio_a: Tỉ lệ đẩy entity_a (0.0 → 1.0)
            push_ratio_b: Tỉ lệ đẩy entity_b (0.0 → 1.0)
        """
        rect_a = entity_a.get_rect()
        rect_b = entity_b.get_rect()
        if not rect_a.colliderect(rect_b):
            return

        # Tính overlap trên mỗi trục
        overlap_x = min(rect_a.right, rect_b.right) - max(rect_a.left, rect_b.left)
        overlap_y = min(rect_a.bottom, rect_b.bottom) - max(rect_a.top, rect_b.top)

        if overlap_x <= 0 or overlap_y <= 0:
            return

        # Đẩy theo trục có overlap nhỏ hơn (minimum penetration)
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

    # === MOVEMENT & SCREEN BOUNDS ===

    def clamp_to_screen(self):
        """
        Giữ entity trong phạm vi màn hình.
        Bug #4 đã sửa: dùng self._screen_width/height thay vì global.
        """
        half = self._size / 2
        self._x = max(half, min(self._screen_width - half, self._x))
        self._y = max(half, min(self._screen_height - half, self._y))

    # === COMBAT ===

    def take_damage(self, amount: int):
        """
        Nhận sát thương.

        Args:
            amount: Lượng sát thương nhận vào
        """
        self._hp -= amount
        if self._hp < 0:
            self._hp = 0

    def is_alive(self) -> bool:
        """Kiểm tra entity còn sống không"""
        return self._hp > 0

    def distance_to(self, other) -> float:
        """
        Tính khoảng cách Euclidean tới thực thể khác.

        Args:
            other: Entity khác (cần có property x, y)

        Returns:
            Khoảng cách (float)
        """
        return math.sqrt((self._x - other.x) ** 2 + (self._y - other.y) ** 2)

    # === RENDERING ===

    def draw(self, surface: pygame.Surface):
        """
        Vẽ thực thể lên màn hình (hình vuông + thanh máu).

        Args:
            surface: Surface pygame để vẽ lên
        """
        rect = pygame.Rect(
            self._x - self._size / 2,
            self._y - self._size / 2,
            self._size,
            self._size
        )
        pygame.draw.rect(surface, self._color, rect)
        self._draw_health_bar(surface)

    def _draw_health_bar(self, surface: pygame.Surface):
        """
        Vẽ thanh máu phía trên entity (private method).

        Args:
            surface: Surface pygame để vẽ lên
        """
        bar_width = self._size
        bar_height = 5
        fill = (self._hp / self._max_hp) * bar_width

        outline_rect = pygame.Rect(
            self._x - self._size / 2,
            self._y - self._size / 2 - 10,
            bar_width, bar_height
        )
        fill_rect = pygame.Rect(
            self._x - self._size / 2,
            self._y - self._size / 2 - 10,
            fill, bar_height
        )
        pygame.draw.rect(surface, Colors.HEALTH_BAR_BG, outline_rect)
        pygame.draw.rect(surface, Colors.HEALTH_BAR_FILL, fill_rect)
