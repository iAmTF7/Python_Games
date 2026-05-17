import pygame

pygame.init()

# Tạo màn hình
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Dungeon Game")

clock = pygame.time.Clock()

# Màu sắc
BLACK = (20, 20, 20)
BLUE = (0, 200, 255)
RED = (220, 50, 50)
YELLOW = (255, 230, 0)
WHITE = (255, 255, 255)

# Font chữ
font = pygame.font.SysFont(None, 36)

# Nhân vật
player = pygame.Rect(100, 100, 40, 40)
player_speed = 5

# Hướng nhìn của nhân vật
# Có thể là: "up", "down", "left", "right"
player_direction = "down"

# Quái
enemy = pygame.Rect(500, 300, 40, 40)
enemy_hp = 100
enemy_alive = True

# Vũ khí gần
attack_damage = 25
attack_range = 45
attack_width = 40

attacking = False
attack_timer = 0
attack_duration = 10

# Thời gian hồi chiêu
attack_cooldown = 25
cooldown_timer = 0

running = True

while running:
    clock.tick(60)

    # Thoát game
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Lấy phím người dùng bấm
    keys = pygame.key.get_pressed()

    # Di chuyển nhân vật
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        player.y -= player_speed
        player_direction = "up"

    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        player.y += player_speed
        player_direction = "down"

    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        player.x -= player_speed
        player_direction = "left"

    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player.x += player_speed
        player_direction = "right"

    # Không cho nhân vật đi ra ngoài màn hình
    if player.left < 0:
        player.left = 0

    if player.right > WIDTH:
        player.right = WIDTH

    if player.top < 0:
        player.top = 0

    if player.bottom > HEIGHT:
        player.bottom = HEIGHT

    # Giảm hồi chiêu đánh
    if cooldown_timer > 0:
        cooldown_timer -= 1

    # Bấm SPACE để đánh
    if keys[pygame.K_SPACE] and cooldown_timer == 0:
        attacking = True
        attack_timer = attack_duration
        cooldown_timer = attack_cooldown

        # Tạo vùng đánh theo hướng nhân vật đang nhìn
        if player_direction == "up":
            attack_rect = pygame.Rect(
                player.x,
                player.y - attack_range,
                attack_width,
                attack_range
            )

        elif player_direction == "down":
            attack_rect = pygame.Rect(
                player.x,
                player.bottom,
                attack_width,
                attack_range
            )

        elif player_direction == "left":
            attack_rect = pygame.Rect(
                player.x - attack_range,
                player.y,
                attack_range,
                attack_width
            )

        elif player_direction == "right":
            attack_rect = pygame.Rect(
                player.right,
                player.y,
                attack_range,
                attack_width
            )

        # Kiểm tra đánh trúng quái
        if enemy_alive and attack_rect.colliderect(enemy):
            enemy_hp -= attack_damage
            print("Đánh trúng quái! Máu quái còn:", enemy_hp)

            if enemy_hp <= 0:
                enemy_alive = False
                print("Quái đã bị tiêu diệt!")

    # Đếm thời gian hiện hiệu ứng chém
    if attacking:
        attack_timer -= 1
        if attack_timer <= 0:
            attacking = False

    # Vẽ nền
    screen.fill(BLACK)

    # Vẽ nhân vật
    pygame.draw.rect(screen, BLUE, player)

    # Vẽ quái nếu còn sống
    if enemy_alive:
        pygame.draw.rect(screen, RED, enemy)

        # Hiển thị máu quái
        hp_text = font.render("HP: " + str(enemy_hp), True, WHITE)
        screen.blit(hp_text, (enemy.x - 10, enemy.y - 35))

    # Vẽ hiệu ứng vũ khí khi đang đánh
    if attacking:
        if player_direction == "up":
            draw_attack = pygame.Rect(
                player.x,
                player.y - attack_range,
                attack_width,
                attack_range
            )

        elif player_direction == "down":
            draw_attack = pygame.Rect(
                player.x,
                player.bottom,
                attack_width,
                attack_range
            )

        elif player_direction == "left":
            draw_attack = pygame.Rect(
                player.x - attack_range,
                player.y,
                attack_range,
                attack_width
            )

        elif player_direction == "right":
            draw_attack = pygame.Rect(
                player.right,
                player.y,
                attack_range,
                attack_width
            )

        pygame.draw.rect(screen, YELLOW, draw_attack)

    pygame.display.flip()

pygame.quit()