"""
Module spawner.py - Spawn quái vật + Factory Pattern

OOP Principles:
    - Factory Pattern: tạo quái theo type string
    - Đóng gói (Encapsulation): registry private
    - Bug #3 đã sửa: fallback spawn ở nhiều vị trí khác nhau
"""

import random
import math

from ..Config.settings import Settings


class MonsterSpawner:
    """
    Lớp quản lý spawn quái vật.
    Kết hợp logic spawn + Factory Pattern.

    Factory Pattern:
        - register_monster_class(): đăng ký loại quái
        - create_monster(): tạo quái theo type string
        - create_random_monster(): tạo quái ngẫu nhiên theo level

    Bug #3 đã sửa: Fallback spawn ở nhiều vị trí khác nhau (4 góc + random).
    """

    # 4 góc fallback (Bug #3: không spawn cùng 1 góc nữa)
    _FALLBACK_CORNERS = [
        "top_left",
        "top_right",
        "bottom_left",
        "bottom_right",
    ]

    def __init__(self, screen_width: int = Settings.SCREEN_WIDTH,
                 screen_height: int = Settings.SCREEN_HEIGHT):
        """
        Khởi tạo MonsterSpawner.

        Args:
            screen_width: Chiều rộng màn hình
            screen_height: Chiều cao màn hình
        """
        self._screen_width = screen_width
        self._screen_height = screen_height
        self._monster_classes = {}  # Registry các loại quái (Factory)
        self._fallback_index = 0   # Index góc fallback (Bug #3)

    # === FACTORY PATTERN ===

    def register_monster_class(self, name: str, cls):
        """
        Đăng ký một loại quái vật vào factory.

        Args:
            name: Tên loại quái (ví dụ: "melee", "ranged")
            cls: Class của quái vật
        """
        self._monster_classes[name] = cls

    def create_monster(self, monster_type: str, x: float, y: float):
        """
        Factory Method: Tạo quái vật theo loại.

        Args:
            monster_type: Loại quái ("melee" hoặc "ranged")
            x, y: Vị trí spawn

        Returns:
            Đối tượng quái vật, hoặc None nếu type không hợp lệ
        """
        cls = self._monster_classes.get(monster_type)
        if cls:
            return cls(x, y,
                       screen_width=self._screen_width,
                       screen_height=self._screen_height)
        return None

    def create_random_monster(self, x: float, y: float, level: int):
        """
        Tạo quái vật ngẫu nhiên, xác suất phụ thuộc vào level.
        Level cao hơn → xác suất quái tầm xa tăng (tối đa 60%).

        Args:
            x, y: Vị trí spawn
            level: Level hiện tại

        Returns:
            Đối tượng quái vật ngẫu nhiên
        """
        ranged_chance = min(0.6, 0.2 + (level - 1) * 0.05)

        if random.random() < ranged_chance:
            return self.create_monster("ranged", x, y)
        else:
            return self.create_monster("melee", x, y)

    @property
    def registered_types(self) -> list:
        """Trả về danh sách các loại quái đã đăng ký"""
        return list(self._monster_classes.keys())

    # === SPAWN LOGIC ===

    def get_enemy_count(self, level: int) -> int:
        """
        Tính số lượng quái dựa trên level.

        Args:
            level: Level hiện tại

        Returns:
            Số lượng quái cần spawn
        """
        return Settings.BASE_ENEMY_COUNT + (level - 1) * Settings.ENEMY_INCREASE_PER_LEVEL

    def get_spawn_position(self, target_x: float, target_y: float,
                           existing_positions: list = None) -> tuple:
        """
        Tạo vị trí spawn ngẫu nhiên, đảm bảo:
        - Không quá gần target
        - Không quá gần quái đã spawn
        Bug #3 đã sửa: Fallback spawn ở các góc khác nhau.

        Args:
            target_x, target_y: Vị trí mục tiêu cần tránh
            existing_positions: Danh sách vị trí quái đã spawn

        Returns:
            Tuple (x, y) vị trí spawn
        """
        if existing_positions is None:
            existing_positions = []

        margin = Settings.SPAWN_MARGIN
        min_dist = Settings.SPAWN_MIN_DISTANCE_FROM_TARGET
        min_monster_dist = Settings.SPAWN_MIN_DISTANCE_BETWEEN

        for _ in range(Settings.SPAWN_MAX_ATTEMPTS):
            x = random.randint(margin, self._screen_width - margin)
            y = random.randint(margin, self._screen_height - margin)

            dist = math.sqrt((x - target_x) ** 2 + (y - target_y) ** 2)
            if dist < min_dist:
                continue

            too_close = False
            for mx, my in existing_positions:
                if math.sqrt((x - mx) ** 2 + (y - my) ** 2) < min_monster_dist:
                    too_close = True
                    break

            if not too_close:
                return (x, y)

        # === BUG #3 FIX: Fallback spawn ở các góc khác nhau ===
        corner = self._FALLBACK_CORNERS[self._fallback_index % len(self._FALLBACK_CORNERS)]
        self._fallback_index += 1

        offset_x = random.randint(0, 40)
        offset_y = random.randint(0, 40)

        if corner == "top_left":
            return (margin + offset_x, margin + offset_y)
        elif corner == "top_right":
            return (self._screen_width - margin - offset_x, margin + offset_y)
        elif corner == "bottom_left":
            return (margin + offset_x, self._screen_height - margin - offset_y)
        else:
            return (self._screen_width - margin - offset_x,
                    self._screen_height - margin - offset_y)

    def spawn_wave(self, level: int,
                   target_x: float, target_y: float) -> list:
        """
        Spawn một wave quái cho level hiện tại.

        Args:
            level: Level hiện tại
            target_x, target_y: Vị trí target cần tránh khi spawn

        Returns:
            Danh sách quái vật đã spawn
        """
        enemy_count = self.get_enemy_count(level)
        monsters = []
        existing_positions = []

        for _ in range(enemy_count):
            x, y = self.get_spawn_position(target_x, target_y,
                                           existing_positions)
            monster = self.create_random_monster(x, y, level)
            if monster:
                monsters.append(monster)
                existing_positions.append((x, y))

        return monsters

    def reset_fallback(self):
        """Reset index fallback về 0"""
        self._fallback_index = 0
