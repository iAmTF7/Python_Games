import pygame
import math
import random

# =========================
# COLORS
# =========================
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

DUAL_LONG = (180, 220, 255)
DUAL_SHORT = (255, 220, 120)
DUAL_SLASH = (120, 210, 255)

# =========================
# WEAPONS
# =========================
weapons = [
    {
        "name": "Sword",
        "type": "melee",
        "damage": 25,
        "range": 120,
        "size": 16,
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
    },
    {
        "name": "Boomerang",
        "type": "returning",
        "damage": 15,
        "speed": 14,
        "return_speed": 16,
        "out_duration": 25,
        "size": 24,
        "color": PURPLE,
        "cooldown": 45
    },
    {
        "name": "Earthshaker",
        "type": "shockwave",
        "damage": 25,
        "max_radius": 160,
        "expansion_speed": 12,
        "knockback": 40,
        "color": BROWN,
        "cooldown": 60
    }
]

current_weapon = 0
selected_weapon = 0
weapon_list_open = False

# =========================
# PROJECTILES / ATTACKS
# =========================
bullets = []
bullet_speed = 9
bullet_size = 10
shoot_timer = 0

spears = []
spear_splash_timer = 0
spear_splash_pos = None
last_spear_splash = False
last_spear_splash_damage = 0
last_spear_splash_range = 162

boomerangs = []
shockwaves = []

attacking = False
attack_timer = 0
attack_rect = pygame.Rect(0, 0, 0, 0)
attack_cooldown_timer = 0

# Sword
sword_attack_start = pygame.Vector2(0, 0)
sword_attack_end = pygame.Vector2(0, 0)
sword_attack_width = 16

# Dash slash
dash_slashing = False
dash_slash_timer = 0
dash_slash_duration = 8
dash_start_pos = pygame.Vector2(0, 0)
dash_end_pos = pygame.Vector2(0, 0)
dash_slash_width = 42

# Flag
flag_swinging = False
flag_timer = 0
flag_duration = 12
flag_side = 1
flag_wave = 0
flag_attack_direction = pygame.Vector2(0, 1)
flag_has_hit_enemy = False
flag_attack_polygon = []

# =========================
# BASIC
# =========================
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

    if w["name"] == "Boomerang":
        return str(w["damage"]) + " | Piercing & Return"

    if w["name"] == "Earthshaker":
        return str(w["damage"]) + " | AOE & Knockback"

    if w["name"] == "Sword":
        return str(w["damage"]) + " | Line: " + str(w["range"]) + " | Width: " + str(w["size"])

    return str(w["damage"])


# =========================
# COLLISION HELPERS
# =========================
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

    rect_points = [rect.topleft, rect.topright, rect.bottomright, rect.bottomleft]

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


# =========================
# FLAG HELPERS
# =========================
def set_flag_direction(direction):
    global flag_attack_direction

    if flag_swinging and direction.length() > 0:
        flag_attack_direction = pygame.Vector2(direction.x, direction.y)


def get_flag_angle():
    if not flag_swinging:
        return 0

    progress = 1 - flag_timer / flag_duration
    start_angle = -45 * flag_side
    end_angle = 45 * flag_side

    return start_angle + (end_angle - start_angle) * progress


def build_flag_attack_polygon(player):
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


def update_flag_hitbox(player, monsters, damage_monster):
    global flag_has_hit_enemy, flag_attack_polygon

    if not flag_swinging:
        flag_attack_polygon = []
        return

    if weapon()["name"] != "Flag":
        return

    flag_attack_polygon = build_flag_attack_polygon(player)

    if flag_has_hit_enemy:
        return

    for monster in monsters:
        if monster["alive"] and rect_hits_polygon(monster["rect"], flag_attack_polygon):
            damage_monster(monster, weapon()["damage"])
            flag_has_hit_enemy = True
            break


# =========================
# MAKE PROJECTILES
# =========================
def make_bullet(player, player_direction):
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


def make_spear(player, player_direction):
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


def make_boomerang(player, player_direction):
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
        "return_speed": w["return_speed"],
        "timer": w["out_duration"],
        "size": w["size"],
        "returning": False,
        "hit_targets": []
    }


# =========================
# USE WEAPON
# =========================
def use_weapon(player, player_direction, monsters, damage_monster, screen_rect, width, height):
    global attacking, attack_timer, attack_cooldown_timer
    global shoot_timer
    global flag_swinging, flag_timer, flag_side
    global flag_attack_direction, flag_has_hit_enemy, flag_attack_polygon
    global dash_slashing, dash_slash_timer
    global dash_start_pos, dash_end_pos, dash_slash_width
    global sword_attack_start, sword_attack_end, sword_attack_width

    w = weapon()

    # Gun
    if w["type"] == "ranged":
        if shoot_timer <= 0:
            bullets.append(make_bullet(player, player_direction))
            shoot_timer = w["cooldown"]
        return

    # Spear
    if w["type"] == "thrown_spear":
        if attack_cooldown_timer <= 0:
            spears.append(make_spear(player, player_direction))
            attack_cooldown_timer = w["cooldown"]
        return

    # Boomerang
    if w["type"] == "returning":
        if attack_cooldown_timer <= 0:
            boomerangs.append(make_boomerang(player, player_direction))
            attack_cooldown_timer = w["cooldown"]
        return

    # Earthshaker
    if w["type"] == "shockwave":
        if attack_cooldown_timer <= 0:
            shockwaves.append({
                "pos": pygame.Vector2(player.centerx, player.centery),
                "current_radius": 10,
                "max_radius": w["max_radius"],
                "expansion_speed": w["expansion_speed"],
                "damage": w["damage"],
                "knockback": w["knockback"],
                "hit_targets": []
            })
            attack_cooldown_timer = w["cooldown"]
        return

    # Dual Blades
    if w["type"] == "dash_slash":
        if attack_cooldown_timer > 0:
            return

        d = pygame.Vector2(player_direction.x, player_direction.y)

        if d.length() == 0:
            d = pygame.Vector2(0, 1)

        d = d.normalize()

        dash_start_pos = pygame.Vector2(player.centerx, player.centery)
        target_pos = dash_start_pos + d * w["dash_distance"]

        target_x = max(player.width // 2, min(width - player.width // 2, target_pos.x))
        target_y = max(player.height // 2, min(height - player.height // 2, target_pos.y))

        dash_end_pos = pygame.Vector2(target_x, target_y)

        player.centerx = int(dash_end_pos.x)
        player.centery = int(dash_end_pos.y)
        player.clamp_ip(screen_rect)

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

    # Sword
    if w["name"] == "Sword":
        attack_timer = 8
        attack_cooldown_timer = w["cooldown"]

        d = pygame.Vector2(player_direction.x, player_direction.y)

        if d.length() == 0:
            d = pygame.Vector2(0, 1)

        d = d.normalize()

        sword_attack_start = pygame.Vector2(player.centerx, player.centery)
        sword_attack_end = sword_attack_start + d * w["range"]
        sword_attack_width = w["size"]

        for monster in monsters:
            if monster["alive"] and rect_hits_line(
                monster["rect"],
                sword_attack_start,
                sword_attack_end,
                sword_attack_width
            ):
                damage_monster(monster, w["damage"])

        return

    # Flag
    if w["name"] == "Flag":
        attack_timer = flag_duration
        attack_cooldown_timer = w["cooldown"]

        flag_swinging = True
        flag_timer = flag_duration
        flag_side *= -1

        flag_attack_direction = pygame.Vector2(player_direction.x, player_direction.y)
        flag_has_hit_enemy = False
        flag_attack_polygon = build_flag_attack_polygon(player)
        return


# =========================
# UPDATE
# =========================
def update(player, player_direction, monsters, damage_monster, screen_rect):
    global flag_wave
    global attacking, attack_timer
    global dash_slashing, dash_slash_timer
    global flag_swinging, flag_timer
    global shoot_timer, attack_cooldown_timer
    global spear_splash_timer, spear_splash_pos
    global last_spear_splash, last_spear_splash_damage, last_spear_splash_range

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

    update_flag_hitbox(player, monsters, damage_monster)

    if shoot_timer > 0:
        shoot_timer -= 1

    if attack_cooldown_timer > 0:
        attack_cooldown_timer -= 1

    if spear_splash_timer > 0:
        spear_splash_timer -= 1
        if spear_splash_timer <= 0:
            spear_splash_pos = None

    # Bullets
    for bullet in bullets[:]:
        bullet["pos"] += bullet["dir"] * bullet_speed
        bullet["rect"].x = int(bullet["pos"].x)
        bullet["rect"].y = int(bullet["pos"].y)

        if not screen_rect.colliderect(bullet["rect"]):
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

    # Spears
    for spear in spears[:]:
        spear["pos"] += spear["dir"] * spear["speed"]
        spear["rect"].x = int(spear["pos"].x)
        spear["rect"].y = int(spear["pos"].y)

        if not screen_rect.colliderect(spear["rect"]):
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

            if splash_roll <= spear["splash_chance"]:
                spear_splash_pos = hit_pos
                spear_splash_timer = 14
                last_spear_splash = True
                last_spear_splash_damage = spear["splash_damage"]
                last_spear_splash_range = spear["splash_range"]

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

    # Boomerangs
    for b in boomerangs[:]:
        if not b["returning"]:
            b["pos"] += b["dir"] * b["speed"]
            b["timer"] -= 1

            if b["timer"] <= 0:
                b["returning"] = True
                b["hit_targets"].clear()

        else:
            target = pygame.Vector2(player.centerx, player.centery)
            current = b["pos"]
            d = target - current

            if d.length() < 20:
                boomerangs.remove(b)
                continue

            if d.length() > 0:
                d = d.normalize()
                b["pos"] += d * b["return_speed"]

        b["rect"].x = int(b["pos"].x)
        b["rect"].y = int(b["pos"].y)

        for monster in monsters:
            if monster["alive"] and b["rect"].colliderect(monster["rect"]):
                if monster not in b["hit_targets"]:
                    damage_monster(monster, b["damage"])
                    b["hit_targets"].append(monster)

    # Shockwaves
    for wave in shockwaves[:]:
        wave["current_radius"] += wave["expansion_speed"]

        if wave["current_radius"] >= wave["max_radius"]:
            shockwaves.remove(wave)
            continue

        for monster in monsters:
            if monster["alive"] and monster not in wave["hit_targets"]:
                if rect_in_circle(monster["rect"], wave["pos"], wave["current_radius"]):
                    damage_monster(monster, wave["damage"])
                    wave["hit_targets"].append(monster)

                    m_center = pygame.Vector2(
                        monster["rect"].centerx,
                        monster["rect"].centery
                    )

                    push_dir = m_center - wave["pos"]

                    if push_dir.length() > 0:
                        push_dir = push_dir.normalize()

                        monster["rect"].x += int(push_dir.x * wave["knockback"])
                        monster["rect"].y += int(push_dir.y * wave["knockback"])
                        monster["rect"].clamp_ip(screen_rect)


# =========================
# DRAW WEAPONS
# =========================
def draw_flag_cloth(screen, px, py, direction):
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
        wave = math.sin(flag_wave * 0.22 + t * math.pi * 2.2) * power * t

        cx = px + side.x * length * t + d.x * wave
        cy = py + side.y * length * t + d.y * wave
        h = height * (1 - t * 0.08) / 2

        top.append((int(cx - d.x * h), int(cy - d.y * h)))
        bottom.append((int(cx + d.x * h), int(cy + d.y * h)))

    points = top + bottom[::-1]

    pygame.draw.polygon(screen, FLAG_RED, points)
    pygame.draw.lines(screen, WHITE, True, points, 2)


def draw_flag(screen, player, player_direction):
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

    pygame.draw.line(screen, BROWN, player.center, (int(end.x), int(end.y)), 6)
    pygame.draw.circle(screen, LIGHT_GRAY, (int(end.x), int(end.y)), 7)

    draw_flag_cloth(screen, end.x, end.y, d)


def draw_fan(screen, player):
    polygon = build_flag_attack_polygon(player)

    if len(polygon) < 3:
        return

    pygame.draw.polygon(screen, FLAG_DARK, polygon)
    pygame.draw.lines(screen, FLAG_LIGHT, True, polygon, 3)


def draw_spear_in_hand(screen, player, player_direction):
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


def draw_flying_spear(screen, spear):
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


def draw_dual_blades_in_hand(screen, player, player_direction):
    d = pygame.Vector2(player_direction.x, player_direction.y)

    if d.length() == 0:
        d = pygame.Vector2(0, 1)

    d = d.normalize()

    side = pygame.Vector2(-d.y, d.x)
    center = pygame.Vector2(player.centerx, player.centery)

    long_start = center + side * 8
    long_end = long_start + d * 48

    short_start = center - side * 9
    short_end = short_start + d * 32

    pygame.draw.line(
        screen,
        DUAL_LONG,
        (int(long_start.x), int(long_start.y)),
        (int(long_end.x), int(long_end.y)),
        5
    )

    pygame.draw.line(
        screen,
        DUAL_SHORT,
        (int(short_start.x), int(short_start.y)),
        (int(short_end.x), int(short_end.y)),
        5
    )

    pygame.draw.circle(screen, WHITE, (int(long_start.x), int(long_start.y)), 4)
    pygame.draw.circle(screen, WHITE, (int(short_start.x), int(short_start.y)), 4)


def draw_weapon_icon(screen, player, player_direction):
    w = weapon()

    d = pygame.Vector2(player_direction.x, player_direction.y)

    if d.length() == 0:
        d = pygame.Vector2(0, 1)

    d = d.normalize()

    if w["name"] == "Sword":
        end = (
            player.centerx + int(d.x * 35),
            player.centery + int(d.y * 35)
        )
        pygame.draw.line(screen, YELLOW, player.center, end, 5)

    elif w["name"] == "Gun":
        pygame.draw.rect(
            screen,
            ORANGE,
            (player.centerx - 8, player.centery - 8, 16, 16)
        )

    elif w["name"] == "Flag":
        draw_flag(screen, player, player_direction)

    elif w["name"] == "Spear":
        draw_spear_in_hand(screen, player, player_direction)

    elif w["name"] == "Dual Blades":
        draw_dual_blades_in_hand(screen, player, player_direction)

    elif w["name"] == "Boomerang":
        pygame.draw.circle(
            screen,
            PURPLE,
            (player.centerx + int(d.x * 20), player.centery + int(d.y * 20)),
            8,
            3
        )

    elif w["name"] == "Earthshaker":
        head_center = (
            player.centerx + int(d.x * 25),
            player.centery + int(d.y * 25)
        )

        pygame.draw.line(screen, BROWN, player.center, head_center, 4)
        pygame.draw.rect(
            screen,
            GRAY,
            (head_center[0] - 10, head_center[1] - 10, 20, 20)
        )


def draw_attacks(screen, show_hitbox):
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

        elif weapon()["name"] == "Sword":
            pygame.draw.line(
                screen,
                YELLOW,
                (int(sword_attack_start.x), int(sword_attack_start.y)),
                (int(sword_attack_end.x), int(sword_attack_end.y)),
                sword_attack_width
            )

            pygame.draw.circle(
                screen,
                WHITE,
                (int(sword_attack_end.x), int(sword_attack_end.y)),
                5
            )

            if show_hitbox:
                pygame.draw.line(
                    screen,
                    WHITE,
                    (int(sword_attack_start.x), int(sword_attack_start.y)),
                    (int(sword_attack_end.x), int(sword_attack_end.y)),
                    2
                )

        else:
            pygame.draw.rect(screen, weapon()["color"], attack_rect)


def draw_projectiles(screen, show_hitbox):
    for bullet in bullets:
        pygame.draw.rect(screen, ORANGE, bullet["rect"])

    for spear in spears:
        draw_flying_spear(screen, spear)

    for b in boomerangs:
        pygame.draw.circle(
            screen,
            PURPLE,
            (int(b["rect"].centerx), int(b["rect"].centery)),
            b["size"] // 2,
            4
        )

    for wave in shockwaves:
        thickness = max(
            1,
            int(10 * (1 - wave["current_radius"] / wave["max_radius"]))
        )

        pygame.draw.circle(
            screen,
            BROWN,
            (int(wave["pos"].x), int(wave["pos"].y)),
            int(wave["current_radius"]),
            thickness
        )

    if spear_splash_timer > 0 and spear_splash_pos is not None:
        pygame.draw.circle(
            screen,
            SPEAR_SPLASH,
            (int(spear_splash_pos.x), int(spear_splash_pos.y)),
            last_spear_splash_range,
            2
        )

        if show_hitbox:
            pygame.draw.circle(
                screen,
                WHITE,
                (int(spear_splash_pos.x), int(spear_splash_pos.y)),
                last_spear_splash_range,
                3
            )


def draw_weapon_list(screen, font, small_font, width, height):
    x = width // 2 - 260
    y = height // 2 - 250

    pygame.draw.rect(screen, DARK_GRAY, (x, y, 520, 520))
    pygame.draw.rect(screen, WHITE, (x, y, 520, 520), 3)

    title = font.render("WEAPON LIST", True, WHITE)
    guide = small_font.render("I: Close | UP/DOWN: Select | ENTER: Equip", True, LIGHT_GRAY)

    screen.blit(title, (x + 185, y + 20))
    screen.blit(guide, (x + 65, y + 55))

    for i, w in enumerate(weapons):
        rect = pygame.Rect(x + 40, y + 90 + i * 55, 440, 48)

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

        screen.blit(name_text, (rect.x + 20, rect.y + 6))
        screen.blit(info_text, (rect.x + 20, rect.y + 28))


def projectile_count():
    return len(bullets) + len(spears) + len(boomerangs) + len(shockwaves)