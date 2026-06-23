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
    ATTACK_CIRCLE_FILL = (255, 80, 80, 60)     # Vòng tấn công melee (mờ, dùng cho fill)
    ATTACK_CIRCLE_BORDER = (255, 50, 50, 150)   # Viền vòng tấn công (mờ, alpha thấp)
    HEALTH_BAR_BG = RED
    HEALTH_BAR_FILL = GREEN

    # Vùng chém cung (90-180 độ) của quái cận chiến - màu mờ (alpha thấp)
    MELEE_ARC_FILL = (255, 60, 60, 70)      # Quạt chém, mờ
    MELEE_ARC_BORDER = (255, 120, 120, 140) # Viền quạt chém, mờ


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
    ENEMY_INCREASE_PER_LEVEL = 1    # Tăng thêm mỗi level (giảm từ 2 -> 1, đỡ dồn quá nhiều quái)

    # Va chạm giữa quái - "ô cứng" để quái không chồng/dính lên nhau
    MONSTER_COLLISION_PUSH = 0.5          # Mỗi quái nhận nửa độ lệch overlap (ổn định, không giật)
    MONSTER_COLLISION_ITERATIONS = 3      # Lặp nhiều vòng/frame để giải HẾT chồng lấn -> cứng như ô/tile

    # Tỉ lệ random loại quái (melee / ranged)
    # Level 1: 60% melee / 40% ranged (đúng tỉ lệ 6/4 yêu cầu)
    # Mỗi màn qua, tỉ lệ ranged tăng dần nhưng CHẬM và có TRẦN thấp hơn,
    # để màn sau không bị dồn quá nhiều quái bắn xa (rất khó đỡ).
    RANGED_CHANCE_BASE = 0.4                  # Tỉ lệ ranged ở level 1 (40%)
    RANGED_CHANCE_INCREASE_PER_LEVEL = 0.02   # Tăng thêm 2% ranged mỗi màn (chậm)
    RANGED_CHANCE_MAX = 0.5                   # Tỉ lệ ranged tối đa 50% (không lấn lướt melee)


class MonsterConfig:
    """
    Lớp chứa cấu hình mặc định cho từng loại quái.
    Đóng gói (Encapsulation): tách riêng cấu hình quái khỏi logic.
    """

    # Quái cận chiến (Melee) - cầm kiếm giống player
    MELEE_HP = 50
    MELEE_DAMAGE = 10
    MELEE_ATTACK_RANGE = 70         # Tầm kiếm (giống độ dài lưỡi kiếm player)
    MELEE_DETECT_RANGE = 150        # Tầm phát hiện player - ngoài tầm này quái đứng yên
    MELEE_SPEED = 2.5
    MELEE_COOLDOWN = Settings.FPS    # 1 giây / lần chém (60 frame @ 60 FPS) - hồi chiêu
    MELEE_SIZE = 30
    MELEE_COLOR = Colors.RED
    MELEE_SWORD_COLOR = Colors.GRAY      # Màu lưỡi kiếm
    MELEE_SWORD_LENGTH = 36               # Độ dài thanh kiếm vẽ trên người quái

    # Hành vi chém kiểu Soul Knight: phát hiện -> đuổi -> vào tầm thì
    # dừng khựng (wind-up) -> vung kiếm theo cung -> hồi chiêu -> đuổi tiếp.
    MELEE_WINDUP_FRAMES = 18         # Số frame dừng khựng trước khi chém (~0.3s)
    MELEE_SLASH_ANGLE_MIN = 90       # Góc cung chém nhỏ nhất (độ)
    MELEE_SLASH_ANGLE_MAX = 180      # Góc cung chém lớn nhất (độ) - mỗi lần chém random trong khoảng này
    MELEE_SLASH_FLASH_FRAMES = 10    # Số frame hiển thị vệt chém sau khi vung kiếm

    # Quái tầm xa (Ranged) - cầm súng giống player
    RANGED_HP = 30
    RANGED_DAMAGE = 15
    RANGED_ATTACK_RANGE = 300
    RANGED_DETECT_RANGE = 250   # Tầm phát hiện player - ngoài tầm này quái đứng yên
    RANGED_SPEED = 1.0
    RANGED_COOLDOWN = 90
    RANGED_SIZE = 30
    RANGED_COLOR = Colors.PURPLE
    RANGED_SAFE_DISTANCE = 80   # Khoảng cách an toàn lùi lại
    RANGED_GUN_COLOR = Colors.GRAY        # Màu thân súng
    RANGED_GUN_LENGTH = 26                # Độ dài súng vẽ trên người quái

    # Đạn (Projectile)
    PROJECTILE_SPEED = 6.0
    PROJECTILE_RADIUS = 8       # Bug #5: tăng từ 6 → 8
    PROJECTILE_COLOR = Colors.YELLOW
    PROJECTILE_BORDER_COLOR = Colors.ORANGE

    # Idle wander (Bug #1: quái di chuyển khi cooldown)
    IDLE_WANDER_RADIUS = 30     # Bán kính wander
    IDLE_WANDER_SPEED_RATIO = 0.3  # Tốc độ wander = 30% tốc độ thường
