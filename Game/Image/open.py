"""
Module open.py - Mở và tải hình ảnh từ file
Sử dụng pygame.image để load sprite và texture
"""

import pygame
import os


class ImageOpener:
    """Lớp quản lý việc mở/tải hình ảnh"""

    def __init__(self):
        """Khởi tạo dictionary lưu trữ hình ảnh"""
        self._images = {}  # Encapsulation: dict private

    def open_image(self, name: str, filepath: str, convert_alpha: bool = True) -> bool:
        """
        Mở một file hình ảnh và lưu vào dictionary.
        
        Args:
            name: Tên định danh cho hình ảnh
            filepath: Đường dẫn tới file hình ảnh
            convert_alpha: Có chuyển đổi alpha channel không
            
        Returns:
            True nếu tải thành công, False nếu thất bại
        """
        try:
            if os.path.exists(filepath):
                image = pygame.image.load(filepath)
                if convert_alpha:
                    image = image.convert_alpha()
                else:
                    image = image.convert()
                self._images[name] = image
                print(f"[ImageOpener] Đã tải hình ảnh: {name}")
                return True
            else:
                print(f"[ImageOpener] Không tìm thấy file: {filepath}")
                return False
        except pygame.error as e:
            print(f"[ImageOpener] Lỗi khi tải {name}: {e}")
            return False

    def get_image(self, name: str):
        """Lấy đối tượng Surface theo tên"""
        return self._images.get(name, None)

    def create_colored_surface(self, name: str, width: int, height: int, color: tuple):
        """Tạo một surface màu đơn giản (dùng khi không có file ảnh)"""
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill(color)
        self._images[name] = surface
        return surface

    @property
    def loaded_images(self) -> list:
        """Trả về danh sách tên các hình ảnh đã tải"""
        return list(self._images.keys())
