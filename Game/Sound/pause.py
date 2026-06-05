"""
Module pause.py - Tạm dừng và tiếp tục âm thanh
"""

import pygame


class SoundPauser:
    """Lớp quản lý việc tạm dừng/tiếp tục âm thanh"""

    def __init__(self):
        self._is_paused = False

    def pause_all(self):
        """Tạm dừng tất cả âm thanh"""
        pygame.mixer.pause()
        pygame.mixer.music.pause()
        self._is_paused = True

    def resume_all(self):
        """Tiếp tục phát tất cả âm thanh"""
        pygame.mixer.unpause()
        pygame.mixer.music.unpause()
        self._is_paused = False

    def stop_all(self):
        """Dừng hoàn toàn tất cả âm thanh"""
        pygame.mixer.stop()
        pygame.mixer.music.stop()
        self._is_paused = False

    @property
    def is_paused(self) -> bool:
        return self._is_paused
