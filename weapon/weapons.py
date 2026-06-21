"""Object-oriented weapon system with legacy-compatible module functions.

This file keeps the original public API used by the old demo:

    import weapons
    weapons.weapon()
    weapons.equip(index)
    weapons.use_weapon(...)
    weapons.update(...)
    weapons.draw_weapon_icon(...)
    weapons.draw_attacks(...)
    weapons.draw_projectiles(...)
    weapons.draw_weapon_list(...)

Internally, the old global procedural state has been moved into WeaponSystem,
weapon classes, attack-effect classes, and projectile classes.  The gameplay
numbers and mechanics are intentionally preserved from the original module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import Callable, Iterable, Optional

import pygame

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
# ORIGINAL WEAPON DATA
# =========================
DEFAULT_RANGED_ENERGY_COST = 2
ENERGY_AMMO_WEAPON_TYPES = {"ranged", "thrown_spear", "returning"}

WEAPON_DATA = [
    {
        "name": "Sword",
        "type": "melee",
        "damage": 25,
        "range": 120,
        "size": 16,
        "color": YELLOW,
        "cooldown": 30,
    },
    {
        "name": "Gun",
        "type": "ranged",
        "damage": 20,
        "range": 0,
        "size": 10,
        "color": ORANGE,
        "cooldown": 30,
    },
    {
        "name": "Flag",
        "type": "melee",
        "damage": 9,
        "range": 75,
        "size": 48,
        "color": FLAG_RED,
        "cooldown": 20,
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
        "cooldown": 45,
    },
    {
        "name": "Dual Blades",
        "type": "dash_slash",
        "damage": 18,
        "dash_distance": 140,
        "slash_width": 42,
        "color": DUAL_SLASH,
        "cooldown": 45,
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
        "cooldown": 45,
    },
    {
        "name": "Earthshaker",
        "type": "shockwave",
        "damage": 25,
        "max_radius": 160,
        "expansion_speed": 12,
        "knockback": 40,
        "color": BROWN,
        "cooldown": 60,
    },
]

# =========================
# SHARED HELPERS
# =========================
DamageFunction = Callable[[object, int], None]


def rotate(vec, angle):
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return pygame.Vector2(
        vec.x * cos_a - vec.y * sin_a,
        vec.x * sin_a + vec.y * cos_a,
    )


def normalized_direction(direction):
    d = pygame.Vector2(direction.x, direction.y)
    if d.length() == 0:
        d = pygame.Vector2(0, 1)
    return d.normalize()


def entity_rect(entity):
    """Return a pygame.Rect from either a Rect, dict, or object entity."""
    if isinstance(entity, pygame.Rect):
        return entity

    if isinstance(entity, dict):
        return entity["rect"]

    if hasattr(entity, "rect"):
        return entity.rect

    if hasattr(entity, "get_rect"):
        return entity.get_rect()

    raise AttributeError("Entity does not expose a rect")


def monster_alive(monster):
    if isinstance(monster, dict):
        return bool(monster.get("alive", True))

    if hasattr(monster, "is_alive"):
        return bool(monster.is_alive())

    return bool(getattr(monster, "alive", True))


def player_center(player):
    rect = entity_rect(player)
    return pygame.Vector2(rect.centerx, rect.centery)


def damage_text_for_data(w):
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


def get_weapon_damage_text(w):
    return damage_text_for_data(w)


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
        (rect.bottomleft, rect.topleft),
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
# CONTEXT
# =========================
@dataclass
class WeaponUseContext:
    player: object
    player_direction: pygame.Vector2
    monsters: list
    damage_monster: DamageFunction
    screen_rect: pygame.Rect
    width: int
    height: int

    @property
    def player_rect(self):
        return entity_rect(self.player)

    @property
    def direction(self):
        return normalized_direction(self.player_direction)


# =========================
# DICT-COMPATIBLE OBJECT BASE
# =========================
class DictCompatible:
    _fields: tuple[str, ...] = ()

    def __getitem__(self, key):
        if key in self._fields:
            return getattr(self, key)
        raise KeyError(key)

    def __setitem__(self, key, value):
        if key in self._fields:
            setattr(self, key, value)
            return
        raise KeyError(key)

    def get(self, key, default=None):
        return getattr(self, key, default) if key in self._fields else default

    def to_dict(self):
        return {key: getattr(self, key) for key in self._fields}


# =========================
# PROJECTILES / ACTIVE EFFECTS
# =========================
@dataclass
class BulletProjectile(DictCompatible):
    rect: pygame.Rect
    pos: pygame.Vector2
    dir: pygame.Vector2
    damage: int
    speed: int = 9

    _fields = ("rect", "pos", "dir", "damage", "speed")

    @classmethod
    def create(cls, player, player_direction, damage, size=10, speed=9):
        d = normalized_direction(player_direction)
        player_rect = entity_rect(player)
        rect = pygame.Rect(
            player_rect.centerx - size // 2,
            player_rect.centery - size // 2,
            size,
            size,
        )
        return cls(rect=rect, pos=pygame.Vector2(rect.x, rect.y), dir=d, damage=damage, speed=speed)

    def update(self, monsters, damage_monster, screen_rect):
        self.pos += self.dir * self.speed
        self.rect.x = int(self.pos.x)
        self.rect.y = int(self.pos.y)

        if not screen_rect.colliderect(self.rect):
            return False

        for monster in monsters:
            rect = entity_rect(monster)
            if monster_alive(monster) and self.rect.colliderect(rect):
                damage_monster(monster, self.damage)
                return False

        return True

    def draw(self, screen, show_hitbox=False):
        pygame.draw.rect(screen, ORANGE, self.rect)


@dataclass
class SpearProjectile(DictCompatible):
    rect: pygame.Rect
    pos: pygame.Vector2
    dir: pygame.Vector2
    damage: int
    speed: int
    size: int
    splash_damage: int
    splash_chance: int
    splash_range: int

    _fields = (
        "rect",
        "pos",
        "dir",
        "damage",
        "speed",
        "size",
        "splash_damage",
        "splash_chance",
        "splash_range",
    )

    @classmethod
    def create(cls, player, player_direction, weapon_data):
        d = normalized_direction(player_direction)
        player_rect = entity_rect(player)
        rect = pygame.Rect(
            player_rect.centerx - weapon_data["size"] // 2,
            player_rect.centery - weapon_data["size"] // 2,
            weapon_data["size"],
            weapon_data["size"],
        )
        return cls(
            rect=rect,
            pos=pygame.Vector2(rect.x, rect.y),
            dir=d,
            damage=weapon_data["damage"],
            speed=weapon_data["speed"],
            size=weapon_data["size"],
            splash_damage=weapon_data["splash_damage"],
            splash_chance=weapon_data["splash_chance"],
            splash_range=weapon_data["splash_range"],
        )

    def update(self, system, monsters, damage_monster, screen_rect):
        self.pos += self.dir * self.speed
        self.rect.x = int(self.pos.x)
        self.rect.y = int(self.pos.y)

        if not screen_rect.colliderect(self.rect):
            return False

        hit_monster = None
        for monster in monsters:
            rect = entity_rect(monster)
            if monster_alive(monster) and self.rect.colliderect(rect):
                hit_monster = monster
                break

        if hit_monster is None:
            return True

        hit_rect = entity_rect(hit_monster)
        hit_pos = pygame.Vector2(hit_rect.centerx, hit_rect.centery)
        damage_monster(hit_monster, self.damage)

        splash_roll = random.randint(1, 100)
        if splash_roll <= self.splash_chance:
            system.spear_splash = SpearSplashEffect(
                pos=hit_pos,
                timer=14,
                damage=self.splash_damage,
                radius=self.splash_range,
            )
            system.last_spear_splash = True
            system.last_spear_splash_damage = self.splash_damage
            system.last_spear_splash_range = self.splash_range

            for monster in monsters:
                if monster is hit_monster:
                    continue

                if monster_alive(monster) and rect_in_circle(entity_rect(monster), hit_pos, self.splash_range):
                    damage_monster(monster, self.splash_damage)
        else:
            system.last_spear_splash = False
            system.last_spear_splash_damage = 0

        return False

    def draw(self, screen, show_hitbox=False):
        draw_flying_spear(screen, self)


@dataclass
class BoomerangProjectile(DictCompatible):
    rect: pygame.Rect
    pos: pygame.Vector2
    dir: pygame.Vector2
    damage: int
    speed: int
    return_speed: int
    timer: int
    size: int
    returning: bool = False
    hit_targets: list = field(default_factory=list)

    _fields = (
        "rect",
        "pos",
        "dir",
        "damage",
        "speed",
        "return_speed",
        "timer",
        "size",
        "returning",
        "hit_targets",
    )

    @classmethod
    def create(cls, player, player_direction, weapon_data):
        d = normalized_direction(player_direction)
        player_rect = entity_rect(player)
        rect = pygame.Rect(
            player_rect.centerx - weapon_data["size"] // 2,
            player_rect.centery - weapon_data["size"] // 2,
            weapon_data["size"],
            weapon_data["size"],
        )
        return cls(
            rect=rect,
            pos=pygame.Vector2(rect.x, rect.y),
            dir=d,
            damage=weapon_data["damage"],
            speed=weapon_data["speed"],
            return_speed=weapon_data["return_speed"],
            timer=weapon_data["out_duration"],
            size=weapon_data["size"],
        )

    def update(self, player, monsters, damage_monster):
        if not self.returning:
            self.pos += self.dir * self.speed
            self.timer -= 1

            if self.timer <= 0:
                self.returning = True
                self.hit_targets.clear()
        else:
            target = player_center(player)
            current = self.pos
            d = target - current

            if d.length() < 20:
                return False

            if d.length() > 0:
                d = d.normalize()
                self.pos += d * self.return_speed

        self.rect.x = int(self.pos.x)
        self.rect.y = int(self.pos.y)

        for monster in monsters:
            rect = entity_rect(monster)
            if monster_alive(monster) and self.rect.colliderect(rect):
                if monster not in self.hit_targets:
                    damage_monster(monster, self.damage)
                    self.hit_targets.append(monster)

        return True

    def draw(self, screen, show_hitbox=False):
        pygame.draw.circle(
            screen,
            PURPLE,
            (int(self.rect.centerx), int(self.rect.centery)),
            self.size // 2,
            4,
        )


@dataclass
class ShockwaveEffect(DictCompatible):
    pos: pygame.Vector2
    current_radius: int
    max_radius: int
    expansion_speed: int
    damage: int
    knockback: int
    hit_targets: list = field(default_factory=list)

    _fields = (
        "pos",
        "current_radius",
        "max_radius",
        "expansion_speed",
        "damage",
        "knockback",
        "hit_targets",
    )

    @classmethod
    def create(cls, player, weapon_data):
        rect = entity_rect(player)
        return cls(
            pos=pygame.Vector2(rect.centerx, rect.centery),
            current_radius=10,
            max_radius=weapon_data["max_radius"],
            expansion_speed=weapon_data["expansion_speed"],
            damage=weapon_data["damage"],
            knockback=weapon_data["knockback"],
        )

    def update(self, monsters, damage_monster, screen_rect):
        self.current_radius += self.expansion_speed

        if self.current_radius >= self.max_radius:
            return False

        for monster in monsters:
            if monster_alive(monster) and monster not in self.hit_targets:
                rect = entity_rect(monster)
                if rect_in_circle(rect, self.pos, self.current_radius):
                    damage_monster(monster, self.damage)
                    self.hit_targets.append(monster)

                    m_center = pygame.Vector2(rect.centerx, rect.centery)
                    push_dir = m_center - self.pos

                    if push_dir.length() > 0:
                        push_dir = push_dir.normalize()
                        rect.x += int(push_dir.x * self.knockback)
                        rect.y += int(push_dir.y * self.knockback)
                        rect.clamp_ip(screen_rect)

        return True

    def draw(self, screen, show_hitbox=False):
        thickness = max(1, int(10 * (1 - self.current_radius / self.max_radius)))
        pygame.draw.circle(
            screen,
            BROWN,
            (int(self.pos.x), int(self.pos.y)),
            int(self.current_radius),
            thickness,
        )


@dataclass
class SpearSplashEffect:
    pos: pygame.Vector2
    timer: int
    damage: int
    radius: int

    def update(self):
        self.timer -= 1
        return self.timer > 0

    def draw(self, screen, show_hitbox=False):
        pygame.draw.circle(
            screen,
            SPEAR_SPLASH,
            (int(self.pos.x), int(self.pos.y)),
            self.radius,
            2,
        )

        if show_hitbox:
            pygame.draw.circle(
                screen,
                WHITE,
                (int(self.pos.x), int(self.pos.y)),
                self.radius,
                3,
            )


@dataclass
class SwordSlashEffect:
    start: pygame.Vector2
    end: pygame.Vector2
    width: int
    timer: int = 8

    def update(self):
        self.timer -= 1
        return self.timer > 0

    def draw(self, screen, show_hitbox=False):
        pygame.draw.line(
            screen,
            YELLOW,
            (int(self.start.x), int(self.start.y)),
            (int(self.end.x), int(self.end.y)),
            self.width,
        )
        pygame.draw.circle(screen, WHITE, (int(self.end.x), int(self.end.y)), 5)

        if show_hitbox:
            pygame.draw.line(
                screen,
                WHITE,
                (int(self.start.x), int(self.start.y)),
                (int(self.end.x), int(self.end.y)),
                2,
            )


@dataclass
class DashSlashEffect:
    start: pygame.Vector2
    end: pygame.Vector2
    width: int
    timer: int = 8

    def update(self):
        self.timer -= 1
        return self.timer > 0

    def draw(self, screen, show_hitbox=False):
        pygame.draw.line(
            screen,
            DUAL_SLASH,
            (int(self.start.x), int(self.start.y)),
            (int(self.end.x), int(self.end.y)),
            self.width,
        )
        pygame.draw.line(
            screen,
            WHITE,
            (int(self.start.x), int(self.start.y)),
            (int(self.end.x), int(self.end.y)),
            3,
        )

        if show_hitbox:
            pygame.draw.circle(screen, WHITE, (int(self.start.x), int(self.start.y)), self.width // 2, 2)
            pygame.draw.circle(screen, WHITE, (int(self.end.x), int(self.end.y)), self.width // 2, 2)


@dataclass
class FlagSwingEffect:
    direction: pygame.Vector2
    side: int
    duration: int = 12
    timer: int = 12
    has_hit_enemy: bool = False
    polygon: list = field(default_factory=list)

    def update_timer(self):
        self.timer -= 1
        return self.timer > 0

    def set_direction(self, direction):
        if direction.length() > 0:
            self.direction = pygame.Vector2(direction.x, direction.y)

    def angle(self):
        progress = 1 - self.timer / self.duration
        start_angle = -45 * self.side
        end_angle = 45 * self.side
        return start_angle + (end_angle - start_angle) * progress

    def build_polygon(self, player):
        d = pygame.Vector2(self.direction.x, self.direction.y)
        if d.length() == 0:
            d = pygame.Vector2(0, 1)
        d = d.normalize()

        center = player_center(player)
        start_angle = -45 * self.side
        current_angle = self.angle()

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

        self.polygon = outer_points + inner_points[::-1]
        return self.polygon

    def update_hitbox(self, player, monsters, damage_monster, damage):
        self.build_polygon(player)

        if self.has_hit_enemy:
            return

        for monster in monsters:
            rect = entity_rect(monster)
            if monster_alive(monster) and rect_hits_polygon(rect, self.polygon):
                damage_monster(monster, damage)
                self.has_hit_enemy = True
                break

    def draw_fan(self, screen, player):
        polygon = self.build_polygon(player)
        if len(polygon) < 3:
            return
        pygame.draw.polygon(screen, FLAG_DARK, polygon)
        pygame.draw.lines(screen, FLAG_LIGHT, True, polygon, 3)

    def draw_hitbox(self, screen):
        if len(self.polygon) >= 3:
            pygame.draw.lines(screen, WHITE, True, self.polygon, 3)


# =========================
# WEAPON CLASSES
# =========================
class BaseWeapon:
    def __init__(self, data):
        self.data = data

    @property
    def name(self):
        return self.data["name"]

    @property
    def color(self):
        return self.data["color"]

    @property
    def cooldown(self):
        return self.data["cooldown"]

    @property
    def weapon_type(self):
        return self.data.get("type", "")

    @property
    def energy_cost(self):
        """Energy is ammo, so only ranged-style weapons spend it."""
        if "energy_cost" in self.data:
            return self.data["energy_cost"]
        if self.weapon_type in ENERGY_AMMO_WEAPON_TYPES:
            return DEFAULT_RANGED_ENERGY_COST
        return 0

    def try_spend_energy(self, context: WeaponUseContext) -> bool:
        cost = self.energy_cost
        if cost <= 0:
            return True

        spend_energy = getattr(context.player, "spend_energy", None)
        if callable(spend_energy):
            return bool(spend_energy(cost))

        if getattr(context.player, "energy", 0) < cost:
            return False
        context.player.energy -= cost
        return True

    def damage_text(self):
        return damage_text_for_data(self.data)

    def use(self, system, context: WeaponUseContext):
        raise NotImplementedError

    def draw_icon(self, system, screen, player, player_direction):
        pass


class SwordWeapon(BaseWeapon):
    def use(self, system, context):
        if system.attack_cooldown_timer > 0:
            return

        d = context.direction
        start = player_center(context.player)
        end = start + d * self.data["range"]
        width = self.data["size"]

        for monster in context.monsters:
            if monster_alive(monster) and rect_hits_line(entity_rect(monster), start, end, width):
                context.damage_monster(monster, self.data["damage"])

        system.sword_slash = SwordSlashEffect(start=start, end=end, width=width, timer=8)
        system.attack_cooldown_timer = self.cooldown

    def draw_icon(self, system, screen, player, player_direction):
        rect = entity_rect(player)
        d = normalized_direction(player_direction)
        end = (rect.centerx + int(d.x * 35), rect.centery + int(d.y * 35))
        pygame.draw.line(screen, YELLOW, rect.center, end, 5)


class GunWeapon(BaseWeapon):
    def use(self, system, context):
        if system.shoot_timer <= 0:
            if not self.try_spend_energy(context):
                return
            system.bullets.append(BulletProjectile.create(
                context.player,
                context.player_direction,
                damage=self.data["damage"],
                size=self.data["size"],
                speed=system.bullet_speed,
            ))
            system.shoot_timer = self.cooldown

    def draw_icon(self, system, screen, player, player_direction):
        rect = entity_rect(player)
        pygame.draw.rect(screen, ORANGE, (rect.centerx - 8, rect.centery - 8, 16, 16))


class FlagWeapon(BaseWeapon):
    def use(self, system, context):
        if system.attack_cooldown_timer > 0:
            return

        system.flag_side *= -1
        system.flag_swing = FlagSwingEffect(
            direction=pygame.Vector2(context.player_direction.x, context.player_direction.y),
            side=system.flag_side,
            duration=system.flag_duration,
            timer=system.flag_duration,
        )
        system.flag_swing.build_polygon(context.player)
        system.attack_cooldown_timer = self.cooldown

    def draw_icon(self, system, screen, player, player_direction):
        draw_flag(screen, player, player_direction)


class SpearWeapon(BaseWeapon):
    def use(self, system, context):
        if system.attack_cooldown_timer <= 0:
            if not self.try_spend_energy(context):
                return
            system.spears.append(SpearProjectile.create(context.player, context.player_direction, self.data))
            system.attack_cooldown_timer = self.cooldown

    def draw_icon(self, system, screen, player, player_direction):
        draw_spear_in_hand(screen, player, player_direction)


class DualBladesWeapon(BaseWeapon):
    def use(self, system, context):
        if system.attack_cooldown_timer > 0:
            return

        player_rect = context.player_rect
        d = context.direction
        start = pygame.Vector2(player_rect.centerx, player_rect.centery)
        target_pos = start + d * self.data["dash_distance"]

        target_x = max(player_rect.width // 2, min(context.width - player_rect.width // 2, target_pos.x))
        target_y = max(player_rect.height // 2, min(context.height - player_rect.height // 2, target_pos.y))
        end = pygame.Vector2(target_x, target_y)

        player_rect.centerx = int(end.x)
        player_rect.centery = int(end.y)
        player_rect.clamp_ip(context.screen_rect)

        width = self.data["slash_width"]
        for monster in context.monsters:
            if monster_alive(monster) and rect_hits_line(entity_rect(monster), start, end, width):
                context.damage_monster(monster, self.data["damage"])

        system.dash_slash = DashSlashEffect(start=start, end=end, width=width, timer=system.dash_slash_duration)
        system.attack_cooldown_timer = self.cooldown

    def draw_icon(self, system, screen, player, player_direction):
        draw_dual_blades_in_hand(screen, player, player_direction)


class BoomerangWeapon(BaseWeapon):
    def use(self, system, context):
        if system.attack_cooldown_timer <= 0:
            if not self.try_spend_energy(context):
                return
            system.boomerangs.append(BoomerangProjectile.create(context.player, context.player_direction, self.data))
            system.attack_cooldown_timer = self.cooldown

    def draw_icon(self, system, screen, player, player_direction):
        rect = entity_rect(player)
        d = normalized_direction(player_direction)
        pygame.draw.circle(
            screen,
            PURPLE,
            (rect.centerx + int(d.x * 20), rect.centery + int(d.y * 20)),
            8,
            3,
        )


class EarthshakerWeapon(BaseWeapon):
    def use(self, system, context):
        if system.attack_cooldown_timer <= 0:
            system.shockwaves.append(ShockwaveEffect.create(context.player, self.data))
            system.attack_cooldown_timer = self.cooldown

    def draw_icon(self, system, screen, player, player_direction):
        rect = entity_rect(player)
        d = normalized_direction(player_direction)
        head_center = (rect.centerx + int(d.x * 25), rect.centery + int(d.y * 25))
        pygame.draw.line(screen, BROWN, rect.center, head_center, 4)
        pygame.draw.rect(screen, GRAY, (head_center[0] - 10, head_center[1] - 10, 20, 20))


# =========================
# WEAPON SYSTEM
# =========================
class WeaponSystem:
    def __init__(self):
        self.weapon_objects = [self._make_weapon(data) for data in WEAPON_DATA]
        self.weapons = [weapon.data for weapon in self.weapon_objects]

        self.current_weapon = 0
        self.selected_weapon = 0
        self.weapon_list_open = False

        self.bullets = []
        self.bullet_speed = 9
        self.bullet_size = 10
        self.shoot_timer = 0

        self.spears = []
        self.spear_splash = None
        self.last_spear_splash = False
        self.last_spear_splash_damage = 0
        self.last_spear_splash_range = 162

        self.boomerangs = []
        self.shockwaves = []

        self.attack_cooldown_timer = 0
        self.sword_slash = None

        self.dash_slash = None
        self.dash_slash_duration = 8

        self.flag_swing = None
        self.flag_duration = 12
        self.flag_side = 1
        self.flag_wave = 0
        self.flag_attack_direction = pygame.Vector2(0, 1)

    def _make_weapon(self, data):
        name = data["name"]
        if name == "Sword":
            return SwordWeapon(data)
        if name == "Gun":
            return GunWeapon(data)
        if name == "Flag":
            return FlagWeapon(data)
        if name == "Spear":
            return SpearWeapon(data)
        if name == "Dual Blades":
            return DualBladesWeapon(data)
        if name == "Boomerang":
            return BoomerangWeapon(data)
        if name == "Earthshaker":
            return EarthshakerWeapon(data)
        return BaseWeapon(data)

    @property
    def current(self):
        return self.weapon_objects[self.current_weapon]

    def current_data(self):
        return self.current.data

    def equip(self, index):
        if not self.weapon_objects:
            return
        self.current_weapon = index % len(self.weapon_objects)
        self.selected_weapon = self.current_weapon

    def set_flag_direction(self, direction):
        if self.flag_swing is not None and direction.length() > 0:
            self.flag_swing.set_direction(direction)
            self.flag_attack_direction = pygame.Vector2(direction.x, direction.y)

    def use_weapon(self, player, player_direction, monsters, damage_monster, screen_rect, width, height):
        context = WeaponUseContext(
            player=player,
            player_direction=player_direction,
            monsters=monsters,
            damage_monster=damage_monster,
            screen_rect=screen_rect,
            width=width,
            height=height,
        )
        self.current.use(self, context)

    def update(self, player, player_direction, monsters, damage_monster, screen_rect):
        self.flag_wave += 1

        if self.sword_slash is not None and not self.sword_slash.update():
            self.sword_slash = None

        if self.dash_slash is not None and not self.dash_slash.update():
            self.dash_slash = None

        if self.flag_swing is not None:
            # Preserve the original timing: flag_timer is decremented before
            # the hitbox is rebuilt and tested.
            if not self.flag_swing.update_timer():
                self.flag_swing = None
            elif self.current.name == "Flag":
                self.flag_swing.update_hitbox(player, monsters, damage_monster, self.current.data["damage"])
                self.flag_attack_direction = pygame.Vector2(
                    self.flag_swing.direction.x,
                    self.flag_swing.direction.y,
                )

        if self.shoot_timer > 0:
            self.shoot_timer -= 1

        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= 1

        if self.spear_splash is not None and not self.spear_splash.update():
            self.spear_splash = None

        self.bullets = [
            bullet for bullet in self.bullets
            if bullet.update(monsters, damage_monster, screen_rect)
        ]

        self.spears = [
            spear for spear in self.spears
            if spear.update(self, monsters, damage_monster, screen_rect)
        ]

        self.boomerangs = [
            b for b in self.boomerangs
            if b.update(player, monsters, damage_monster)
        ]

        self.shockwaves = [
            wave for wave in self.shockwaves
            if wave.update(monsters, damage_monster, screen_rect)
        ]

    def draw_weapon_icon(self, screen, player, player_direction):
        self.current.draw_icon(self, screen, player, player_direction)

    def draw_attacks(self, screen, show_hitbox):
        if self.dash_slash is not None:
            self.dash_slash.draw(screen, show_hitbox)
            return

        if self.flag_swing is not None and self.current.name == "Flag":
            if show_hitbox:
                self.flag_swing.draw_hitbox(screen)
            return

        if self.sword_slash is not None and self.current.name == "Sword":
            self.sword_slash.draw(screen, show_hitbox)

    def draw_projectiles(self, screen, show_hitbox):
        for bullet in self.bullets:
            bullet.draw(screen, show_hitbox)

        for spear in self.spears:
            spear.draw(screen, show_hitbox)

        for b in self.boomerangs:
            b.draw(screen, show_hitbox)

        for wave in self.shockwaves:
            wave.draw(screen, show_hitbox)

        if self.spear_splash is not None:
            self.spear_splash.draw(screen, show_hitbox)

    def draw_weapon_list(self, screen, font, small_font, width, height):
        x = width // 2 - 260
        y = height // 2 - 250

        pygame.draw.rect(screen, DARK_GRAY, (x, y, 520, 520))
        pygame.draw.rect(screen, WHITE, (x, y, 520, 520), 3)

        title = font.render("WEAPON LIST", True, WHITE)
        guide = small_font.render("I: Close | UP/DOWN: Select | ENTER: Equip", True, LIGHT_GRAY)

        screen.blit(title, (x + 185, y + 20))
        screen.blit(guide, (x + 65, y + 55))

        for i, w in enumerate(self.weapons):
            rect = pygame.Rect(x + 40, y + 90 + i * 55, 440, 48)

            if i == self.selected_weapon:
                pygame.draw.rect(screen, GRAY, rect)
                pygame.draw.rect(screen, WHITE, rect, 2)
            else:
                pygame.draw.rect(screen, (65, 65, 65), rect)

            text = w["name"]
            if i == self.current_weapon:
                text += " [EQUIPPED]"

            name_text = font.render(text, True, w["color"])
            info_text = small_font.render(
                "Type: " + w["type"] + " | Damage: " + get_weapon_damage_text(w),
                True,
                WHITE,
            )

            screen.blit(name_text, (rect.x + 20, rect.y + 6))
            screen.blit(info_text, (rect.x + 20, rect.y + 28))

    def draw_fan(self, screen, player):
        if self.flag_swing is not None:
            self.flag_swing.draw_fan(screen, player)

    def projectile_count(self):
        return len(self.bullets) + len(self.spears) + len(self.boomerangs) + len(self.shockwaves)


# =========================
# DRAW HELPERS
# =========================
def _active_system():
    return _default_system


def get_flag_angle():
    system = _active_system()
    if system.flag_swing is None:
        return 0
    return system.flag_swing.angle()


def build_flag_attack_polygon(player):
    system = _active_system()
    if system.flag_swing is None:
        return []
    return system.flag_swing.build_polygon(player)


def update_flag_hitbox(player, monsters, damage_monster):
    system = _active_system()
    if system.flag_swing is None:
        system.flag_attack_direction = pygame.Vector2(0, 1)
        return
    if system.current.name != "Flag":
        return
    system.flag_swing.update_hitbox(player, monsters, damage_monster, system.current.data["damage"])


def draw_flag_cloth(screen, px, py, direction):
    system = _active_system()
    d = normalized_direction(direction)
    side = pygame.Vector2(-d.y, d.x)

    length = 54
    height = 34
    power = 5
    segments = 8

    top = []
    bottom = []

    for i in range(segments + 1):
        t = i / segments
        wave = math.sin(system.flag_wave * 0.22 + t * math.pi * 2.2) * power * t

        cx = px + side.x * length * t + d.x * wave
        cy = py + side.y * length * t + d.y * wave
        h = height * (1 - t * 0.08) / 2

        top.append((int(cx - d.x * h), int(cy - d.y * h)))
        bottom.append((int(cx + d.x * h), int(cy + d.y * h)))

    points = top + bottom[::-1]
    pygame.draw.polygon(screen, FLAG_RED, points)
    pygame.draw.lines(screen, WHITE, True, points, 2)


def draw_flag(screen, player, player_direction):
    system = _active_system()
    rect = entity_rect(player)

    if system.flag_swing is not None:
        d = pygame.Vector2(system.flag_swing.direction.x, system.flag_swing.direction.y)
    else:
        d = pygame.Vector2(player_direction.x, player_direction.y)

    d = normalized_direction(d)

    if system.flag_swing is not None:
        d = rotate(d, math.radians(system.flag_swing.angle()))

    end = pygame.Vector2(rect.centerx, rect.centery) + d * 52

    pygame.draw.line(screen, BROWN, rect.center, (int(end.x), int(end.y)), 6)
    pygame.draw.circle(screen, LIGHT_GRAY, (int(end.x), int(end.y)), 7)
    draw_flag_cloth(screen, end.x, end.y, d)


def draw_fan(screen, player):
    _active_system().draw_fan(screen, player)


def draw_spear_in_hand(screen, player, player_direction):
    rect = entity_rect(player)
    d = normalized_direction(player_direction)

    start = pygame.Vector2(rect.centerx, rect.centery)
    end = start + d * 45

    pygame.draw.line(
        screen,
        SPEAR_COLOR,
        (int(start.x), int(start.y)),
        (int(end.x), int(end.y)),
        5,
    )

    left = rotate(d, math.radians(150)) * 13
    right = rotate(d, math.radians(-150)) * 13

    pygame.draw.polygon(
        screen,
        SPEAR_TIP,
        [
            (int(end.x), int(end.y)),
            (int(end.x + left.x), int(end.y + left.y)),
            (int(end.x + right.x), int(end.y + right.y)),
        ],
    )


def draw_flying_spear(screen, spear):
    d = spear["dir"] if isinstance(spear, DictCompatible) else spear["dir"]
    rect = spear["rect"] if isinstance(spear, DictCompatible) else spear["rect"]
    center = pygame.Vector2(rect.centerx, rect.centery)

    start = center - d * 18
    end = center + d * 22

    pygame.draw.line(
        screen,
        SPEAR_COLOR,
        (int(start.x), int(start.y)),
        (int(end.x), int(end.y)),
        5,
    )

    left = rotate(d, math.radians(150)) * 12
    right = rotate(d, math.radians(-150)) * 12

    pygame.draw.polygon(
        screen,
        SPEAR_TIP,
        [
            (int(end.x), int(end.y)),
            (int(end.x + left.x), int(end.y + left.y)),
            (int(end.x + right.x), int(end.y + right.y)),
        ],
    )


def draw_dual_blades_in_hand(screen, player, player_direction):
    rect = entity_rect(player)
    d = normalized_direction(player_direction)

    side = pygame.Vector2(-d.y, d.x)
    center = pygame.Vector2(rect.centerx, rect.centery)

    long_start = center + side * 8
    long_end = long_start + d * 48

    short_start = center - side * 9
    short_end = short_start + d * 32

    pygame.draw.line(
        screen,
        DUAL_LONG,
        (int(long_start.x), int(long_start.y)),
        (int(long_end.x), int(long_end.y)),
        5,
    )

    pygame.draw.line(
        screen,
        DUAL_SHORT,
        (int(short_start.x), int(short_start.y)),
        (int(short_end.x), int(short_end.y)),
        5,
    )

    pygame.draw.circle(screen, WHITE, (int(long_start.x), int(long_start.y)), 4)
    pygame.draw.circle(screen, WHITE, (int(short_start.x), int(short_start.y)), 4)


# =========================
# LEGACY-COMPATIBLE DEFAULT SYSTEM
# =========================
_default_system = WeaponSystem()

# These module globals are preserved because main.py reads or writes them.
weapons = _default_system.weapons
current_weapon = _default_system.current_weapon
selected_weapon = _default_system.selected_weapon
weapon_list_open = _default_system.weapon_list_open

bullets = _default_system.bullets
bullet_speed = _default_system.bullet_speed
bullet_size = _default_system.bullet_size
shoot_timer = _default_system.shoot_timer

spears = _default_system.spears
spear_splash_timer = 0
spear_splash_pos = None
last_spear_splash = _default_system.last_spear_splash
last_spear_splash_damage = _default_system.last_spear_splash_damage
last_spear_splash_range = _default_system.last_spear_splash_range

boomerangs = _default_system.boomerangs
shockwaves = _default_system.shockwaves

attacking = False
attack_timer = 0
attack_rect = pygame.Rect(0, 0, 0, 0)
attack_cooldown_timer = _default_system.attack_cooldown_timer

sword_attack_start = pygame.Vector2(0, 0)
sword_attack_end = pygame.Vector2(0, 0)
sword_attack_width = 16

dash_slashing = False
dash_slash_timer = 0
dash_slash_duration = _default_system.dash_slash_duration
dash_start_pos = pygame.Vector2(0, 0)
dash_end_pos = pygame.Vector2(0, 0)
dash_slash_width = 42

flag_swinging = False
flag_timer = 0
flag_duration = _default_system.flag_duration
flag_side = _default_system.flag_side
flag_wave = _default_system.flag_wave
flag_attack_direction = _default_system.flag_attack_direction
flag_has_hit_enemy = False
flag_attack_polygon = []


def _sync_system_from_exports():
    _default_system.current_weapon = current_weapon % len(_default_system.weapon_objects)
    _default_system.selected_weapon = selected_weapon % len(_default_system.weapon_objects)
    _default_system.weapon_list_open = weapon_list_open
    _default_system.bullet_speed = bullet_speed
    _default_system.bullet_size = bullet_size
    _default_system.shoot_timer = shoot_timer
    _default_system.attack_cooldown_timer = attack_cooldown_timer
    _default_system.dash_slash_duration = dash_slash_duration
    _default_system.flag_duration = flag_duration
    _default_system.flag_side = flag_side


def _sync_exports_from_system():
    global weapons, current_weapon, selected_weapon, weapon_list_open
    global bullets, bullet_speed, bullet_size, shoot_timer
    global spears, spear_splash_timer, spear_splash_pos
    global last_spear_splash, last_spear_splash_damage, last_spear_splash_range
    global boomerangs, shockwaves
    global attacking, attack_timer, attack_cooldown_timer
    global sword_attack_start, sword_attack_end, sword_attack_width
    global dash_slashing, dash_slash_timer, dash_start_pos, dash_end_pos, dash_slash_width
    global flag_swinging, flag_timer, flag_side, flag_wave, flag_attack_direction
    global flag_has_hit_enemy, flag_attack_polygon

    weapons = _default_system.weapons
    current_weapon = _default_system.current_weapon
    selected_weapon = _default_system.selected_weapon
    weapon_list_open = _default_system.weapon_list_open

    bullets = _default_system.bullets
    bullet_speed = _default_system.bullet_speed
    bullet_size = _default_system.bullet_size
    shoot_timer = _default_system.shoot_timer

    spears = _default_system.spears
    boomerangs = _default_system.boomerangs
    shockwaves = _default_system.shockwaves

    if _default_system.spear_splash is not None:
        spear_splash_timer = _default_system.spear_splash.timer
        spear_splash_pos = _default_system.spear_splash.pos
    else:
        spear_splash_timer = 0
        spear_splash_pos = None

    last_spear_splash = _default_system.last_spear_splash
    last_spear_splash_damage = _default_system.last_spear_splash_damage
    last_spear_splash_range = _default_system.last_spear_splash_range

    attack_cooldown_timer = _default_system.attack_cooldown_timer

    if _default_system.sword_slash is not None:
        sword_attack_start = _default_system.sword_slash.start
        sword_attack_end = _default_system.sword_slash.end
        sword_attack_width = _default_system.sword_slash.width
    else:
        sword_attack_start = pygame.Vector2(0, 0)
        sword_attack_end = pygame.Vector2(0, 0)
        sword_attack_width = 16

    if _default_system.dash_slash is not None:
        dash_slashing = True
        dash_slash_timer = _default_system.dash_slash.timer
        dash_start_pos = _default_system.dash_slash.start
        dash_end_pos = _default_system.dash_slash.end
        dash_slash_width = _default_system.dash_slash.width
    else:
        dash_slashing = False
        dash_slash_timer = 0
        dash_start_pos = pygame.Vector2(0, 0)
        dash_end_pos = pygame.Vector2(0, 0)
        dash_slash_width = 42

    if _default_system.flag_swing is not None:
        flag_swinging = True
        flag_timer = _default_system.flag_swing.timer
        flag_side = _default_system.flag_swing.side
        flag_attack_direction = _default_system.flag_swing.direction
        flag_has_hit_enemy = _default_system.flag_swing.has_hit_enemy
        flag_attack_polygon = _default_system.flag_swing.polygon
    else:
        flag_swinging = False
        flag_timer = 0
        flag_attack_direction = _default_system.flag_attack_direction
        flag_has_hit_enemy = False
        flag_attack_polygon = []

    flag_wave = _default_system.flag_wave
    attacking = _default_system.sword_slash is not None or _default_system.dash_slash is not None or _default_system.flag_swing is not None
    if _default_system.sword_slash is not None:
        attack_timer = _default_system.sword_slash.timer
    elif _default_system.dash_slash is not None:
        attack_timer = _default_system.dash_slash.timer
    elif _default_system.flag_swing is not None:
        attack_timer = _default_system.flag_swing.timer
    else:
        attack_timer = 0


# =========================
# LEGACY API
# =========================
def weapon():
    _sync_system_from_exports()
    _sync_exports_from_system()
    return _default_system.current_data()


def equip(index):
    _sync_system_from_exports()
    _default_system.equip(index)
    _sync_exports_from_system()


def set_flag_direction(direction):
    _sync_system_from_exports()
    _default_system.set_flag_direction(direction)
    _sync_exports_from_system()


def make_bullet(player, player_direction):
    _sync_system_from_exports()
    return BulletProjectile.create(player, player_direction, weapon()["damage"], size=bullet_size, speed=bullet_speed)


def make_spear(player, player_direction):
    _sync_system_from_exports()
    return SpearProjectile.create(player, player_direction, weapon())


def make_boomerang(player, player_direction):
    _sync_system_from_exports()
    return BoomerangProjectile.create(player, player_direction, weapon())


def use_weapon(player, player_direction, monsters, damage_monster, screen_rect, width, height):
    _sync_system_from_exports()
    _default_system.use_weapon(player, player_direction, monsters, damage_monster, screen_rect, width, height)
    _sync_exports_from_system()


def update(player, player_direction, monsters, damage_monster, screen_rect):
    _sync_system_from_exports()
    _default_system.update(player, player_direction, monsters, damage_monster, screen_rect)
    _sync_exports_from_system()


def draw_weapon_icon(screen, player, player_direction):
    _sync_system_from_exports()
    _default_system.draw_weapon_icon(screen, player, player_direction)
    _sync_exports_from_system()


def draw_attacks(screen, show_hitbox):
    _sync_system_from_exports()
    _default_system.draw_attacks(screen, show_hitbox)
    _sync_exports_from_system()


def draw_projectiles(screen, show_hitbox):
    _sync_system_from_exports()
    _default_system.draw_projectiles(screen, show_hitbox)
    _sync_exports_from_system()


def draw_weapon_list(screen, font, small_font, width, height):
    _sync_system_from_exports()
    _default_system.draw_weapon_list(screen, font, small_font, width, height)
    _sync_exports_from_system()


def projectile_count():
    _sync_system_from_exports()
    count = _default_system.projectile_count()
    _sync_exports_from_system()
    return count


# Initialize exported globals from the default system.
_sync_exports_from_system()
