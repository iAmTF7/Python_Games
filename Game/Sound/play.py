"""
Module play.py - Phát âm thanh trong game
Hỗ trợ phát sound effect và background music
"""

import pygame


class SoundPlayer:
    """Lớp quản lý việc phát âm thanh"""

    def __init__(self, sound_loader):
        """
        Khởi tạo SoundPlayer với một SoundLoader.
        
        Args:
            sound_loader: Đối tượng SoundLoader đã tải sẵn âm thanh
        """
        self._loader = sound_loader  # Composition: sử dụng SoundLoader
        self._volume = 0.7
        self._is_muted = False

    def play(self, name: str, loops: int = 0):
        """
        Phát âm thanh theo tên.
        
        Args:
            name: Tên âm thanh đã được load
            loops: Số lần lặp (-1 = lặp vô hạn, 0 = phát 1 lần)
        """
        if self._is_muted:
            return
        sound = self._loader.get_sound(name)
        if sound:
            sound.set_volume(self._volume)
            sound.play(loops=loops)
        else:
            # Không có âm thanh thì bỏ qua (silent mode)
            pass

    def play_bgm(self, filepath: str, loops: int = -1):
        """Phát nhạc nền từ file"""
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.set_volume(self._volume)
            pygame.mixer.music.play(loops=loops)
        except pygame.error:
            pass  # Bỏ qua nếu không có file nhạc

    def set_volume(self, volume: float):
        """Đặt âm lượng (0.0 - 1.0)"""
        self._volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self._volume)

    def mute(self):
        """Tắt tiếng"""
        self._is_muted = True
        pygame.mixer.music.set_volume(0)

    def unmute(self):
        """Bật tiếng"""
        self._is_muted = False
        pygame.mixer.music.set_volume(self._volume)

    @property
    def volume(self) -> float:
        return self._volume

    @property
    def is_muted(self) -> bool:
        return self._is_muted
