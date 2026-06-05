import pygame
import math
import random

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

SPEAR_COLOR = (80, 220, 255)
SPEAR_TIP = (230, 230, 255)
SPEAR_SPLASH = (60, 130, 180)

MONSTER_COLOR = (210, 60, 80)
MONSTER_OUTLINE = (255, 120, 120)

DUAL_LONG = (180, 220, 255)
DUAL_SHORT = (255, 220, 120)
DUAL_SLASH = (120, 210, 255)

font = pygame.font.SysFont(None, 30)
small_font = pygame.font.SysFont(None, 24)
big_font = pygame.font.SysFont(None, 70)

player = pygame.Rect(100, 100, 40, 40)
player_speed = 5
player_direction = pygame.Vector2(0, 1)
player_hp = 100

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
    },
    {
        "name": "Spear",
        "type": "thrown_spear",
        "damage": 10,
        "splash_damage": 3,
        "splash_chance": 12,
        "splash_range": 162,
        "speed": 13,
        "size": 12,
        "color": SPEAR_COLOR,
        "cooldown": 45
    },
    {
        "name": "Dual Blades",
        "type": "dash_slash",
        "damage": 18,
        "dash_distance": 140,
        "slash_width": 42,
        "color": DUAL_SLASH,
        "cooldown": 45
    }
]

current_weapon = 0
selected_weapon = 0
weapon_list_open = False

bullets = []
bullet_speed = 9
bullet_size = 10
shoot_timer = 0

spears = []
spear_splash_timer = 0
spear_splash_pos = None
last_spear_splash = False
last_spear_splash_damage = 0

attacking = False
attack_timer = 0
attack_rect = pygame.Rect(0, 0, 0, 0)
attack_cooldown_timer = 0

dash_slashing = False
dash_slash_timer = 0
dash_slash_duration = 8
dash_start_pos = pygame.Vector2(0, 0)
dash_end_pos = pygame.Vector2(0, 0)
dash_slash_width = 42

flag_swinging = False
flag_timer = 0
flag_duration = 12
flag_side = 1
flag_wave = 0
flag_attack_direction = pygame.Vector2(0, 1)
flag_has_hit_enemy = False
flag_attack_polygon = []

monsters = []
monster_speed = 2.2
monster_touch_damage = 10
monster_touch_cooldown = 60
spawn_static_monster = True
freeze_all_monsters = False

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


def spawn_monster(x=None, y=None, static=None):
    if static is None:
        static = spawn_static_monster

    if x is None:
        x = player.centerx - 20

    if y is None:
        y = player.centery - 20

    monster = {
        "rect": pygame.Rect(x, y, 40, 40),
        "hp": 100,
        "max_hp": 100,
        "speed": monster_speed,
        "touch_timer": 0,
        "alive": True,
        "static": static
    }

    monsters.append(monster)


def damage_monster(monster, damage):
    if enemy_invincible:
        return

    monster["hp"] -= damage

    if monster["hp"] <= 0:
        monster["hp"] = 0
        monster["alive"] = False


def update_monsters():
    for monster in monsters:
        if not monster["alive"]:
            continue

        rect = monster["rect"]

        if not freeze_all_monsters and not monster["static"]:
            direction = pygame.Vector2(
                player.centerx - rect.centerx,
                player.centery - rect.centery
            )

            if direction.length() > 0:
                direction = direction.normalize()
                rect.x += int(direction.x * monster["speed"])
                rect.y += int(direction.y * monster["speed"])

        rect.clamp_ip(screen.get_rect())

        if monster["touch_timer"] > 0:
            monster["touch_timer"] -= 1


def monster_touch_player():
    global player_hp

    for monster in monsters:
        if not monster["alive"]:
            continue

        if monster["rect"].colliderect(player) and monster["touch_timer"] <= 0:
            if not player_invincible:
                player_hp = max(0, player_hp - monster_touch_damage)

            monster["touch_timer"] = monster_touch_cooldown


def get_weapon_damage_text(w):
    if w["name"] == "Spear":
        return (
            str(w["damage"])
            + " | Splash: "
            + str(w["splash_damage"])
            + " / "
            + str(w["splash_chance"])
            + "%"
            + " | Range: "
            + str(w["splash_range"])
        )

    if w["name"] == "Dual Blades":
        return (
            str(w["damage"])
            + " | Dash: "
            + str(w["dash_distance"])
            + " | Width: "
            + str(w["slash_width"])
        )

    return str(w["damage"])


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
        return (p3[1] - p1[1]) * (p2[0] - p1[0]) > (
            p2[1] - p1[1]
        ) * (p3[0] - p1[0])

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


def rect_in_circle(rect, center, radius):
    closest_x = max(rect.left, min(center.x, rect.right))
    closest_y = max(rect.top, min(center.y, rect.bottom))

    distance = pygame.Vector2(closest_x, closest_y).distance_to(center)

    return distance <= radius


def rect_hits_line(rect, start, end, width):
    rect_center = pygame.Vector2(rect.centerx, rect.centery)
    line_start = pygame.Vector2(start.x, start.y)
    line_end = pygame.Vector2(end.x, end.y)

    line = line_end - line_start

    if line.length() == 0:
        return rect.collidepoint(line_start.x, line_start.y)

    t = (rect_center - line_start).dot(line) / line.length_squared()
    t = max(0, min(1, t))

    closest = line_start + line * t
    distance = rect_center.distance_to(closest)

    monster_radius = max(rect.width, rect.height) / 2

    return distance <= width / 2 + monster_radius


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


def make_spear():
    d = pygame.Vector2(player_direction.x, player_direction.y)

    if d.length() == 0:
        d = pygame.Vector2(0, 1)

    d = d.normalize()

    w = weapon()

    rect = pygame.Rect(
        player.centerx - w["size"] // 2,
        player.centery - w["size"] // 2,
        w["size"],
        w["size"]
    )

    return {
        "rect": rect,
        "pos": pygame.Vector2(rect.x, rect.y),
        "dir": d,
        "damage": w["damage"],
        "speed": w["speed"],
        "size": w["size"],
        "splash_damage": w["splash_damage"],
        "splash_chance": w["splash_chance"],
        "splash_range": w["splash_range"]
    }


def use_weapon():
    global attacking, attack_timer, attack_rect
    global shoot_timer
    global flag_swinging, flag_timer, flag_side
    global attack_cooldown_timer
    global flag_attack_direction, flag_has_hit_enemy, flag_attack_polygon
    global dash_slashing, dash_slash_timer
    global dash_start_pos, dash_end_pos, dash_slash_width

    w = weapon()

    if w["type"] == "ranged":
        if shoot_timer <= 0:
            bullets.append(make_bullet())
            shoot_timer = w["cooldown"]

        return

    if w["type"] == "thrown_spear":
        if attack_cooldown_timer <= 0:
            spears.append(make_spear())
            attack_cooldown_timer = w["cooldown"]

        return

    if w["type"] == "dash_slash":
        if attack_cooldown_timer > 0:
            return

        d = pygame.Vector2(player_direction.x, player_direction.y)

        if d.length() == 0:
            d = pygame.Vector2(0, 1)

        d = d.normalize()

        dash_start_pos = pygame.Vector2(player.centerx, player.centery)
        target_pos = dash_start_pos + d * w["dash_distance"]

        target_x = max(player.width // 2, min(WIDTH - player.width // 2, target_pos.x))
        target_y = max(player.height // 2, min(HEIGHT - player.height // 2, target_pos.y))

        dash_end_pos = pygame.Vector2(target_x, target_y)

        player.centerx = int(dash_end_pos.x)
        player.centery = int(dash_end_pos.y)
        player.clamp_ip(screen.get_rect())

        dash_slashing = True
        attacking = True
        dash_slash_timer = dash_slash_duration
        attack_timer = dash_slash_duration
        dash_slash_width = w["slash_width"]

        for monster in monsters:
            if monster["alive"] and rect_hits_line(
                monster["rect"],
                dash_start_pos,
                dash_end_pos,
                dash_slash_width
            ):
                damage_monster(monster, w["damage"])

        attack_cooldown_timer = w["cooldown"]
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

    for monster in monsters:
        if monster["alive"] and attack_rect.colliderect(monster["rect"]):
            damage_monster(monster, w["damage"])


def update_flag_hitbox():
    global flag_has_hit_enemy, flag_attack_polygon

    if not flag_swinging:
        flag_attack_polygon = []
        return

    if weapon()["name"] != "Flag":
        return

    flag_attack_polygon = build_flag_attack_polygon()

    if flag_has_hit_enemy:
        return

    for monster in monsters:
        if monster["alive"] and rect_hits_polygon(monster["rect"], flag_attack_polygon):
            damage_monster(monster, weapon()["damage"])
            flag_has_hit_enemy = True
            break


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


def draw_spear_in_hand():
    d = pygame.Vector2(player_direction.x, player_direction.y)

    if d.length() == 0:
        d = pygame.Vector2(0, 1)

    d = d.normalize()

    start = pygame.Vector2(player.centerx, player.centery)
    end = start + d * 45

    pygame.draw.line(
        screen,
        SPEAR_COLOR,
        (int(start.x), int(start.y)),
        (int(end.x), int(end.y)),
        5
    )

    left = rotate(d, math.radians(150)) * 13
    right = rotate(d, math.radians(-150)) * 13

    pygame.draw.polygon(
        screen,
        SPEAR_TIP,
        [
            (int(end.x), int(end.y)),
            (int(end.x + left.x), int(end.y + left.y)),
            (int(end.x + right.x), int(end.y + right.y))
        ]
    )


def draw_flying_spear(spear):
    d = spear["dir"]
    center = pygame.Vector2(spear["rect"].centerx, spear["rect"].centery)

    start = center - d * 18
    end = center + d * 22

    pygame.draw.line(
        screen,
        SPEAR_COLOR,
        (int(start.x), int(start.y)),
        (int(end.x), int(end.y)),
        5
    )

    left = rotate(d, math.radians(150)) * 12
    right = rotate(d, math.radians(-150)) * 12

    pygame.draw.polygon(
        screen,
        SPEAR_TIP,
        [
            (int(end.x), int(end.y)),
            (int(end.x + left.x), int(end.y + left.y)),
            (int(end.x + right.x), int(end.y + right.y))
        ]
    )


def draw_dual_blades_in_hand():
    d = pygame.Vector2(player_direction.x, player_direction.y)

    if d.length() == 0:
        d = pygame.Vector2(0, 1)

    d = d.normalize()
    side = pygame.Vector2(-d.y, d.x)
    center = pygame.Vector2(player.centerx, player.centery)

    long_start = center + side * 8
    long_end = long_start + d * 48

    pygame.draw.line(
        screen,
        DUAL_LONG,
        (int(long_start.x), int(long_start.y)),
        (int(long_end.x), int(long_end.y)),
        5
    )

    short_start = center - side * 9
    short_end = short_start + d * 32

    pygame.draw.line(
        screen,
        DUAL_SHORT,
        (int(short_start.x), int(short_start.y)),
        (int(short_end.x), int(short_end.y)),
        5
    )

    pygame.draw.circle(screen, WHITE, (int(long_start.x), int(long_start.y)), 4)
    pygame.draw.circle(screen, WHITE, (int(short_start.x), int(short_start.y)), 4)


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

    elif w["name"] == "Spear":
        draw_spear_in_hand()

    elif w["name"] == "Dual Blades":
        draw_dual_blades_in_hand()


def draw_weapon_list():
    x = WIDTH // 2 - 260
    y = HEIGHT // 2 - 220

    pygame.draw.rect(screen, DARK_GRAY, (x, y, 520, 450))
    pygame.draw.rect(screen, WHITE, (x, y, 520, 450), 3)

    title = font.render("WEAPON LIST", True, WHITE)
    guide = small_font.render(
        "I: Close | UP/DOWN: Select | ENTER: Equip",
        True,
        LIGHT_GRAY
    )

    screen.blit(title, (x + 185, y + 20))
    screen.blit(guide, (x + 65, y + 55))

    for i, w in enumerate(weapons):
        rect = pygame.Rect(x + 40, y + 100 + i * 65, 440, 55)

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
            "Type: " + w["type"] + " | Damage: " + get_weapon_damage_text(w),
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

    pygame.draw.rect(screen, DARK_GRAY, (x, y, 310, 265))
    pygame.draw.rect(screen, WHITE, (x, y, 310, 265), 2)

    spawn_mode_text = "STATIC" if spawn_static_monster else "CHASE"
    freeze_text = "ON" if freeze_all_monsters else "OFF"

    items = [
        ("DEVELOPER PANEL", WHITE),
        ("F3: Collapse / Open", GRAY),
        ("F4: Player God: " + ("ON" if player_invincible else "OFF"),
         GREEN if player_invincible else RED),
        ("F5: Enemy God: " + ("ON" if enemy_invincible else "OFF"),
         GREEN if enemy_invincible else RED),
        ("F6: Hitbox: " + ("ON" if show_hitbox else "OFF"),
         GREEN if show_hitbox else RED),
        ("N: Spawn Here", GRAY),
        ("M: Spawn Mode: " + spawn_mode_text, WHITE),
        ("B: Freeze All: " + freeze_text, GREEN if freeze_all_monsters else RED),
        ("ESC: Exit", GRAY)
    ]

    for i, item in enumerate(items):
        used_font = font if i == 0 else small_font
        text = used_font.render(item[0], True, item[1])
        screen.blit(text, (x + 15, y + 15 + i * 25))


spawn_monster(WIDTH - 300, HEIGHT // 2, static=False)

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

                elif event.key == pygame.K_n:
                    spawn_monster(player.centerx - 20, player.centery - 20)

                elif event.key == pygame.K_m:
                    spawn_static_monster = not spawn_static_monster

                elif event.key == pygame.K_b:
                    freeze_all_monsters = not freeze_all_monsters

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

    if dash_slashing:
        dash_slash_timer -= 1

        if dash_slash_timer <= 0:
            dash_slashing = False

    if flag_swinging:
        flag_timer -= 1

        if flag_timer <= 0:
            flag_swinging = False

    update_flag_hitbox()
    update_monsters()
    monster_touch_player()

    if shoot_timer > 0:
        shoot_timer -= 1

    if attack_cooldown_timer > 0:
        attack_cooldown_timer -= 1

    if spear_splash_timer > 0:
        spear_splash_timer -= 1

        if spear_splash_timer <= 0:
            spear_splash_pos = None

    for bullet in bullets[:]:
        bullet["pos"] += bullet["dir"] * bullet_speed
        bullet["rect"].x = int(bullet["pos"].x)
        bullet["rect"].y = int(bullet["pos"].y)

        if not screen.get_rect().colliderect(bullet["rect"]):
            bullets.remove(bullet)
            continue

        hit_monster = None

        for monster in monsters:
            if monster["alive"] and bullet["rect"].colliderect(monster["rect"]):
                hit_monster = monster
                break

        if hit_monster is not None:
            damage_monster(hit_monster, bullet["damage"])
            bullets.remove(bullet)

    for spear in spears[:]:
        spear["pos"] += spear["dir"] * spear["speed"]
        spear["rect"].x = int(spear["pos"].x)
        spear["rect"].y = int(spear["pos"].y)

        if not screen.get_rect().colliderect(spear["rect"]):
            spears.remove(spear)
            continue

        hit_monster = None

        for monster in monsters:
            if monster["alive"] and spear["rect"].colliderect(monster["rect"]):
                hit_monster = monster
                break

        if hit_monster is not None:
            hit_pos = pygame.Vector2(
                hit_monster["rect"].centerx,
                hit_monster["rect"].centery
            )

            damage_monster(hit_monster, spear["damage"])

            splash_roll = random.randint(1, 100)
            splash_triggered = splash_roll <= spear["splash_chance"]

            if splash_triggered:
                spear_splash_pos = hit_pos
                spear_splash_timer = 14
                last_spear_splash = True
                last_spear_splash_damage = spear["splash_damage"]

                for monster in monsters:
                    if monster is hit_monster:
                        continue

                    if monster["alive"] and rect_in_circle(
                        monster["rect"],
                        spear_splash_pos,
                        spear["splash_range"]
                    ):
                        damage_monster(monster, last_spear_splash_damage)

            else:
                last_spear_splash = False
                last_spear_splash_damage = 0

            spears.remove(spear)

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

    for monster in monsters:
        if not monster["alive"]:
            continue

        rect = monster["rect"]

        pygame.draw.rect(screen, MONSTER_COLOR, rect)

        if monster["static"]:
            pygame.draw.rect(screen, WHITE, rect, 3)
        else:
            pygame.draw.rect(screen, MONSTER_OUTLINE, rect, 2)

        if enemy_invincible:
            pygame.draw.rect(screen, GREEN, rect, 3)

        hp_ratio = monster["hp"] / monster["max_hp"]

        pygame.draw.rect(screen, RED, (rect.x, rect.y - 10, 40, 5))
        pygame.draw.rect(
            screen,
            GREEN,
            (rect.x, rect.y - 10, max(0, hp_ratio * 40), 5)
        )

        monster_text = small_font.render(
            str(monster["hp"]),
            True,
            WHITE
        )

        screen.blit(monster_text, (rect.x + 4, rect.y - 32))

    if dash_slashing:
        pygame.draw.line(
            screen,
            DUAL_SLASH,
            (int(dash_start_pos.x), int(dash_start_pos.y)),
            (int(dash_end_pos.x), int(dash_end_pos.y)),
            dash_slash_width
        )

        pygame.draw.line(
            screen,
            WHITE,
            (int(dash_start_pos.x), int(dash_start_pos.y)),
            (int(dash_end_pos.x), int(dash_end_pos.y)),
            3
        )

        if show_hitbox:
            pygame.draw.circle(
                screen,
                WHITE,
                (int(dash_start_pos.x), int(dash_start_pos.y)),
                dash_slash_width // 2,
                2
            )
            pygame.draw.circle(
                screen,
                WHITE,
                (int(dash_end_pos.x), int(dash_end_pos.y)),
                dash_slash_width // 2,
                2
            )

    elif attacking:
        if weapon()["name"] == "Flag":
            if show_hitbox and len(flag_attack_polygon) >= 3:
                pygame.draw.lines(screen, WHITE, True, flag_attack_polygon, 3)
        else:
            pygame.draw.rect(screen, weapon()["color"], attack_rect)

    for bullet in bullets:
        pygame.draw.rect(screen, ORANGE, bullet["rect"])

    for spear in spears:
        draw_flying_spear(spear)

    if spear_splash_timer > 0 and spear_splash_pos is not None:
        pygame.draw.circle(
            screen,
            SPEAR_SPLASH,
            (int(spear_splash_pos.x), int(spear_splash_pos.y)),
            weapon()["splash_range"],
            2
        )

        if show_hitbox:
            pygame.draw.circle(
                screen,
                WHITE,
                (int(spear_splash_pos.x), int(spear_splash_pos.y)),
                weapon()["splash_range"],
                3
            )

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
            "Type: " + weapon()["type"] + " | Damage: " + get_weapon_damage_text(weapon()),
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
            "Spears: " + str(len(spears)),
            True,
            SPEAR_COLOR
        ),
        (20, 160)
    )

    alive_monsters = sum(1 for monster in monsters if monster["alive"])
    spawn_mode_text = "STATIC" if spawn_static_monster else "CHASE"
    freeze_text = "ON" if freeze_all_monsters else "OFF"

    screen.blit(
        small_font.render(
            "Monsters: "
            + str(alive_monsters)
            + " | N: Spawn Here | M: "
            + spawn_mode_text
            + " | B Freeze: "
            + freeze_text,
            True,
            MONSTER_COLOR
        ),
        (20, 185)
    )

    screen.blit(
        small_font.render(
            "Player God: " + ("ON" if player_invincible else "OFF"),
            True,
            GREEN if player_invincible else GRAY
        ),
        (20, 210)
    )

    screen.blit(
        small_font.render(
            "Enemy God: " + ("ON" if enemy_invincible else "OFF"),
            True,
            GREEN if enemy_invincible else GRAY
        ),
        (20, 235)
    )

    screen.blit(
        small_font.render(
            "Attack Cooldown: " + str(attack_cooldown_timer),
            True,
            LIGHT_GRAY
        ),
        (20, 265)
    )

    screen.blit(
        small_font.render(
            "Shoot Cooldown: " + str(shoot_timer),
            True,
            LIGHT_GRAY
        ),
        (20, 290)
    )

    if weapon()["name"] == "Spear":
        screen.blit(
            small_font.render(
                "Spear: Direct "
                + str(weapon()["damage"])
                + " | Circle Splash: "
                + ("YES" if last_spear_splash else "NO")
                + " | Splash Damage: "
                + str(last_spear_splash_damage)
                + " | Chance: "
                + str(weapon()["splash_chance"])
                + "%"
                + " | Range: "
                + str(weapon()["splash_range"]),
                True,
                SPEAR_COLOR
            ),
            (20, 315)
        )

        screen.blit(
            small_font.render(
                "Rule: Direct target does NOT take splash. Splash only hits nearby monsters.",
                True,
                LIGHT_GRAY
            ),
            (20, 340)
        )

    if weapon()["name"] == "Dual Blades":
        screen.blit(
            small_font.render(
                "Dual Blades: Dash slash in a straight line | Damage: "
                + str(weapon()["damage"]),
                True,
                DUAL_SLASH
            ),
            (20, 315)
        )

        screen.blit(
            small_font.render(
                "Rule: SPACE makes player dash and slash along the dash path.",
                True,
                LIGHT_GRAY
            ),
            (20, 340)
        )

    screen.blit(
        font.render(
            "Move: WASD/Arrow | TAB: Switch | I: Weapons | SPACE: Use | N: Spawn Here | M: Spawn Mode | B: Freeze Monsters",
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
pygame.mouse.set_visible(True)
pygame.quit()