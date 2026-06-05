"""
Module over.py - Xử lý khi game over hoặc hoàn thành level
Quản lý trạng thái kết thúc, điểm số, và restart
"""

import pygame


class LevelOver:
    """
    Lớp quản lý trạng thái kết thúc game/level.
    Xử lý hiển thị game over, thống kê, và restart.
    """

    def __init__(self):
        self._is_game_over = False
        self._is_level_complete = False
        self._score = 0
        self._kills = 0
        self._highest_level = 1

    @property
    def is_game_over(self) -> bool:
        return self._is_game_over

    @property
    def is_level_complete(self) -> bool:
        return self._is_level_complete

    @property
    def score(self) -> int:
        return self._score

    @property
    def kills(self) -> int:
        return self._kills

    @property
    def highest_level(self) -> int:
        return self._highest_level

    def add_kill(self, points: int = 10):
        """Thêm kill và điểm"""
        self._kills += 1
        self._score += points

    def check_level_complete(self, monsters: list) -> bool:
        """
        Kiểm tra xem đã diệt hết quái chưa.
        
        Args:
            monsters: Danh sách quái vật hiện tại
            
        Returns:
            True nếu tất cả quái đã chết
        """
        all_dead = all(not m.is_alive() for m in monsters)
        if all_dead and not self._is_level_complete:
            self._is_level_complete = True
            print(f"[LevelOver] Hoàn thành level! Tổng kill: {self._kills}")
        return all_dead

    def check_game_over(self, player) -> bool:
        """
        Kiểm tra xem player đã chết chưa.
        
        Args:
            player: Đối tượng Player
            
        Returns:
            True nếu player đã chết
        """
        if not player.is_alive():
            self._is_game_over = True
            return True
        return False

    def update_highest_level(self, level: int):
        """Cập nhật level cao nhất đạt được"""
        if level > self._highest_level:
            self._highest_level = level

    def draw_game_over(self, surface, font_large, font_small):
        """
        Vẽ màn hình Game Over.
        
        Args:
            surface: Màn hình pygame
            font_large: Font lớn cho tiêu đề
            font_small: Font nhỏ cho thống kê
        """
        width = surface.get_width()
        height = surface.get_height()

        # Overlay tối
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        # Tiêu đề GAME OVER
        title = font_large.render("GAME OVER", True, (255, 50, 50))
        title_rect = title.get_rect(center=(width // 2, height // 2 - 60))
        surface.blit(title, title_rect)

        # Thống kê
        stats = [
            f"Level cao nhất: {self._highest_level}",
            f"Tổng kill: {self._kills}",
            f"Điểm số: {self._score}",
            "",
            "Nhấn R để chơi lại | ESC để thoát"
        ]

        for i, text in enumerate(stats):
            rendered = font_small.render(text, True, (255, 255, 255))
            rect = rendered.get_rect(center=(width // 2, height // 2 + i * 30))
            surface.blit(rendered, rect)

    def draw_level_complete(self, surface, font_large, font_small, level: int):
        """
        Vẽ thông báo hoàn thành level.
        
        Args:
            surface: Màn hình pygame
            font_large: Font lớn
            font_small: Font nhỏ
            level: Level vừa hoàn thành
        """
        width = surface.get_width()
        height = surface.get_height()

        # Tiêu đề
        title = font_large.render(f"LEVEL {level} COMPLETE!", True, (50, 255, 50))
        title_rect = title.get_rect(center=(width // 2, height // 2 - 30))
        surface.blit(title, title_rect)

        # Hướng dẫn
        hint = font_small.render("Đi vào Portal để sang map tiếp theo!", True, (255, 255, 255))
        hint_rect = hint.get_rect(center=(width // 2, height // 2 + 20))
        surface.blit(hint, hint_rect)

    def reset_level_state(self):
        """Reset trạng thái cho level mới"""
        self._is_level_complete = False

    def reset_all(self):
        """Reset toàn bộ trạng thái game"""
        self._is_game_over = False
        self._is_level_complete = False
        self._score = 0
        self._kills = 0
        self._highest_level = 1
