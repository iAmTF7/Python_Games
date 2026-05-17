import pygame
import math

pygame.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("2D Dungeon Game")
pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

clock = pygame.time.Clock()

BLACK = (20, 20, 20)
BLUE = (0, 200, 255)
RED = (220, 50, 50)
YELLOW = (255, 230, 0)
WHITE = (255, 255, 255)
GREEN = (0, 220, 80)
ORANGE = (255, 140, 0)
GRAY = (120, 120, 120)
LIGHT_GRAY = (170, 170, 170)
DARK_GRAY = (45, 45, 45)
PURPLE = (160, 80, 255)
BROWN = (130, 80, 35)
FLAG_RED = (255, 60, 60)
FLAG_LIGHT = (255, 150, 150)
FLAG_DARK = (170, 30, 30)

font = pygame.font.SysFont(None, 30)
small_font = pygame.font.SysFont(None, 24)
big_font = pygame.font.SysFont(None, 70)

player = pygame.Rect(100, 100, 40, 40)
player_speed = 5
player_direction = pygame.Vector2(0, 1)
player_hp = 100

enemy = pygame.Rect(WIDTH - 300, HEIGHT // 2, 40, 40)
enemy_hp = 100
enemy_alive = True

weapons = [
    {
        "name": "Sword",
        "type": "melee",
        "damage": 25,
        "range": 55,
        "size": 40,
        "color": YELLOW,
        "cooldown": 30
    },
    {
        "name": "Gun",
        "type": "ranged",
        "damage": 20,
        "range": 0,
        "size": 10,
        "color": ORANGE,
        "cooldown": 30
    },
    {
        "name": "Flag",
        "type": "melee",
        "damage": 9,
        "range": 75,
        "size": 48,
        "color": FLAG_RED,
        "cooldown": 20
    }
]

current_weapon = 0
selected_weapon = 0
weapon_list_open = False

bullets = []
bullet_speed = 9
bullet_size = 10
shoot_timer = 0

attacking = False
attack_timer = 0
attack_rect = pygame.Rect(0, 0, 0, 0)
attack_cooldown_timer = 0

flag_swinging = False
flag_timer = 0
flag_duration = 12
flag_side = 1
flag_wave = 0
flag_attack_direction = pygame.Vector2(0, 1)
flag_has_hit_enemy = False
flag_attack_polygon = []

touch_timer = 0
touch_damage = 10
touch_cooldown = 60

dev_panel_open = True
player_invincible = False
enemy_invincible = False
show_hitbox = False


def weapon():
    return weapons[current_weapon]


def equip(index):
    global current_weapon, selected_weapon
    current_weapon = index
    selected_weapon = index


def rotate(vec, angle):
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    return pygame.Vector2(
        vec.x * cos_a - vec.y * sin_a,
        vec.x * sin_a + vec.y * cos_a
    )


def get_flag_angle():
    if not flag_swinging:
        return 0

    progress = 1 - flag_timer / flag_duration
    start_angle = -45 * flag_side
    end_angle = 45 * flag_side

    return start_angle + (end_angle - start_angle) * progress


def point_in_polygon(point, polygon):
    x, y = point
    inside = False
    j = len(polygon) - 1

    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]

        if (yi > y) != (yj > y):
            x_cross = (xj - xi) * (y - yi) / (yj - yi + 0.00001) + xi

            if x < x_cross:
                inside = not inside

        j = i

    return inside


def lines_intersect(a, b, c, d):
    def ccw(p1, p2, p3):
        return (p3[1] - p1[1]) * (p2[0] - p1[0]) > (p2[1] - p1[1]) * (p3[0] - p1[0])

    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)


def rect_hits_polygon(rect, polygon):
    if len(polygon) < 3:
        return False

    rect_points = [
        rect.topleft,
        rect.topright,
        rect.bottomright,
        rect.bottomleft
    ]

    for point in rect_points:
        if point_in_polygon(point, polygon):
            return True

    for point in polygon:
        if rect.collidepoint(point):
            return True

    rect_edges = [
        (rect.topleft, rect.topright),
        (rect.topright, rect.bottomright),
        (rect.bottomright, rect.bottomleft),
        (rect.bottomleft, rect.topleft)
    ]

    for i in range(len(polygon)):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % len(polygon)]

        for e1, e2 in rect_edges:
            if lines_intersect(p1, p2, e1, e2):
                return True

    return False


def build_flag_attack_polygon():
    if not flag_swinging:
        return []

    d = pygame.Vector2(flag_attack_direction.x, flag_attack_direction.y)

    if d.length() == 0:
        d = pygame.Vector2(0, 1)

    d = d.normalize()

    center = pygame.Vector2(player.centerx, player.centery)

    start_angle = -45 * flag_side
    current_angle = get_flag_angle()

    inner = 22
    outer = 95
    steps = 18

    outer_points = []
    inner_points = []

    for i in range(steps + 1):
        t = i / steps
        angle = start_angle + (current_angle - start_angle) * t
        rotated = rotate(d, math.radians(angle))

        outer_point = center + rotated * outer
        inner_point = center + rotated * inner

        outer_points.append((int(outer_point.x), int(outer_point.y)))
        inner_points.append((int(inner_point.x), int(inner_point.y)))

    return outer_points + inner_points[::-1]


def attack_box(rng, size):
    d = player_direction

    if d.x > 0 and d.y == 0:
        return pygame.Rect(player.right, player.y, rng, size)

    if d.x < 0 and d.y == 0:
        return pygame.Rect(player.x - rng, player.y, rng, size)

    if d.y > 0 and d.x == 0:
        return pygame.Rect(player.x, player.bottom, size, rng)

    if d.y < 0 and d.x == 0:
        return pygame.Rect(player.x, player.y - rng, size, rng)

    if d.x > 0 and d.y > 0:
        return pygame.Rect(player.right, player.bottom, rng, rng)

    if d.x > 0 and d.y < 0:
        return pygame.Rect(player.right, player.y - rng, rng, rng)

    if d.x < 0 and d.y > 0:
        return pygame.Rect(player.x - rng, player.bottom, rng, rng)

    if d.x < 0 and d.y < 0:
        return pygame.Rect(player.x - rng, player.y - rng, rng, rng)

    return pygame.Rect(0, 0, 0, 0)


def make_bullet():
    d = pygame.Vector2(player_direction.x, player_direction.y)

    if d.length() == 0:
        d = pygame.Vector2(0, 1)

    d = d.normalize()

    rect = pygame.Rect(
        player.centerx - bullet_size // 2,
        player.centery - bullet_size // 2,
        bullet_size,
        bullet_size
    )

    return {
        "rect": rect,
        "pos": pygame.Vector2(rect.x, rect.y),
        "dir": d,
        "damage": weapon()["damage"]
    }


def use_weapon():
    global attacking, attack_timer, attack_rect
    global enemy_hp, enemy_alive, shoot_timer
    global flag_swinging, flag_timer, flag_side
    global attack_cooldown_timer
    global flag_attack_direction, flag_has_hit_enemy, flag_attack_polygon

    w = weapon()

    if w["type"] == "ranged":
        if shoot_timer <= 0:
            bullets.append(make_bullet())
            shoot_timer = w["cooldown"]

        return

    if attack_cooldown_timer > 0:
        return

    attacking = True

    if w["name"] == "Flag":
        attack_timer = flag_duration
        attack_cooldown_timer = w["cooldown"]
        flag_swinging = True
        flag_timer = flag_duration
        flag_side *= -1
        flag_attack_direction = pygame.Vector2(player_direction.x, player_direction.y)
        flag_has_hit_enemy = False
        flag_attack_polygon = build_flag_attack_polygon()
        return

    attack_timer = 10
    attack_cooldown_timer = w["cooldown"]
    attack_rect = attack_box(w["range"], w["size"])

    if enemy_alive and attack_rect.colliderect(enemy):
        if not enemy_invincible:
            enemy_hp -= w["damage"]

            if enemy_hp <= 0:
                enemy_hp = 0
                enemy_alive = False


def update_flag_hitbox():
    global enemy_hp, enemy_alive, flag_has_hit_enemy, flag_attack_polygon

    if not flag_swinging:
        flag_attack_polygon = []
        return

    if weapon()["name"] != "Flag":
        return

    flag_attack_polygon = build_flag_attack_polygon()

    if enemy_alive and rect_hits_polygon(enemy, flag_attack_polygon) and not flag_has_hit_enemy:
        if not enemy_invincible:
            enemy_hp -= weapon()["damage"]

            if enemy_hp <= 0:
                enemy_hp = 0
                enemy_alive = False

        flag_has_hit_enemy = True


def draw_flag_cloth(px, py, direction):
    d = pygame.Vector2(direction.x, direction.y)

    if d.length() == 0:
        d = pygame.Vector2(0, 1)

    d = d.normalize()
    side = pygame.Vector2(-d.y, d.x)

    length = 54
    height = 34
    power = 5
    segments = 8

    top = []
    bottom = []

    for i in range(segments + 1):
        t = i / segments

        wave = math.sin(
            flag_wave * 0.22 + t * math.pi * 2.2
        ) * power * t

        cx = px + side.x * length * t + d.x * wave
        cy = py + side.y * length * t + d.y * wave

        h = height * (1 - t * 0.08) / 2

        top.append((int(cx - d.x * h), int(cy - d.y * h)))
        bottom.append((int(cx + d.x * h), int(cy + d.y * h)))

    points = top + bottom[::-1]

    pygame.draw.polygon(screen, FLAG_RED, points)
    pygame.draw.lines(screen, WHITE, True, points, 2)

    colors = [FLAG_LIGHT, WHITE, FLAG_DARK]

    for n in range(3):
        line = []
        ratio = 0.28 + n * 0.18

        for i in range(segments + 1):
            t = i / segments

            wave = math.sin(
                flag_wave * 0.22 + t * math.pi * 2.2
            ) * power * t

            cx = px + side.x * length * t + d.x * wave
            cy = py + side.y * length * t + d.y * wave

            offset = (ratio - 0.5) * height * (1 - t * 0.08)

            line.append((int(cx + d.x * offset), int(cy + d.y * offset)))

        pygame.draw.lines(screen, colors[n], False, line, 2)


def draw_flag():
    if flag_swinging:
        d = pygame.Vector2(flag_attack_direction.x, flag_attack_direction.y)
    else:
        d = pygame.Vector2(player_direction.x, player_direction.y)

    if d.length() == 0:
        d = pygame.Vector2(0, 1)

    d = d.normalize()

    if flag_swinging:
        d = rotate(d, math.radians(get_flag_angle()))

    end = pygame.Vector2(player.centerx, player.centery) + d * 52

    pygame.draw.line(
        screen,
        BROWN,
        player.center,
        (int(end.x), int(end.y)),
        6
    )

    pygame.draw.circle(
        screen,
        LIGHT_GRAY,
        (int(end.x), int(end.y)),
        7
    )

    draw_flag_cloth(end.x, end.y, d)


def draw_fan():
    polygon = build_flag_attack_polygon()

    if len(polygon) < 3:
        return

    pygame.draw.polygon(screen, FLAG_DARK, polygon)
    pygame.draw.lines(screen, FLAG_LIGHT, True, polygon, 3)

    d = pygame.Vector2(flag_attack_direction.x, flag_attack_direction.y)

    if d.length() == 0:
        d = pygame.Vector2(0, 1)

    d = d.normalize()

    center = pygame.Vector2(player.centerx, player.centery)
    current_dir = rotate(d, math.radians(get_flag_angle()))
    tip = center + current_dir * 95

    pygame.draw.line(
        screen,
        FLAG_RED,
        (int(center.x), int(center.y)),
        (int(tip.x), int(tip.y)),
        6
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (int(tip.x), int(tip.y)),
        5
    )


def draw_weapon_icon():
    w = weapon()

    if w["name"] == "Sword":
        end = (
            player.centerx + int(player_direction.x * 35),
            player.centery + int(player_direction.y * 35)
        )

        pygame.draw.line(screen, YELLOW, player.center, end, 5)

    elif w["name"] == "Gun":
        pygame.draw.rect(
            screen,
            ORANGE,
            (player.centerx - 8, player.centery - 8, 16, 16)
        )

    elif w["name"] == "Flag":
        draw_flag()


def draw_weapon_list():
    x = WIDTH // 2 - 250
    y = HEIGHT // 2 - 160

    pygame.draw.rect(screen, DARK_GRAY, (x, y, 500, 320))
    pygame.draw.rect(screen, WHITE, (x, y, 500, 320), 3)

    title = font.render("WEAPON LIST", True, WHITE)
    guide = small_font.render(
        "I: Close | UP/DOWN: Select | ENTER: Equip",
        True,
        LIGHT_GRAY
    )

    screen.blit(title, (x + 175, y + 20))
    screen.blit(guide, (x + 55, y + 55))

    for i, w in enumerate(weapons):
        rect = pygame.Rect(x + 40, y + 100 + i * 65, 420, 55)

        if i == selected_weapon:
            pygame.draw.rect(screen, GRAY, rect)
            pygame.draw.rect(screen, WHITE, rect, 2)
        else:
            pygame.draw.rect(screen, (65, 65, 65), rect)

        text = w["name"]

        if i == current_weapon:
            text += " [EQUIPPED]"

        name_text = font.render(text, True, w["color"])
        info_text = small_font.render(
            "Type: " + w["type"] + " | Damage: " + str(w["damage"]),
            True,
            WHITE
        )

        screen.blit(name_text, (rect.x + 20, rect.y + 8))
        screen.blit(info_text, (rect.x + 20, rect.y + 32))


def draw_dev():
    x = WIDTH - 330
    y = 20

    if not dev_panel_open:
        pygame.draw.rect(screen, DARK_GRAY, (x, y, 180, 40))
        pygame.draw.rect(screen, WHITE, (x, y, 180, 40), 2)

        text = small_font.render("DEV PANEL [F3]", True, WHITE)
        screen.blit(text, (x + 15, y + 12))
        return

    pygame.draw.rect(screen, DARK_GRAY, (x, y, 310, 200))
    pygame.draw.rect(screen, WHITE, (x, y, 310, 200), 2)

    items = [
        ("DEVELOPER PANEL", WHITE),
        ("F3: Collapse / Open", GRAY),
        ("F4: Player God: " + ("ON" if player_invincible else "OFF"),
         GREEN if player_invincible else RED),
        ("F5: Enemy God: " + ("ON" if enemy_invincible else "OFF"),
         GREEN if enemy_invincible else RED),
        ("F6: Hitbox: " + ("ON" if show_hitbox else "OFF"),
         GREEN if show_hitbox else RED),
        ("ESC: Exit", GRAY)
    ]

    for i, item in enumerate(items):
        used_font = font if i == 0 else small_font
        text = used_font.render(item[0], True, item[1])
        screen.blit(text, (x + 15, y + 15 + i * 30))


running = True

while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if weapon_list_open:
                    weapon_list_open = False
                else:
                    running = False

            elif event.key == pygame.K_i:
                weapon_list_open = not weapon_list_open

            elif weapon_list_open:
                if event.key == pygame.K_UP:
                    selected_weapon = (selected_weapon - 1) % len(weapons)

                elif event.key == pygame.K_DOWN:
                    selected_weapon = (selected_weapon + 1) % len(weapons)

                elif event.key == pygame.K_RETURN:
                    equip(selected_weapon)
                    weapon_list_open = False

            else:
                if event.key == pygame.K_TAB:
                    equip((current_weapon + 1) % len(weapons))

                elif event.key == pygame.K_SPACE:
                    use_weapon()

                elif event.key == pygame.K_F3:
                    dev_panel_open = not dev_panel_open

                elif event.key == pygame.K_F4:
                    player_invincible = not player_invincible

                elif event.key == pygame.K_F5:
                    enemy_invincible = not enemy_invincible

                elif event.key == pygame.K_F6:
                    show_hitbox = not show_hitbox

    keys = pygame.key.get_pressed()
    move = pygame.Vector2(0, 0)

    if keys[pygame.K_w] or keys[pygame.K_UP]:
        move.y -= 1

    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        move.y += 1

    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        move.x -= 1

    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        move.x += 1

    if move.length() > 0:
        move = move.normalize()
        player_direction = pygame.Vector2(move.x, move.y)

        if flag_swinging:
            flag_attack_direction = pygame.Vector2(move.x, move.y)

        player.x += int(move.x * player_speed)
        player.y += int(move.y * player_speed)

    player.clamp_ip(screen.get_rect())

    flag_wave += 1

    if attacking:
        attack_timer -= 1

        if attack_timer <= 0:
            attacking = False

    if flag_swinging:
        flag_timer -= 1

        if flag_timer <= 0:
            flag_swinging = False

    update_flag_hitbox()

    if touch_timer > 0:
        touch_timer -= 1

    if shoot_timer > 0:
        shoot_timer -= 1

    if attack_cooldown_timer > 0:
        attack_cooldown_timer -= 1

    if enemy_alive and player.colliderect(enemy) and touch_timer <= 0:
        if not player_invincible:
            player_hp = max(0, player_hp - touch_damage)

        touch_timer = touch_cooldown

    for bullet in bullets[:]:
        bullet["pos"] += bullet["dir"] * bullet_speed
        bullet["rect"].x = int(bullet["pos"].x)
        bullet["rect"].y = int(bullet["pos"].y)

        if not screen.get_rect().colliderect(bullet["rect"]):
            bullets.remove(bullet)
            continue

        if enemy_alive and bullet["rect"].colliderect(enemy):
            if not enemy_invincible:
                enemy_hp -= bullet["damage"]

                if enemy_hp <= 0:
                    enemy_hp = 0
                    enemy_alive = False

            bullets.remove(bullet)

    screen.fill(BLACK)

    if flag_swinging and weapon()["name"] == "Flag":
        draw_fan()

    pygame.draw.rect(screen, BLUE, player)

    if player_invincible:
        pygame.draw.rect(screen, GREEN, player, 3)

    look = (
        player.centerx + int(player_direction.x * 25),
        player.centery + int(player_direction.y * 25)
    )

    pygame.draw.line(screen, WHITE, player.center, look, 3)

    draw_weapon_icon()

    if enemy_alive:
        pygame.draw.rect(screen, RED, enemy)

        if enemy_invincible:
            pygame.draw.rect(screen, GREEN, enemy, 3)

        enemy_text = font.render("Enemy HP: " + str(enemy_hp), True, WHITE)
        screen.blit(enemy_text, (enemy.x - 25, enemy.y - 35))

        pygame.draw.rect(screen, RED, (enemy.x, enemy.y - 10, 40, 5))
        pygame.draw.rect(
            screen,
            GREEN,
            (enemy.x, enemy.y - 10, max(0, enemy_hp) * 40 / 100, 5)
        )

    if attacking:
        if weapon()["name"] == "Flag":
            if show_hitbox and len(flag_attack_polygon) >= 3:
                pygame.draw.lines(screen, WHITE, True, flag_attack_polygon, 3)
        else:
            pygame.draw.rect(screen, weapon()["color"], attack_rect)

    for bullet in bullets:
        pygame.draw.rect(screen, ORANGE, bullet["rect"])

    pygame.draw.rect(screen, RED, (20, 50, 100, 10))
    pygame.draw.rect(screen, GREEN, (20, 50, max(0, player_hp), 10))

    screen.blit(
        font.render("Player HP: " + str(player_hp), True, WHITE),
        (20, 20)
    )

    screen.blit(
        font.render(
            "Weapon: " + weapon()["name"] + " | SPACE",
            True,
            weapon()["color"]
        ),
        (20, 75)
    )

    screen.blit(
        small_font.render(
            "Type: " + weapon()["type"] + " | Damage: " + str(weapon()["damage"]),
            True,
            WHITE
        ),
        (20, 105)
    )

    screen.blit(
        font.render("Bullets: " + str(len(bullets)), True, PURPLE),
        (20, 135)
    )

    screen.blit(
        small_font.render(
            "Player God: " + ("ON" if player_invincible else "OFF"),
            True,
            GREEN if player_invincible else GRAY
        ),
        (20, 165)
    )

    screen.blit(
        small_font.render(
            "Enemy God: " + ("ON" if enemy_invincible else "OFF"),
            True,
            GREEN if enemy_invincible else GRAY
        ),
        (20, 190)
    )

    screen.blit(
        small_font.render(
            "Attack Cooldown: " + str(attack_cooldown_timer),
            True,
            LIGHT_GRAY
        ),
        (20, 220)
    )

    screen.blit(
        small_font.render(
            "Shoot Cooldown: " + str(shoot_timer),
            True,
            LIGHT_GRAY
        ),
        (20, 245)
    )

    screen.blit(
        font.render(
            "Move: WASD/Arrow | TAB: Switch | I: Weapons | SPACE: Use",
            True,
            WHITE
        ),
        (20, HEIGHT - 60)
    )

    screen.blit(
        font.render(
            "F3: Dev | F4: Player God | F5: Enemy God | F6: Hitbox | ESC: Exit",
            True,
            GRAY
        ),
        (20, HEIGHT - 30)
    )

    draw_dev()

    if weapon_list_open:
        draw_weapon_list()

    if player_hp <= 0:
        screen.blit(
            big_font.render("GAME OVER", True, RED),
            (WIDTH // 2 - 160, HEIGHT // 2 - 40)
        )

    pygame.display.flip()

pygame.event.set_grab(False)
pygame.mouse.set_visible