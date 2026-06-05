import pygame
import math
from .entity import Entity
from .projectile import Projectile

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
PURPLE = (128, 0, 128)

class Monster(Entity):
    """
    Lớp cơ sở cho quái vật.
    Kế thừa từ Entity, sử dụng Polymorphism qua phương thức attack().
    """
    def __init__(self, x, y, hp, damage, attack_range, speed, cooldown, color, size):
        super().__init__(x, y, hp, speed, color, size)
        self._damage = damage
        self._attack_range = attack_range
        self._cooldown = cooldown
        self._current_cooldown = 0

    def update(self, player, projectiles):
        """Cập nhật trạng thái quái: di chuyển và tấn công"""
        if not self.is_alive():
            return

        if self._current_cooldown > 0:
            self._current_cooldown -= 1

        dist = self.distance_to(player)

        if dist <= self._attack_range:
            if self._current_cooldown <= 0:
                self.attack(player, projectiles)
                self._current_cooldown = self._cooldown
        else:
            self.move_towards(player)

    def move_towards(self, target):
        """Di chuyển về phía mục tiêu"""
        dist = self.distance_to(target)
        if dist == 0:
            return
        dx = (target.x - self._x) / dist
        dy = (target.y - self._y) / dist
        self._x += dx * self._speed
        self._y += dy * self._speed

    def separate_from_others(self, monsters):
        """
        Va chạm cứng AABB giữa các quái.
        Đẩy quái ra khỏi nhau để không bao giờ chồng lên nhau.
        
        Args:
            monsters: Danh sách tất cả quái vật
        """
        if not self.is_alive():
            return
        for other in monsters:
            if other is self or not other.is_alive():
                continue
            if self.collides_with(other):
                # Đẩy đều 2 bên (50/50)
                Entity.resolve_aabb_collision(self, other, 0.5, 0.5)
        # Giữ quái trong màn hình
        self.clamp_to_screen()

    def attack(self, target, projectiles):
        """Đa hình: Phương thức này sẽ được ghi đè ở class con"""
        pass

    def draw(self, surface):
        """Vẽ quái vật (chỉ vẽ nếu còn sống)"""
        if not self.is_alive():
            return
        super().draw(surface)

class MeleeMonster(Monster):
    """
    Quái cận chiến - gây sát thương trực tiếp.
    Override attack() → đánh trực tiếp target.
    """
    def __init__(self, x, y):
        super().__init__(x, y, hp=50, damage=10, attack_range=35,
                         speed=2.5, cooldown=60, color=RED, size=30)

    def attack(self, target, projectiles):
        """Đa hình: Tấn công cận chiến - gây sát thương trực tiếp"""
        target.take_damage(self._damage)

    def draw(self, surface):
        """Vẽ quái cận chiến (hình vuông đỏ)"""
        if not self.is_alive():
            return

        # Vẽ vòng tròn tầm đánh khi đang tấn công (giống player)
        if self._current_cooldown > self._cooldown - 10:
            attack_circle_surface = pygame.Surface(
                (self._attack_range * 2 + 4, self._attack_range * 2 + 4),
                pygame.SRCALPHA
            )
            # Vòng tròn đỏ mờ
            pygame.draw.circle(
                attack_circle_surface, (255, 80, 80, 60),
                (self._attack_range + 2, self._attack_range + 2),
                self._attack_range, 0
            )
            # Viền vòng tròn đỏ
            pygame.draw.circle(
                attack_circle_surface, (255, 50, 50, 150),
                (self._attack_range + 2, self._attack_range + 2),
                self._attack_range, 2
            )
            surface.blit(
                attack_circle_surface,
                (int(self._x) - self._attack_range - 2,
                 int(self._y) - self._attack_range - 2)
            )

        rect = pygame.Rect(self._x - self._size/2, self._y - self._size/2,
                           self._size, self._size)
        pygame.draw.rect(surface, self._color, rect)
        # Vẽ dấu X để phân biệt
        pygame.draw.line(surface, BLACK, 
                        (self._x - 8, self._y - 8), 
                        (self._x + 8, self._y + 8), 2)
        pygame.draw.line(surface, BLACK, 
                        (self._x + 8, self._y - 8), 
                        (self._x - 8, self._y + 8), 2)
        self.draw_health_bar(surface)

class RangedMonster(Monster):
    """
    Quái tầm xa - bắn đạn ma thuật.
    Override attack() → sinh ra Projectile.
    Override move_towards() → giữ khoảng cách an toàn.
    """
    def __init__(self, x, y):
        super().__init__(x, y, hp=30, damage=15, attack_range=300,
                         speed=1.0, cooldown=90, color=PURPLE, size=30)

    def move_towards(self, target):
        """
        Đa hình: Di chuyển thông minh - giữ khoảng cách.
        Nếu xa quá thì tiến lại gần, nếu gần quá thì lùi lại.
        """
        dist = self.distance_to(target)
        if dist > self._attack_range:
            super().move_towards(target)
        elif dist < self._attack_range - 80:
            if dist == 0:
                return
            dx = (self._x - target.x) / dist
            dy = (self._y - target.y) / dist
            self._x += dx * self._speed
            self._y += dy * self._speed

    def attack(self, target, projectiles):
        """Đa hình: Tấn công tầm xa - bắn đạn ma thuật"""
        proj = Projectile(self._x, self._y, target.x, target.y, 
                         self._damage, speed=6.0)
        projectiles.append(proj)

    def draw(self, surface):
        """Vẽ quái tầm xa (hình vuông tím với dấu +)"""
        if not self.is_alive():
            return

        rect = pygame.Rect(self._x - self._size/2, self._y - self._size/2,
                           self._size, self._size)
        pygame.draw.rect(surface, self._color, rect)
        # Vẽ dấu + để phân biệt
        pygame.draw.line(surface, WHITE,
                        (self._x, self._y - 10),
                        (self._x, self._y + 10), 2)
        pygame.draw.line(surface, WHITE,
                        (self._x - 10, self._y),
                        (self._x + 10, self._y), 2)
        self.draw_health_bar(surface)
