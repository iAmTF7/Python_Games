"""
Module close.py - Giải phóng tài nguyên hình ảnh
Quản lý bộ nhớ và dọn dẹp khi không cần sử dụng
"""

import pygame


class ImageCloser:
    """Lớp quản lý việc giải phóng tài nguyên hình ảnh"""

    @staticmethod
    def close_image(image_opener, name: str) -> bool:
        """
        Giải phóng một hình ảnh cụ thể khỏi bộ nhớ.
        
        Args:
            image_opener: Đối tượng ImageOpener
            name: Tên hình ảnh cần giải phóng
            
        Returns:
            True nếu giải phóng thành công
        """
        if name in image_opener._images:
            del image_opener._images[name]
            print(f"[ImageCloser] Đã giải phóng: {name}")
            return True
        return False

    @staticmethod
    def close_all(image_opener):
        """Giải phóng tất cả hình ảnh"""
        count = len(image_opener._images)
        image_opener._images.clear()
        print(f"[ImageCloser] Đã giải phóng {count} hình ảnh")

    @staticmethod
    def get_memory_usage(image_opener) -> dict:
        """Trả về thông tin bộ nhớ sử dụng bởi các hình ảnh"""
        info = {}
        for name, img in image_opener._images.items():
            size = img.get_size()
            info[name] = {
                "width": size[0],
                "height": size[1],
                "bytes": size[0] * size[1] * 4  # Ước tính RGBA
            }
        return info
