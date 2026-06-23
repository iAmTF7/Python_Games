"""
Module settings.py - Cấu hình hệ thống combat quái
Chứa các hằng số, bảng màu, và cấu hình mặc định.
Tập trung quản lý config để dễ thay đổi (Đóng gói - Encapsulation).
"""


class Colors:
    """
    Lớp chứa tất cả hằng số màu sắc dùng trong game.
    Đóng gói (Encapsulation): gom nhóm các hằng số liên quan.
    """
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    PURPLE = (128, 0, 128)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 165, 0)
    CYAN = (0, 255, 255)
    GRAY = (200, 200, 200)
    DARK_GREEN = (0, 180, 0)

    # Màu chuyên dụng cho combat
    ATTACK_CIRCLE_FILL = (255, 80, 80, 60)     # Vòng tấn công melee (mờ)
    ATTACK_CIRCLE_BORDER = (255, 50, 50, 150)   # Viền vòng tấn công
    HEALTH_BAR_BG = RED
    HEALTH_BAR_FILL = GREEN


class Settings:
    """
    Lớp chứa các thiết lập chung của game.
    Đóng gói (Encapsulation): quản lý tập trung cấu hình.
    """
    # Kích thước màn hình mặc định
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60

    # Spawn
    SPAWN_MARGIN = 60               # Khoảng cách tối thiểu từ viền
    SPAWN_MIN_DISTANCE_FROM_TARGET = 150  # Khoảng cách tối thiểu từ target
    SPAWN_MIN_DISTANCE_BETWEEN = 50      # Khoảng cách tối thiểu giữa các quái
    SPAWN_MAX_ATTEMPTS = 100             # Số lần thử tìm vị trí spawn

    # Base enemy
    BASE_ENEMY_COUNT = 3            # Số quái cơ bản ở level 1
    ENEMY_INCREASE_PER_LEVEL = 2    # Tăng thêm mỗi level


class MonsterConfig:
    """
    Lớp chứa cấu hình mặc định cho từng loại quái.
    Đóng gói (Encapsulation): tách riêng cấu hình quái khỏi logic.
    """

    # Quái cận chiến (Melee)
    MELEE_HP = 50
    MELEE_DAMAGE = 10
    MELEE_ATTACK_RANGE = 35
    MELEE_SPEED = 2.5
    MELEE_COOLDOWN = 60
    MELEE_SIZE = 30
    MELEE_COLOR = Colors.RED

    # Quái tầm xa (Ranged)
    RANGED_HP = 30
    RANGED_DAMAGE = 15
    RANGED_ATTACK_RANGE = 300
    RANGED_SPEED = 1.0
    RANGED_COOLDOWN = 90
    RANGED_SIZE = 30
    RANGED_COLOR = Colors.PURPLE
    RANGED_SAFE_DISTANCE = 80   # Khoảng cách an toàn lùi lại

    # Đạn (Projectile)
    PROJECTILE_SPEED = 6.0
    PROJECTILE_RADIUS = 8       # Bug #5: tăng từ 6 → 8
    PROJECTILE_COLOR = Colors.YELLOW
    PROJECTILE_BORDER_COLOR = Colors.ORANGE

    # Idle wander (Bug #1: quái di chuyển khi cooldown)
    IDLE_WANDER_RADIUS = 30     # Bán kính wander
    IDLE_WANDER_SPEED_RATIO = 0.3  # Tốc độ wander = 30% tốc độ thường
