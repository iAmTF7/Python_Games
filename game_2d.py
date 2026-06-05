"""
Soul Knight - Monster Combat Demo (2D)
Game flow theo cơ chế:
    Spawn quái random → Player combat → Diệt hết quái →
    Portal mở → Qua map mới → Spawn nhiều quái hơn →
    Lặp tới khi player chết

Sử dụng cấu trúc Package:
    Game/
    ├── __init__.py
    ├── Sound/ (load, play, pause)
    ├── Image/ (open, change, close)
    └── Level/ (start, load, over)
"""

import pygame
import math
import random
import sys
import os

# Fix encoding cho console Windows (hỗ trợ tiếng Việt)
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Thêm thư mục gốc vào path để import package Game
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Game.Level.start import LevelStarter
from Game.Level.load import LevelLoader
from Game.Level.over import LevelOver
from Game.Sound.load import SoundLoader
from Game.Sound.play import SoundPlayer
from Game.Sound.pause import SoundPauser
from Game.Image.open import ImageOpener
from Game.Image.change import ImageChanger
from Game.Image.close import ImageCloser
from Game.Monster.entity import Player
from Game.Monster.monster import MeleeMonster, RangedMonster

# Khởi tạo pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Soul Knight - Monster Combat Demo (2D)")
clock = pygame.time.Clock()

# Màu sắc
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
DARK_GREEN = (0, 180, 0)

# Font chữ
font_large = pygame.font.SysFont("Arial", 42, bold=True)
font_medium = pygame.font.SysFont("Arial", 28)
font_small = pygame.font.SysFont("Arial", 20)
font_tiny = pygame.font.SysFont("Arial", 16)



# ============================================================
# LỚP PORTAL (Cổng dịch chuyển)
# ============================================================
class Portal:
    """
    Cổng dịch chuyển - xuất hiện khi diệt hết quái.
    Player đi vào portal để qua map mới.
    """
    def __init__(self, x, y):
        self._x = x
        self._y = y
        self._radius = 25
        self._active = False
        self._animation_angle = 0
        self._pulse = 0

    @property
    def x(self): return self._x

    @property
    def y(self): return self._y

    @property
    def active(self): return self._active

    def activate(self):
        """Kích hoạt portal khi diệt hết quái"""
        self._active = True
        print("[Portal] Portal đã mở!")

    def deactivate(self):
        """Tắt portal"""
        self._active = False

    def check_collision(self, player) -> bool:
        """Kiểm tra player có chạm portal không"""
        if not self._active:
            return False
        dist = math.sqrt((self._x - player.x)**2 + (self._y - player.y)**2)
        return dist < self._radius + player.size / 2

    def update(self):
        """Cập nhật animation portal"""
        if self._active:
            self._animation_angle = (self._animation_angle + 3) % 360
            self._pulse = (self._pulse + 0.05) % (2 * math.pi)

    def draw(self, surface):
        """Vẽ portal với hiệu ứng xoay"""
        if not self._active:
            # Portal chưa mở - vẽ mờ
            pygame.draw.circle(surface, (80, 80, 80), 
                             (int(self._x), int(self._y)), self._radius, 2)
            return

        # Portal đang mở - vẽ hiệu ứng
        pulse_size = int(3 * math.sin(self._pulse))

        # Vòng ngoài (xanh cyan)
        pygame.draw.circle(surface, CYAN, 
                         (int(self._x), int(self._y)), 
                         self._radius + pulse_size, 3)
        # Vòng giữa (xanh lá)
        pygame.draw.circle(surface, DARK_GREEN, 
                         (int(self._x), int(self._y)), 
                         self._radius - 5 + pulse_size, 2)
        # Vòng trong (trắng)
        pygame.draw.circle(surface, WHITE, 
                         (int(self._x), int(self._y)), 
                         self._radius - 12, 0)

        # Vẽ các đường xoay
        for i in range(4):
            angle = math.radians(self._animation_angle + i * 90)
            end_x = self._x + math.cos(angle) * (self._radius - 5)
            end_y = self._y + math.sin(angle) * (self._radius - 5)
            pygame.draw.line(surface, CYAN, 
                           (int(self._x), int(self._y)), 
                           (int(end_x), int(end_y)), 2)

    def set_position(self, x, y):
        """Đặt vị trí portal"""
        self._x = x
        self._y = y


# ============================================================
# HÀM VẼ HUD (Head-Up Display)
# ============================================================
def draw_hud(surface, player, level_starter, level_over, monsters, level_loader):
    """
    Vẽ giao diện thông tin game (HUD).
    Hiển thị level, HP, kill, score, map name.
    """
    level = level_starter.current_level
    map_name = level_loader.get_map_name(level)

    # Nền HUD bán trong suốt
    hud_bg = pygame.Surface((250, 130), pygame.SRCALPHA)
    hud_bg.fill((0, 0, 0, 120))
    surface.blit(hud_bg, (5, 5))

    # Thông tin
    enemies_alive = sum(1 for m in monsters if m.is_alive())
    total_enemies = len(monsters)

    texts = [
        (f"Level {level} - {map_name}", CYAN),
        (f"HP: {player.hp}/{player.max_hp}", GREEN if player.hp > 30 else RED),
        (f"Quái: {enemies_alive}/{total_enemies}", 
         GREEN if enemies_alive == 0 else YELLOW),
        (f"Kill: {level_over.kills} | Điểm: {level_over.score}", WHITE),
    ]

    for i, (text, color) in enumerate(texts):
        rendered = font_small.render(text, True, color)
        surface.blit(rendered, (15, 12 + i * 28))

    # Hướng dẫn điều khiển (góc dưới trái)
    controls = "WASD: Di chuyển | SPACE: Tấn công | R: Restart"
    ctrl_text = font_tiny.render(controls, True, (180, 180, 180))
    surface.blit(ctrl_text, (10, HEIGHT - 25))


# ============================================================
# HÀM VẼ NỀN MAP
# ============================================================
def draw_map_background(surface, level, level_loader):
    """
    Vẽ nền map với màu sắc thay đổi theo level.
    Thêm grid pattern để tạo cảm giác sàn.
    """
    bg_color = level_loader.get_map_color(level)
    surface.fill(bg_color)

    # Vẽ grid (lưới sàn)
    grid_color = tuple(max(0, c - 20) for c in bg_color)
    for x in range(0, WIDTH, 40):
        pygame.draw.line(surface, grid_color, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(surface, grid_color, (0, y), (WIDTH, y), 1)


# ============================================================
# HIỆU ỨNG CHUYỂN MAP
# ============================================================
def transition_effect(surface):
    """Hiệu ứng fade khi chuyển map"""
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill(BLACK)
    for alpha in range(0, 255, 15):
        overlay.set_alpha(alpha)
        surface.blit(overlay, (0, 0))
        pygame.display.flip()
        pygame.time.delay(20)
    for alpha in range(255, 0, -15):
        overlay.set_alpha(alpha)
        surface.blit(overlay, (0, 0))
        pygame.display.flip()
        pygame.time.delay(20)


# ============================================================
# VÒNG LẶP GAME CHÍNH (GAME LOOP)
# ============================================================
def main():
    """
    Game Loop chính theo flow:
    1. Spawn quái random
    2. Player combat
    3. Diệt hết quái
    4. Portal mở
    5. Qua map mới
    6. Spawn nhiều quái hơn
    7. Lặp tới khi player chết
    """

    # === Khởi tạo các module từ Game package ===
    # Sound
    sound_loader = SoundLoader()
    sound_player = SoundPlayer(sound_loader)
    sound_pauser = SoundPauser()

    # Image
    image_opener = ImageOpener()
    image_changer = ImageChanger()
    image_closer = ImageCloser()

    # Level
    level_starter = LevelStarter(WIDTH, HEIGHT)
    level_loader = LevelLoader()
    level_over = LevelOver()

    # Đăng ký các loại quái vào factory (Factory Pattern)
    level_loader.register_monster_class("melee", MeleeMonster)
    level_loader.register_monster_class("ranged", RangedMonster)

    # === Khởi tạo game objects ===
    player = Player(WIDTH // 2, HEIGHT // 2)
    portal = Portal(WIDTH // 2, HEIGHT // 2)

    # === Bước 1: Spawn quái random cho level 1 ===
    monsters = level_starter.start_level(level_loader, player.x, player.y)
    projectiles = []

    # Trạng thái game
    portal_activated = False
    waiting_for_restart = False

    running = True
    while running:
        # === Xử lý sự kiện ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                # Bước 2: Player combat - Nhấn SPACE để tấn công
                if event.key == pygame.K_SPACE and player.is_alive():
                    player.attack_monsters(monsters, level_over)

                # Restart game khi đã game over
                if event.key == pygame.K_r and waiting_for_restart:
                    # Reset toàn bộ
                    level_over.reset_all()
                    level_starter.reset()
                    player.reset(WIDTH // 2, HEIGHT // 2)
                    portal.deactivate()
                    portal_activated = False
                    monsters = level_starter.start_level(
                        level_loader, player.x, player.y)
                    projectiles = []
                    waiting_for_restart = False

                # Thoát game
                if event.key == pygame.K_ESCAPE:
                    running = False

        # === Bước 7: Kiểm tra player chết → Game Over ===
        if level_over.check_game_over(player):
            waiting_for_restart = True

        if not waiting_for_restart and player.is_alive():
            # === Cập nhật Player ===
            player.update()

            # === Bước 2: Monster combat - Quái tấn công player ===
            for m in monsters:
                if m.is_alive():
                    m.update(player, projectiles)

            # === Đẩy quái ra xa nhau (va chạm cứng AABB) ===
            for m in monsters:
                m.separate_from_others(monsters)

            # === Va chạm cứng Player ↔ Quái (không cho dính nhau) ===
            player.resolve_collision_with_monsters(monsters)

            # === Cập nhật đạn và kiểm tra va chạm ===
            active_projectiles = []
            for p in projectiles:
                p.update()
                dist = math.sqrt((p.x - player.x)**2 + (p.y - player.y)**2)
                if dist < player.size/2 + p.radius:
                    player.take_damage(p.damage)
                elif 0 <= p.x <= WIDTH and 0 <= p.y <= HEIGHT:
                    active_projectiles.append(p)
            projectiles = active_projectiles

            # === Bước 3: Kiểm tra diệt hết quái ===
            if level_over.check_level_complete(monsters) and not portal_activated:
                # === Bước 4: Portal mở ===
                portal.set_position(WIDTH // 2, HEIGHT // 2)
                portal.activate()
                portal_activated = True
                level_over.update_highest_level(level_starter.current_level)

            # === Cập nhật Portal ===
            portal.update()

            # === Bước 5 & 6: Qua map mới + Spawn nhiều quái hơn ===
            if portal_activated and portal.check_collision(player):
                # Hiệu ứng chuyển map
                transition_effect(screen)

                # Chuyển level
                level_starter.next_level()
                level_over.reset_level_state()

                # Reset player về giữa map
                player.reset(WIDTH // 2, HEIGHT // 2)

                # Spawn nhiều quái hơn ở map mới
                monsters = level_starter.start_level(
                    level_loader, player.x, player.y)
                projectiles = []

                # Tắt portal
                portal.deactivate()
                portal_activated = False

        # === RENDER ===
        # Vẽ nền map
        draw_map_background(screen, level_starter.current_level, level_loader)

        # Vẽ Portal
        portal.draw(screen)

        # Vẽ Player
        if player.is_alive():
            player.draw(screen)

        # Vẽ quái
        for m in monsters:
            m.draw(screen)

        # Vẽ đạn
        for p in projectiles:
            p.draw(screen)

        # Vẽ HUD
        draw_hud(screen, player, level_starter, level_over, monsters, level_loader)

        # Thông báo khi hoàn thành level
        if portal_activated:
            level_over.draw_level_complete(screen, font_medium, font_small,
                                          level_starter.current_level)

        # Màn hình Game Over
        if waiting_for_restart:
            level_over.draw_game_over(screen, font_large, font_small)

        pygame.display.flip()
        clock.tick(60)  # 60 FPS

    # === Dọn dẹp tài nguyên ===
    image_closer.close_all(image_opener)
    sound_pauser.stop_all()
    pygame.quit()


if __name__ == "__main__":
    main()
