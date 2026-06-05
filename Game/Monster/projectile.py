import pygame
import math

YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

class Projectile:
    """Đạn ma thuật bắn bởi quái tầm xa"""
    def __init__(self, x, y, target_x, target_y, damage, speed):
        self.x = x
        self.y = y
        self.damage = damage
        self.speed = speed
        self.radius = 6

        # Tính hướng bay dựa trên góc atan2
        angle = math.atan2(target_y - y, target_x - x)
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed

    def update(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius)
        # Vẽ viền sáng
        pygame.draw.circle(surface, ORANGE, (int(self.x), int(self.y)), self.radius, 1)
