import pygame
import weapons

pygame.init()

# =========================
# SCREEN
# =========================
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("2D Dungeon Game")

pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

clock = pygame.time.Clock()

# =========================
# COLORS
# =========================
BLACK = (20, 20, 20)
BLUE = (0, 200, 255)
RED = (220, 50, 50)
WHITE = (255, 255, 255)
GREEN = (0, 220, 80)
GRAY = (120, 120, 120)
LIGHT_GRAY = (170, 170, 170)
DARK_GRAY = (45, 45, 45)

MONSTER_COLOR = (210, 60, 80)
MONSTER_OUTLINE = (255, 120, 120)

# =========================
# FONTS
# =========================
font = pygame.font.SysFont(None, 30)
small_font = pygame.font.SysFont(None, 24)
big_font = pygame.font.SysFont(None, 70)

# =========================
# PLAYER
# =========================
player = pygame.Rect(100, 100, 40, 40)
player_speed = 5
player_direction = pygame.Vector2(0, 1)
player_hp = 100

# =========================
# MONSTERS
# =========================
monsters = []
monster_speed = 2.2
monster_touch_damage = 10
monster_touch_cooldown = 60
spawn_static_monster = False
freeze_all_monsters = False

# =========================
# DEV
# =========================
dev_panel_open = True
player_invincible = False
enemy_invincible = False
show_hitbox = False


# =========================
# MONSTER FUNCTIONS
# =========================
def spawn_monster(x=None, y=None, static=None):
    if static is None:
        static = spawn_static_monster

    if x is None:
        x = player.centerx - 20
    if y is None:
        y = player.centery - 20

    monsters.append({
        "rect": pygame.Rect(x, y, 40, 40),
        "hp": 100,
        "max_hp": 100,
        "speed": monster_speed,
        "touch_timer": 0,
        "alive": True,
        "static": static
    })


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


# =========================
# DRAW DEV
# =========================
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
        ("F4: Player God: " + ("ON" if player_invincible else "OFF"), GREEN if player_invincible else RED),
        ("F5: Enemy God: " + ("ON" if enemy_invincible else "OFF"), GREEN if enemy_invincible else RED),
        ("F6: Hitbox: " + ("ON" if show_hitbox else "OFF"), GREEN if show_hitbox else RED),
        ("N: Spawn Here", GRAY),
        ("M: Spawn Mode: " + spawn_mode_text, WHITE),
        ("B: Freeze All: " + freeze_text, GREEN if freeze_all_monsters else RED),
        ("ESC: Exit", GRAY)
    ]

    for i, item in enumerate(items):
        used_font = font if i == 0 else small_font
        text = used_font.render(item[0], True, item[1])
        screen.blit(text, (x + 15, y + 15 + i * 25))


# =========================
# START GAME
# =========================
spawn_monster(WIDTH - 300, HEIGHT // 2, static=False)

running = True

while running:
    clock.tick(60)

    # =========================
    # EVENTS
    # =========================
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if weapons.weapon_list_open:
                    weapons.weapon_list_open = False
                else:
                    running = False

            elif event.key == pygame.K_i:
                weapons.weapon_list_open = not weapons.weapon_list_open

            elif weapons.weapon_list_open:
                if event.key == pygame.K_UP:
                    weapons.selected_weapon = (weapons.selected_weapon - 1) % len(weapons.weapons)

                elif event.key == pygame.K_DOWN:
                    weapons.selected_weapon = (weapons.selected_weapon + 1) % len(weapons.weapons)

                elif event.key == pygame.K_RETURN:
                    weapons.equip(weapons.selected_weapon)
                    weapons.weapon_list_open = False

            else:
                if event.key == pygame.K_TAB:
                    weapons.equip((weapons.current_weapon + 1) % len(weapons.weapons))

                elif event.key == pygame.K_SPACE:
                    weapons.use_weapon(
                        player,
                        player_direction,
                        monsters,
                        damage_monster,
                        screen.get_rect(),
                        WIDTH,
                        HEIGHT
                    )

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

    # =========================
    # PLAYER MOVE
    # =========================
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

        weapons.set_flag_direction(player_direction)

        player.x += int(move.x * player_speed)
        player.y += int(move.y * player_speed)

    player.clamp_ip(screen.get_rect())

    # =========================
    # UPDATE
    # =========================
    weapons.update(
        player,
        player_direction,
        monsters,
        damage_monster,
        screen.get_rect()
    )

    update_monsters()
    monster_touch_player()

    # =========================
    # DRAW
    # =========================
    screen.fill(BLACK)

    if weapons.flag_swinging and weapons.weapon()["name"] == "Flag":
        weapons.draw_fan(screen, player)

    pygame.draw.rect(screen, BLUE, player)

    if player_invincible:
        pygame.draw.rect(screen, GREEN, player, 3)

    look = (
        player.centerx + int(player_direction.x * 25),
        player.centery + int(player_direction.y * 25)
    )

    pygame.draw.line(screen, WHITE, player.center, look, 3)

    weapons.draw_weapon_icon(screen, player, player_direction)

    # Monsters
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
            (rect.x, rect.y - 10, int(max(0, hp_ratio * 40)), 5)
        )

        monster_text = small_font.render(str(monster["hp"]), True, WHITE)
        screen.blit(monster_text, (rect.x + 4, rect.y - 32))

    weapons.draw_attacks(screen, show_hitbox)
    weapons.draw_projectiles(screen, show_hitbox)

    # =========================
    # HUD
    # =========================
    pygame.draw.rect(screen, RED, (20, 50, 100, 10))
    pygame.draw.rect(screen, GREEN, (20, 50, max(0, player_hp), 10))

    screen.blit(
        font.render("Player HP: " + str(player_hp), True, WHITE),
        (20, 20)
    )

    screen.blit(
        font.render(
            "Weapon: " + weapons.weapon()["name"] + " | SPACE",
            True,
            weapons.weapon()["color"]
        ),
        (20, 75)
    )

    screen.blit(
        small_font.render(
            "Type: "
            + weapons.weapon()["type"]
            + " | Damage: "
            + weapons.get_weapon_damage_text(weapons.weapon()),
            True,
            WHITE
        ),
        (20, 105)
    )

    screen.blit(
        font.render(
            "Projectiles Active: " + str(weapons.projectile_count()),
            True,
            weapons.PURPLE
        ),
        (20, 135)
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
        (20, 165)
    )

    screen.blit(
        small_font.render(
            "Player God: " + ("ON" if player_invincible else "OFF"),
            True,
            GREEN if player_invincible else GRAY
        ),
        (20, 190)
    )

    screen.blit(
        small_font.render(
            "Enemy God: " + ("ON" if enemy_invincible else "OFF"),
            True,
            GREEN if enemy_invincible else GRAY
        ),
        (20, 215)
    )

    screen.blit(
        small_font.render(
            "Attack Cooldown: " + str(weapons.attack_cooldown_timer),
            True,
            LIGHT_GRAY
        ),
        (20, 245)
    )

    # Weapon info
    if weapons.weapon()["name"] == "Sword":
        screen.blit(
            small_font.render(
                "Sword: Straight long slash | Range: "
                + str(weapons.weapon()["range"])
                + " | Width: "
                + str(weapons.weapon()["size"]),
                True,
                weapons.YELLOW
            ),
            (20, 280)
        )

    elif weapons.weapon()["name"] == "Spear":
        screen.blit(
            small_font.render(
                "Spear: Direct "
                + str(weapons.weapon()["damage"])
                + " | Splash Damage: "
                + str(weapons.last_spear_splash_damage)
                + " | Chance: "
                + str(weapons.weapon()["splash_chance"])
                + "%",
                True,
                weapons.SPEAR_COLOR
            ),
            (20, 280)
        )

        screen.blit(
            small_font.render(
                "Rule: Direct target does NOT take splash. Splash only hits nearby monsters.",
                True,
                LIGHT_GRAY
            ),
            (20, 305)
        )

    elif weapons.weapon()["name"] == "Dual Blades":
        screen.blit(
            small_font.render(
                "Dual Blades: Dash slash in a straight line",
                True,
                weapons.DUAL_SLASH
            ),
            (20, 280)
        )

    elif weapons.weapon()["name"] == "Boomerang":
        screen.blit(
            small_font.render(
                "Boomerang: Flies out, then returns to player",
                True,
                weapons.PURPLE
            ),
            (20, 280)
        )

    elif weapons.weapon()["name"] == "Earthshaker":
        screen.blit(
            small_font.render(
                "Earthshaker: Expanding AOE shockwave",
                True,
                weapons.BROWN
            ),
            (20, 280)
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

    if weapons.weapon_list_open:
        weapons.draw_weapon_list(screen, font, small_font, WIDTH, HEIGHT)

    if player_hp <= 0:
        screen.blit(
            big_font.render("GAME OVER", True, RED),
            (WIDTH // 2 - 160, HEIGHT // 2 - 40)
        )

    pygame.display.flip()

pygame.event.set_grab(False)
pygame.mouse.set_visible(True)
pygame.quit()