"""
Module load.py - Tải dữ liệu level (quái, map, cấu hình)
Factory Pattern: Tạo quái vật dựa trên loại và level
"""

import random
import math


class LevelLoader:
    """
    Lớp tải và tạo dữ liệu cho level.
    Sử dụng Factory Pattern để tạo các loại quái vật khác nhau.
    """

    # Màu sắc cho map background theo level
    MAP_COLORS = [
        (200, 200, 200),  # Level 1: Xám nhạt
        (180, 220, 180),  # Level 2: Xanh lá nhạt
        (220, 200, 180),  # Level 3: Nâu nhạt (sa mạc)
        (180, 180, 220),  # Level 4: Tím nhạt
        (220, 180, 180),  # Level 5: Đỏ nhạt (hell)
        (160, 200, 220),  # Level 6: Xanh dương nhạt (ice)
        (200, 200, 160),  # Level 7: Vàng nhạt
        (180, 160, 200),  # Level 8: Tím đậm hơn
    ]

    # Tên map theo level
    MAP_NAMES = [
        "Đồng Cỏ", "Rừng Xanh", "Sa Mạc", "Hang Động",
        "Địa Ngục", "Vùng Băng", "Tháp Cổ", "Lâu Đài Tối"
    ]

    def __init__(self):
        self._monster_classes = {}  # Registry các loại quái

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
            Đối tượng quái vật
        """
        cls = self._monster_classes.get(monster_type)
        if cls:
            return cls(x, y)
        return None

    def create_random_monster(self, x: float, y: float, level: int):
        """
        Tạo quái vật ngẫu nhiên, xác suất phụ thuộc vào level.
        Level cao hơn → xác suất quái tầm xa tăng.
        
        Args:
            x, y: Vị trí spawn
            level: Level hiện tại
            
        Returns:
            Đối tượng quái vật ngẫu nhiên
        """
        # Tỷ lệ quái ranged tăng dần theo level (tối đa 60%)
        ranged_chance = min(0.6, 0.2 + (level - 1) * 0.05)
        
        if random.random() < ranged_chance:
            return self.create_monster("ranged", x, y)
        else:
            return self.create_monster("melee", x, y)

    def get_map_color(self, level: int) -> tuple:
        """Lấy màu nền map theo level"""
        index = (level - 1) % len(self.MAP_COLORS)
        return self.MAP_COLORS[index]

    def get_map_name(self, level: int) -> str:
        """Lấy tên map theo level"""
        index = (level - 1) % len(self.MAP_NAMES)
        return self.MAP_NAMES[index]

    @property
    def registered_types(self) -> list:
        """Trả về danh sách các loại quái đã đăng ký"""
        return list(self._monster_classes.keys())
