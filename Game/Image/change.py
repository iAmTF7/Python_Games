"""
Module change.py - Biến đổi hình ảnh (scale, rotate, flip)
Xử lý các thao tác transform trên pygame.Surface
"""

import pygame


class ImageChanger:
    """Lớp quản lý việc biến đổi hình ảnh"""

    @staticmethod
    def scale(image: pygame.Surface, new_width: int, new_height: int) -> pygame.Surface:
        """
        Thay đổi kích thước hình ảnh.
        
        Args:
            image: Surface cần scale
            new_width: Chiều rộng mới
            new_height: Chiều cao mới
            
        Returns:
            Surface đã được scale
        """
        return pygame.transform.scale(image, (new_width, new_height))

    @staticmethod
    def rotate(image: pygame.Surface, angle: float) -> pygame.Surface:
        """Xoay hình ảnh theo góc (độ)"""
        return pygame.transform.rotate(image, angle)

    @staticmethod
    def flip(image: pygame.Surface, flip_x: bool = False, flip_y: bool = False) -> pygame.Surface:
        """Lật hình ảnh theo trục X hoặc Y"""
        return pygame.transform.flip(image, flip_x, flip_y)

    @staticmethod
    def set_alpha(image: pygame.Surface, alpha: int) -> pygame.Surface:
        """
        Đặt độ trong suốt cho hình ảnh (0=trong suốt, 255=đặc)
        
        Args:
            image: Surface cần thay đổi
            alpha: Giá trị alpha (0-255)
        """
        image.set_alpha(alpha)
        return image

    @staticmethod
    def colorize(image: pygame.Surface, color: tuple) -> pygame.Surface:
        """Tô màu cho hình ảnh (overlay color)"""
        colored = image.copy()
        colored.fill(color, special_flags=pygame.BLEND_MULT)
        return colored
