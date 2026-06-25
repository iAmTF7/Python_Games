"""
Module melee.py - Quái cận chiến (MeleeMonster)
Kế thừa từ Monster, override attack()/update() để tái hiện hành vi quái
cận chiến kiểu "Soul Knight":

    1. Phát hiện player trong một khoảng cách nhất định (attack_range).
    2. Di chuyển thẳng về phía player.
    3. Khi vào tầm đánh:
        - Dừng lại một chút (wind-up).
        - Vung kiếm theo cung 90-180 độ (random mỗi lần chém).
        - Gây sát thương nếu player nằm trong vùng kiếm.
        - Hồi chiêu rồi tiếp tục đuổi.

Tương thích với tile_map: việc di chuyển trong lúc đuổi (CHASING) vẫn được
kiểm tra va chạm tường giống hành vi gốc của Monster.update().

OOP Principles:
    - Kế thừa (Inheritance): MeleeMonster → Monster → Entity
    - Đa hình (Polymorphism): override attack(), update(), draw()
"""

import math
import random

import pygame

from .base import Monster
from ..Config.settings import Colors, MonsterConfig, Settings


class MeleeMonster(Monster):
    """
    Quái cận chiến - cầm kiếm, đuổi theo player và vung kiếm theo cung.

    State machine của 1 lượt tấn công:
        CHASING -> (vào tầm) -> WINDUP (dừng khựng) -> SLASH (gây damage
        theo cung 90-180 độ random) -> COOLDOWN (hồi chiêu) -> CHASING.

    Kế thừa (Inheritance): Monster → Entity
    Đa hình (Polymorphism):
        - update(): điều khiển toàn bộ state machine (đè update() gốc)
        - attack(): vung kiếm gây damage theo cung tại thời điểm SLASH
        - draw(): vẽ thân quái + kiếm + quạt chém mờ (telegraph + slash)
    """

    # Các state của quái cận chiến
    STATE_CHASING = "chasing"
    STATE_WINDUP = "windup"
    STATE_COOLDOWN = "cooldown"

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
            screen_height=screen_height,
            detect_range=MonsterConfig.MELEE_DETECT_RANGE,
        )
        # Hướng quái đang nhìn/cầm kiếm (đơn vị vector). Mặc định nhìn xuống.
        self._facing_x = 0.0
        self._facing_y = 1.0

        # State machine cho chu trình tấn công.
        self._state = self.STATE_CHASING
        self._windup_timer = 0
        self._slash_flash = 0   # Số frame còn lại để vẽ vệt chém sau khi vung
        # Góc cung chém của lượt vung kiếm hiện tại (random mỗi lần, 90-180 độ)
        self._slash_angle = MonsterConfig.MELEE_SLASH_ANGLE_MIN

    def _update_facing(self, target):
        """Cập nhật hướng quái nhìn về phía mục tiêu."""
        dx = target.x - self._x
        dy = target.y - self._y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            self._facing_x = dx / dist
            self._facing_y = dy / dist

    def move_towards(self, target):
        """Đa hình: vẫn di chuyển như Monster, nhưng luôn quay mặt về target."""
        self._update_facing(target)
        super().move_towards(target)

    def update(self, target, projectiles: list, tile_map=None):
        """
        Đa hình (Polymorphism): Điều khiển toàn bộ hành vi quái cận chiến
        theo state machine (đè update() mặc định của Monster vì cần thêm
        bước wind-up trước khi chém).

        1. CHASING: phát hiện player trong tầm -> đuổi thẳng tới (vẫn áp
           dụng kiểm tra tile_map để không xuyên tường, giống hành vi gốc).
           Vào tầm đánh -> chuyển sang WINDUP (dừng lại, không di chuyển).
        2. WINDUP: đứng yên trong vài frame (chuẩn bị vung kiếm), random
           góc cung chém (90-180 độ).
           Hết wind-up -> vung kiếm (attack), chuyển sang COOLDOWN.
        3. COOLDOWN: hồi chiêu (đứng yên / wander nhẹ).
           Hết cooldown -> chuyển lại CHASING để tiếp tục đuổi.
        """
        if not self.is_alive():
            return

        old_x, old_y = self._x, self._y
        dist = self.distance_to(target)
        target_detected = (
            self._detect_range is None
            or dist <= self._detect_range
        )

        # Keep the visible attack direction responsive while the player is
        # detected, not only when the monster first enters attack range.
        # This makes the sword/telegraph track the player during chase,
        # wind-up, and cooldown idle-wander.
        if target_detected:
            self._update_facing(target)

        if self._state == self.STATE_CHASING:
            if not target_detected:
                # Player ngoài tầm phát hiện -> đứng yên hoàn toàn, chưa
                # phát hiện player, không đuổi và không quay hướng.
                pass
            elif dist <= self._attack_range:
                # Vào tầm đánh -> dừng lại và random góc cung chém
                # (90-180 độ, giống Soul Knight). Hướng đánh tiếp tục được
                # cập nhật mỗi frame trong lúc wind-up nếu player còn trong
                # tầm phát hiện.
                self._state = self.STATE_WINDUP
                self._windup_timer = MonsterConfig.MELEE_WINDUP_FRAMES
                self._slash_angle = random.uniform(
                    MonsterConfig.MELEE_SLASH_ANGLE_MIN,
                    MonsterConfig.MELEE_SLASH_ANGLE_MAX
                )
            else:
                # Đã phát hiện player, chưa vào tầm -> đuổi thẳng tới
                self.move_towards(target)

        elif self._state == self.STATE_WINDUP:
            # Dừng khựng, không di chuyển; hướng đánh vẫn bám theo player
            # nhờ _update_facing() ở đầu update() khi player còn được phát hiện.
            self._windup_timer -= 1
            if self._windup_timer <= 0:
                self.attack(target, projectiles)
                self._current_cooldown = self._cooldown
                self._state = self.STATE_COOLDOWN

        elif self._state == self.STATE_COOLDOWN:
            # Hồi chiêu - đứng yên (idle wander nhẹ) rồi tiếp tục đuổi.
            # Facing vẫn cập nhật mỗi frame khi player còn trong detect range.
            if self._current_cooldown > 0:
                self._current_cooldown -= 1
                self._idle_wander()
            else:
                self._state = self.STATE_CHASING

        if self._slash_flash > 0:
            self._slash_flash -= 1

        # Giữ hành vi gốc: không cho quái di chuyển xuyên tường khi có map.
        if tile_map is not None:
            self._keep_inside_walkable_map(tile_map, old_x, old_y)

    def attack(self, target, projectiles: list):
        """
        Đa hình (Polymorphism): Vung kiếm theo cung 90-180 độ (random).

        Được gọi đúng 1 lần khi wind-up kết thúc. Gây sát thương nếu
        player nằm trong tầm kiếm VÀ trong cung chém theo hướng facing
        hiện tại. Facing được cập nhật mỗi frame trong update() khi player
        còn nằm trong detect range.

        Args:
            target: Mục tiêu tấn công
            projectiles: Không dùng (chỉ để giữ interface chung)
        """
        dx = target.x - self._x
        dy = target.y - self._y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist <= self._attack_range and dist > 0:
            dot = (dx / dist) * self._facing_x + (dy / dist) * self._facing_y
            dot = max(-1.0, min(1.0, dot))
            angle_diff = math.degrees(math.acos(dot))

            half_angle = self._slash_angle / 2
            if angle_diff <= half_angle:
                target.take_damage(self._damage)

        self._slash_flash = MonsterConfig.MELEE_SLASH_FLASH_FRAMES

    def draw(self, surface: pygame.Surface):
        """
        Đa hình (Polymorphism): Vẽ quái cận chiến cầm kiếm.
        Thân quái hình vuông đỏ + thanh kiếm cầm theo hướng nhìn.
        - Khi đang wind-up: vẽ quạt cung chém MỜ (báo hiệu trước hướng và
          độ rộng góc sắp chém, để player có thể né đúng hướng).
        - Khi vừa chém xong: vẽ lại quạt cung chém MỜ trong vài frame.

        Args:
            surface: Surface pygame để vẽ lên
        """
        if not self.is_alive():
            return

        # Wind-up hoặc vừa chém: vẽ quạt cung chém mờ (telegraph) để player
        # biết trước hướng/góc sắp/đang bị chém.
        if self._state == self.STATE_WINDUP or self._slash_flash > 0:
            self._draw_slash_arc(surface)

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

        # Vẽ thanh kiếm trên tay quái, giống cách player cầm kiếm:
        # 1 đường thẳng từ tâm quái, dài MELEE_SWORD_LENGTH, theo hướng nhìn.
        sword_end_x = self._x + self._facing_x * MonsterConfig.MELEE_SWORD_LENGTH
        sword_end_y = self._y + self._facing_y * MonsterConfig.MELEE_SWORD_LENGTH
        pygame.draw.line(
            surface, MonsterConfig.MELEE_SWORD_COLOR,
            (int(self._x), int(self._y)),
            (int(sword_end_x), int(sword_end_y)), 4
        )
        pygame.draw.circle(surface, Colors.WHITE,
                           (int(sword_end_x), int(sword_end_y)), 3)

        self._draw_health_bar(surface)

    def _draw_slash_arc(self, surface: pygame.Surface):
        """Vẽ quạt cung chém MỜ (alpha thấp) hướng theo facing, khi vừa vung kiếm."""
        radius = self._attack_range
        half_angle = math.radians(self._slash_angle / 2)
        facing_angle = math.atan2(self._facing_y, self._facing_x)

        points = [(radius + 2, radius + 2)]
        steps = 14
        for i in range(steps + 1):
            t = -half_angle + (2 * half_angle) * (i / steps)
            angle = facing_angle + t
            px = radius + 2 + math.cos(angle) * radius
            py = radius + 2 + math.sin(angle) * radius
            points.append((px, py))

        diameter = radius * 2 + 4
        arc_surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.polygon(arc_surface, Colors.MELEE_ARC_FILL, points)
        pygame.draw.lines(arc_surface, Colors.MELEE_ARC_BORDER, True, points, 2)
        surface.blit(
            arc_surface,
            (int(self._x) - radius - 2, int(self._y) - radius - 2)
        )
