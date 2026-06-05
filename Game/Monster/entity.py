import pygame
import math

# Kích thước màn hình mặc định
WIDTH, HEIGHT = 800, 600

# Màu sắc
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

class Entity:
    """
    Lớp cha cho tất cả thực thể trong game.
    Sử dụng Encapsulation: thuộc tính private với property getter.
    Hỗ trợ va chạm cứng AABB (Axis-Aligned Bounding Box).
    """
    def __init__(self, x: float, y: float, hp: int, speed: float, color, size: int):
        self._x = x
        self._y = y
        self._hp = hp
        self._max_hp = hp
        self._speed = speed
        self._color = color
        self._size = size

    @property
    def x(self): return self._x

    @property
    def y(self): return self._y

    @property
    def hp(self): return self._hp

    @property
    def max_hp(self): return self._max_hp

    @property
    def size(self): return self._size

    def get_rect(self) -> pygame.Rect:
        """Trả về hitbox AABB của entity"""
        return pygame.Rect(self._x - self._size / 2, self._y - self._size / 2,
                           self._size, self._size)

    def collides_with(self, other) -> bool:
        """Kiểm tra va chạm AABB với entity khác"""
        return self.get_rect().colliderect(other.get_rect())

    @staticmethod
    def resolve_aabb_collision(entity_a, entity_b, push_ratio_a=0.5, push_ratio_b=0.5):
        """
        Giải quyết va chạm cứng AABB giữa 2 entity.
        Đẩy chúng ra khỏi nhau theo trục có overlap nhỏ nhất (giống game thật).
        
        Args:
            entity_a, entity_b: Hai entity đang va chạm
            push_ratio_a: Tỉ lệ đẩy entity_a (0.0 = không đẩy, 1.0 = đẩy hết)
            push_ratio_b: Tỉ lệ đẩy entity_b
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
            # Đẩy theo trục X
            if entity_a._x < entity_b._x:
                entity_a._x -= overlap_x * push_ratio_a
                entity_b._x += overlap_x * push_ratio_b
            else:
                entity_a._x += overlap_x * push_ratio_a
                entity_b._x -= overlap_x * push_ratio_b
        else:
            # Đẩy theo trục Y
            if entity_a._y < entity_b._y:
                entity_a._y -= overlap_y * push_ratio_a
                entity_b._y += overlap_y * push_ratio_b
            else:
                entity_a._y += overlap_y * push_ratio_a
                entity_b._y -= overlap_y * push_ratio_b

    def clamp_to_screen(self):
        """Giữ entity trong phạm vi màn hình"""
        self._x = max(self._size / 2, min(WIDTH - self._size / 2, self._x))
        self._y = max(self._size / 2, min(HEIGHT - self._size / 2, self._y))

    def take_damage(self, amount: int):
        """Nhận sát thương"""
        self._hp -= amount
        if self._hp < 0:
            self._hp = 0

    def is_alive(self):
        """Kiểm tra còn sống không"""
        return self._hp > 0

    def distance_to(self, other):
        """Tính khoảng cách tới thực thể khác (dùng Euclidean)"""
        return math.sqrt((self._x - other.x)**2 + (self._y - other.y)**2)

    def draw(self, surface):
        """Vẽ thực thể lên màn hình"""
        rect = pygame.Rect(self._x - self._size/2, self._y - self._size/2, 
                           self._size, self._size)
        pygame.draw.rect(surface, self._color, rect)
        self.draw_health_bar(surface)

    def draw_health_bar(self, surface):
        """Vẽ thanh máu phía trên entity"""
        bar_width = self._size
        bar_height = 5
        fill = (self._hp / self._max_hp) * bar_width
        outline_rect = pygame.Rect(self._x - self._size/2, 
                                   self._y - self._size/2 - 10, 
                                   bar_width, bar_height)
        fill_rect = pygame.Rect(self._x - self._size/2, 
                                self._y - self._size/2 - 10, 
                                fill, bar_height)
        pygame.draw.rect(surface, RED, outline_rect)
        pygame.draw.rect(surface, GREEN, fill_rect)

class Player(Entity):
    """
    Lớp người chơi (Hiệp sĩ).
    Kế thừa Entity, thêm khả năng tấn công cận chiến.
    """
    def __init__(self, x, y):
        super().__init__(x, y, hp=100, speed=4.0, color=BLUE, size=30)
        self._attack_damage = 20
        self._attack_range = 50
        self._attack_cooldown = 0
        self._attack_cooldown_max = 20

    @property
    def attack_damage(self): return self._attack_damage

    @property
    def attack_range(self): return self._attack_range

    def update(self):
        """Cập nhật vị trí player theo input bàn phím"""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self._x -= self._speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self._x += self._speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self._y -= self._speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self._y += self._speed

        # Giữ player trong phạm vi màn hình
        self.clamp_to_screen()

        # Giảm cooldown tấn công
        if self._attack_cooldown > 0:
            self._attack_cooldown -= 1

    def resolve_collision_with_monsters(self, monsters):
        """
        Va chạm cứng: Player bị đẩy ra khi chạm quái.
        Player bị đẩy 100%, quái không bị dịch (giống tường cứng).
        Lặp nhiều lần để giải quyết trường hợp bị kẹp giữa nhiều quái.
        """
        for _ in range(3):  # Lặp 3 lần để giải quyết chồng chéo
            for m in monsters:
                if not m.is_alive():
                    continue
                if self.collides_with(m):
                    # Player bị đẩy 70%, quái bị đẩy 30%
                    Entity.resolve_aabb_collision(self, m, push_ratio_a=0.7, push_ratio_b=0.3)
            self.clamp_to_screen()

    def attack_monsters(self, monsters, level_over):
        """
        Tấn công quái trong phạm vi (nhấn Space).
        
        Args:
            monsters: Danh sách quái vật
            level_over: Đối tượng LevelOver để tính kill
        """
        if self._attack_cooldown > 0:
            return

        for m in monsters:
            if m.is_alive() and self.distance_to(m) <= self._attack_range:
                m.take_damage(self._attack_damage)
                if not m.is_alive():
                    level_over.add_kill(points=10 + m._damage)
        
        self._attack_cooldown = self._attack_cooldown_max

    def draw(self, surface):
        """Vẽ player với hiệu ứng"""
        # Vẽ vòng tấn công (khi đang attack)
        if self._attack_cooldown > self._attack_cooldown_max - 5:
            pygame.draw.circle(surface, (100, 100, 255, 100), 
                             (int(self._x), int(self._y)), 
                             self._attack_range, 2)
        
        # Vẽ thân player
        rect = pygame.Rect(self._x - self._size/2, self._y - self._size/2, 
                           self._size, self._size)
        pygame.draw.rect(surface, self._color, rect)
        pygame.draw.rect(surface, WHITE, rect, 2)  # Viền trắng
        self.draw_health_bar(surface)

    def reset(self, x, y):
        """Reset player về vị trí và trạng thái ban đầu"""
        self._x = x
        self._y = y
        self._hp = self._max_hp
        self._attack_cooldown = 0
