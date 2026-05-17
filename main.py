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

# Nhân vật
player = pygame.Rect(100, 100, 40, 40)
player_speed = 5

# Quái đứng yên
enemy = pygame.Rect(500, 300, 40, 40)

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
    if keys[pygame.K_w]:
        player.y -= player_speed

    if keys[pygame.K_s]:
        player.y += player_speed

    if keys[pygame.K_a]:
        player.x -= player_speed

    if keys[pygame.K_d]:
        player.x += player_speed

    # Không cho nhân vật đi ra ngoài màn hình
    if player.left < 0:
        player.left = 0

    if player.right > WIDTH:
        player.right = WIDTH

    if player.top < 0:
        player.top = 0

    if player.bottom > HEIGHT:
        player.bottom = HEIGHT

    # Kiểm tra va chạm với quái
    if player.colliderect(enemy):
        print("Cham quai!")

    # Vẽ nền
    screen.fill(BLACK)

    # Vẽ nhân vật
    pygame.draw.rect(screen, BLUE, player)

    # Vẽ quái đứng yên
    pygame.draw.rect(screen, RED, enemy)

    pygame.display.flip()

pygame.quit()