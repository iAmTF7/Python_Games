"""
Module base.py - Lớp quái vật cơ sở (Monster)
Kế thừa từ Entity, là base class cho MeleeMonster và RangedMonster.

OOP Principles:
    - Kế thừa (Inheritance): Monster kế thừa Entity
    - Đa hình (Polymorphism): attack() sẽ được override ở class con
    - Trừu tượng (Abstraction): attack() là abstract-like method
    - Đóng gói (Encapsulation): thuộc tính private + @property
    - Bug #1 đã sửa: quái idle_wander khi cooldown trong range
    - Bug #2 đã sửa: thêm @property damage
"""

import random
import math

from ..Entity.base import Entity
from ..Config.settings import Colors, MonsterConfig, Settings


class Monster(Entity):
    """
    Lớp cơ sở cho tất cả quái vật.
    Kế thừa (Inheritance) từ Entity.

    Đa hình (Polymorphism):
        - attack(): được ghi đè ở MeleeMonster, RangedMonster
        - move_towards(): có thể ghi đè (RangedMonster giữ khoảng cách)
        - draw(): ghi đè để vẽ khác nhau

    Bug #1 đã sửa:
        - Khi cooldown > 0 và trong range → gọi idle_wander() thay vì đứng yên
    Bug #2 đã sửa:
        - Thêm @property damage để truy cập an toàn
    """

    def __init__(self, x: float, y: float, hp: int, damage: int,
                 attack_range: int, speed: float, cooldown: int,
                 color: tuple, size: int,
                 screen_width: int = Settings.SCREEN_WIDTH,
                 screen_height: int = Settings.SCREEN_HEIGHT):
        """
        Khởi tạo Monster.

        Args:
            x, y: Vị trí ban đầu
            hp: Máu tối đa
            damage: Sát thương mỗi đòn
            attack_range: Tầm tấn công
            speed: Tốc độ di chuyển
            cooldown: Thời gian hồi chiêu (frames)
            color: Màu sắc hiển thị
            size: Kích thước hitbox
            screen_width: Chiều rộng màn hình (bug #4)
            screen_height: Chiều cao màn hình (bug #4)
        """
        super().__init__(x, y, hp, speed, color, size,
                         screen_width, screen_height)
        self._damage = damage
        self._attack_range = attack_range
        self._cooldown = cooldown
        self._current_cooldown = 0

        # Bug #1: Wander state cho idle movement
        self._wander_target_x = x
        self._wander_target_y = y
        self._wander_timer = 0

    # === PROPERTY GETTERS (Bug #2: thêm damage property) ===

    @property
    def damage(self) -> int:
        """
        Sát thương mỗi đòn tấn công.
        Bug #2 đã sửa: dùng property thay vì truy cập _damage trực tiếp.
        """
        return self._damage

    @property
    def attack_range(self) -> int:
        """Tầm tấn công"""
        return self._attack_range

    @property
    def cooldown(self) -> int:
        """Thời gian hồi chiêu tối đa"""
        return self._cooldown

    @property
    def current_cooldown(self) -> int:
        """Thời gian hồi chiêu hiện tại"""
        return self._current_cooldown

    # === COMBAT LOGIC ===

    def update(self, target, projectiles: list):
        """
        Cập nhật trạng thái quái mỗi frame: di chuyển và tấn công.
        Bug #1 đã sửa: khi cooldown > 0 và trong range → idle_wander()

        Args:
            target: Mục tiêu (Entity hoặc DummyTarget)
            projectiles: Danh sách đạn (để RangedMonster thêm vào)
        """
        if not self.is_alive():
            return

        if self._current_cooldown > 0:
            self._current_cooldown -= 1

        dist = self.distance_to(target)

        if dist <= self._attack_range:
            if self._current_cooldown <= 0:
                # Hết cooldown → tấn công
                self.attack(target, projectiles)
                self._current_cooldown = self._cooldown
            else:
                # Bug #1 FIX: Cooldown > 0 trong range → idle wander
                # thay vì đứng yên
                self._idle_wander()
        else:
            # Ngoài range → tiến về phía target
            self.move_towards(target)

    def attack(self, target, projectiles: list):
        """
        Tấn công mục tiêu.
        Trừu tượng (Abstraction) + Đa hình (Polymorphism):
        Method này sẽ được override ở MeleeMonster và RangedMonster.

        Args:
            target: Mục tiêu tấn công
            projectiles: Danh sách đạn
        """
        pass  # Override ở class con

    # === MOVEMENT ===

    def move_towards(self, target):
        """
        Di chuyển về phía mục tiêu.
        Đa hình (Polymorphism): RangedMonster sẽ override để giữ khoảng cách.

        Args:
            target: Mục tiêu di chuyển tới
        """
        dist = self.distance_to(target)
        if dist == 0:
            return
        dx = (target.x - self._x) / dist
        dy = (target.y - self._y) / dist
        self._x += dx * self._speed
        self._y += dy * self._speed

    def _idle_wander(self):
        """
        Bug #1 FIX: Di chuyển ngẫu nhiên xung quanh vị trí hiện tại
        khi đang cooldown và trong range (thay vì đứng yên).

        Quái sẽ chọn một điểm ngẫu nhiên gần đó và đi chậm tới đó,
        tạo cảm giác "tuần tra" tự nhiên.
        """
        wander_radius = MonsterConfig.IDLE_WANDER_RADIUS
        wander_speed = self._speed * MonsterConfig.IDLE_WANDER_SPEED_RATIO

        self._wander_timer -= 1
        if self._wander_timer <= 0:
            # Chọn điểm wander mới
            angle = random.uniform(0, 2 * math.pi)
            self._wander_target_x = self._x + math.cos(angle) * wander_radius
            self._wander_target_y = self._y + math.sin(angle) * wander_radius
            self._wander_timer = random.randint(20, 50)  # 20-50 frames

        # Di chuyển chậm tới điểm wander
        dist = math.sqrt(
            (self._wander_target_x - self._x) ** 2 +
            (self._wander_target_y - self._y) ** 2
        )
        if dist > 2:  # Chỉ di chuyển nếu chưa tới nơi
            dx = (self._wander_target_x - self._x) / dist
            dy = (self._wander_target_y - self._y) / dist
            self._x += dx * wander_speed
            self._y += dy * wander_speed

        self.clamp_to_screen()

    # === COLLISION ===

    def separate_from_others(self, monsters: list):
        """
        Va chạm cứng AABB giữa các quái.
        Đẩy quái ra khỏi nhau để không chồng lên nhau.

        Args:
            monsters: Danh sách tất cả quái vật
        """
        if not self.is_alive():
            return
        for other in monsters:
            if other is self or not other.is_alive():
                continue
            if self.collides_with(other):
                Entity.resolve_aabb_collision(self, other, 0.5, 0.5)
        self.clamp_to_screen()

    # === RENDERING ===

    def draw(self, surface):
        """
        Vẽ quái vật (chỉ vẽ nếu còn sống).
        Đa hình (Polymorphism): class con sẽ override.

        Args:
            surface: Surface pygame để vẽ lên
        """
        if not self.is_alive():
            return
        super().draw(surface)
