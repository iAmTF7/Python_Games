"""
Module load.py - Tải và quản lý tài nguyên âm thanh
Sử dụng pygame.mixer để load các file âm thanh (.wav, .ogg, .mp3)
"""

import pygame
import os


class SoundLoader:
    """Lớp quản lý việc tải âm thanh từ file"""

    def __init__(self):
        """Khởi tạo mixer và dictionary lưu trữ âm thanh"""
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        self._sounds = {}  # Encapsulation: dict private lưu trữ sound

    def load_sound(self, name: str, filepath: str) -> bool:
        """
        Tải một file âm thanh và lưu vào dictionary.
        
        Args:
            name: Tên định danh cho âm thanh
            filepath: Đường dẫn tới file âm thanh
            
        Returns:
            True nếu tải thành công, False nếu thất bại
        """
        try:
            if os.path.exists(filepath):
                self._sounds[name] = pygame.mixer.Sound(filepath)
                print(f"[SoundLoader] Đã tải âm thanh: {name}")
                return True
            else:
                print(f"[SoundLoader] Không tìm thấy file: {filepath}")
                return False
        except pygame.error as e:
            print(f"[SoundLoader] Lỗi khi tải {name}: {e}")
            return False

    def get_sound(self, name: str):
        """Lấy đối tượng Sound theo tên"""
        return self._sounds.get(name, None)

    def load_default_sounds(self):
        """Tải các âm thanh mặc định cho game (nếu có file)"""
        default_sounds = {
            "attack": "assets/sounds/attack.wav",
            "hit": "assets/sounds/hit.wav",
            "portal": "assets/sounds/portal.wav",
            "death": "assets/sounds/death.wav",
            "level_up": "assets/sounds/level_up.wav",
        }
        for name, path in default_sounds.items():
            self.load_sound(name, path)

    @property
    def loaded_sounds(self) -> list:
        """Trả về danh sách tên các âm thanh đã tải"""
        return list(self._sounds.keys())
