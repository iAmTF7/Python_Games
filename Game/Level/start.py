"""
Module start.py - Khởi tạo và bắt đầu level mới
Quản lý việc tạo level, spawn quái, và cấu hình ban đầu
"""

import random


class LevelStarter:
    """
    Lớp khởi tạo level mới.
    Quản lý việc spawn quái random theo level hiện tại.
    """

    def __init__(self, screen_width: int, screen_height: int):
        self._screen_width = screen_width
        self._screen_height = screen_height
        self._current_level = 1
        self._base_enemy_count = 3  # Số quái cơ bản ở level 1
        self._margin = 60  # Khoảng cách tối thiểu từ viền

    @property
    def current_level(self) -> int:
        return self._current_level

    @current_level.setter
    def current_level(self, value: int):
        self._current_level = max(1, value)

    def get_enemy_count(self) -> int:
        """
        Tính số lượng quái dựa trên level hiện tại.
        Mỗi level tăng thêm quái (Đa hình qua công thức).
        """
        return self._base_enemy_count + (self._current_level - 1) * 2

    def get_random_spawn_position(self, player_x: float, player_y: float, 
                                   min_distance: float = 150,
                                   existing_positions: list = None,
                                   min_monster_distance: float = 50) -> tuple:
        """
        Tạo vị trí spawn ngẫu nhiên cho quái, đảm bảo không quá gần player
        và không quá gần các quái đã spawn.
        
        Args:
            player_x: Tọa độ X của player
            player_y: Tọa độ Y của player
            min_distance: Khoảng cách tối thiểu từ player
            existing_positions: Danh sách vị trí (x, y) của quái đã spawn
            min_monster_distance: Khoảng cách tối thiểu giữa các quái
            
        Returns:
            Tuple (x, y) vị trí spawn
        """
        import math
        if existing_positions is None:
            existing_positions = []
        for _ in range(100):  # Thử tối đa 100 lần
            x = random.randint(self._margin, self._screen_width - self._margin)
            y = random.randint(self._margin, self._screen_height - self._margin)
            dist = math.sqrt((x - player_x)**2 + (y - player_y)**2)
            if dist < min_distance:
                continue
            # Kiểm tra khoảng cách với các quái đã spawn
            too_close = False
            for mx, my in existing_positions:
                if math.sqrt((x - mx)**2 + (y - my)**2) < min_monster_distance:
                    too_close = True
                    break
            if not too_close:
                return (x, y)
        # Fallback: spawn ở góc
        return (self._margin, self._margin)

    def start_level(self, level_loader, player_x: float, player_y: float) -> list:
        """
        Bắt đầu level mới: spawn quái random.
        
        Args:
            level_loader: Đối tượng LevelLoader để tạo quái
            player_x: Vị trí X của player
            player_y: Vị trí Y của player
            
        Returns:
            Danh sách quái vật cho level hiện tại
        """
        enemy_count = self.get_enemy_count()
        monsters = []
        existing_positions = []

        for _ in range(enemy_count):
            x, y = self.get_random_spawn_position(
                player_x, player_y, 
                existing_positions=existing_positions)
            monster = level_loader.create_random_monster(x, y, self._current_level)
            monsters.append(monster)
            existing_positions.append((x, y))

        print(f"[LevelStarter] Level {self._current_level} - Spawn {enemy_count} quái")
        return monsters

    def next_level(self):
        """Chuyển sang level tiếp theo"""
        self._current_level += 1
        print(f"[LevelStarter] Chuyển sang Level {self._current_level}")

    def reset(self):
        """Reset về level 1"""
        self._current_level = 1
