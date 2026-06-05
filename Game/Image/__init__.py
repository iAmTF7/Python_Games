# Image Sub-Package
# Quản lý toàn bộ hình ảnh/sprite trong game

"""
Image Package quản lý:
    - open: Mở/tải hình ảnh từ file
    - change: Thay đổi/biến đổi hình ảnh (scale, rotate, flip)
    - close: Giải phóng tài nguyên hình ảnh
"""

from Game.Image.open import ImageOpener
from Game.Image.change import ImageChanger
from Game.Image.close import ImageCloser

__all__ = ['ImageOpener', 'ImageChanger', 'ImageCloser']
