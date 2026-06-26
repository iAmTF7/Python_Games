"""Weapon projectiles, effects, concrete weapons, and weapon system."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random

import pygame

from .constants import *
from .physics import *
from .rendering import (
    draw_dual_blades_in_hand,
    draw_flag,
    draw_spear_in_hand,
    draw_flying_spear,
)


@dataclass
class WeaponUseContext:
    player: object
    player_direction: pygame.Vector2
    monsters: list
    damage_monster: DamageFunction
    screen_rect: pygame.Rect
    width: int
    height: int
    tile_map: object | None = None

    @property
    def player_rect(self):
        return entity_rect(self.player)

    @property
    def direction(self):
        return normalized_direction(self.player_direction)


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


def damage_monsters_on_line(context, start, end, width, damage):
    for monster in context.monsters:
        monster_rect = entity_rect(monster)

        if not monster_alive(monster):
            continue

        if not rect_hits_line(monster_rect, start, end, width):
            continue

        monster_center = pygame.Vector2(monster_rect.centerx, monster_rect.centery)

        if line_blocked_by_wall(context.tile_map, start, monster_center):
            continue

        context.damage_monster(monster, damage)


def clip_line_end_for_melee_visual(tile_map, start, end, step=4):
    if tile_map is None:
        return end

    start = pygame.Vector2(start)
    end = pygame.Vector2(end)

    direction = end - start
    distance = direction.length()

    if distance <= 0:
        return end

    direction = direction.normalize()
    last_safe = pygame.Vector2(start.x, start.y)

    is_walkable = getattr(tile_map, "is_pixel_rect_walkable", None)

    if callable(is_walkable):
        steps = max(1, int(distance // step))

        for i in range(1, steps + 1):
            point = start + direction * step * i

            test_rect = pygame.Rect(
                int(point.x) - 3,
                int(point.y) - 3,
                6,
                6,
            )

            if not is_walkable(test_rect, include_exit=True):
                return last_safe

            last_safe = pygame.Vector2(point.x, point.y)

        return end

    iter_wall_rects = getattr(tile_map, "iter_wall_rects_between", None)

    if callable(iter_wall_rects):
        line_start = (int(start.x), int(start.y))
        line_end = (int(end.x), int(end.y))

        nearest_distance = None
        nearest_point = None

        for wall_rect in iter_wall_rects(line_start, line_end):
            clipped = wall_rect.clipline(line_start, line_end)

            if not clipped:
                continue

            hit_point = pygame.Vector2(clipped[0])
            hit_distance = start.distance_to(hit_point)

            if nearest_distance is None or hit_distance < nearest_distance:
                nearest_distance = hit_distance
                nearest_point = hit_point

        if nearest_point is not None:
            return start + direction * max(0, nearest_distance - 4)

    return end


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

        return cls(
            rect=rect,
            pos=pygame.Vector2(rect.x, rect.y),
            dir=d,
            damage=damage,
            speed=speed,
        )

    def update(self, monsters, damage_monster, screen_rect, tile_map=None):
        previous_center = self.rect.center

        self.pos += self.dir * self.speed
        self.rect.x = int(self.pos.x)
        self.rect.y = int(self.pos.y)

        if not screen_rect.colliderect(self.rect):
            return False

        if projectile_blocked_by_wall(tile_map, self.rect, previous_center):
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

    def update(self, system, monsters, damage_monster, screen_rect, tile_map=None):
        previous_center = self.rect.center

        self.pos += self.dir * self.speed
        self.rect.x = int(self.pos.x)
        self.rect.y = int(self.pos.y)

        if not screen_rect.colliderect(self.rect):
            return False

        if projectile_blocked_by_wall(tile_map, self.rect, previous_center):
            system.last_spear_splash = False
            system.last_spear_splash_damage = 0
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

    def update(self, player, monsters, damage_monster, screen_rect=None, tile_map=None):
        previous_center = self.rect.center
        previous_pos = pygame.Vector2(self.pos.x, self.pos.y)
        previous_rect = self.rect.copy()
        was_returning = self.returning

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

        if screen_rect is not None and not screen_rect.colliderect(self.rect):
            return False

        if projectile_blocked_by_wall(tile_map, self.rect, previous_center):
            self.pos = previous_pos
            self.rect = previous_rect

            if was_returning:
                return False

            self.returning = True
            self.timer = 0
            self.hit_targets.clear()
            return True

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
    tile_map: object | None = None

    def update_timer(self):
        self.timer -= 1
        return self.timer > 0

    def set_direction(self, direction):
        if direction.length() > 0:
            self.direction = pygame.Vector2(direction.x, direction.y)

    def progress(self):
        if self.duration <= 0:
            return 1

        return max(0, min(1, 1 - self.timer / self.duration))

    def attack_direction(self):
        d = pygame.Vector2(self.direction.x, self.direction.y)

        if d.length() == 0:
            d = pygame.Vector2(0, 1)

        return d.normalize()

    def fan_params(self):
        return {
            "inner": 22,
            "outer": 95,
            "half_arc": 45,
            "steps": 18,
        }

    def sweep_angles(self):
        params = self.fan_params()
        half_arc = params["half_arc"]

        start_angle = -half_arc * self.side
        end_angle = half_arc * self.side

        progress = self.progress()
        current_angle = start_angle + (end_angle - start_angle) * progress

        return start_angle, current_angle, end_angle

    def angle(self):
        _, current_angle, _ = self.sweep_angles()
        return current_angle

    def blocked_immediately_by_wall(self, player, tile_map=None):
        active_tile_map = tile_map if tile_map is not None else self.tile_map

        if active_tile_map is None:
            return False

        center = player_center(player)
        d = self.attack_direction()
        check_end = center + d * 28

        return line_blocked_by_wall(active_tile_map, center, check_end)

    def clipped_point(self, tile_map, center, direction, distance):
        raw_point = center + direction * distance
        return clip_line_end_for_melee_visual(tile_map, center, raw_point)

    def build_polygon(self, player, tile_map=None):
        active_tile_map = tile_map if tile_map is not None else self.tile_map

        if self.blocked_immediately_by_wall(player, active_tile_map):
            self.polygon = []
            return self.polygon

        center = player_center(player)
        base = self.attack_direction()

        params = self.fan_params()
        inner = params["inner"]
        outer = params["outer"]
        steps = params["steps"]

        start_angle, current_angle, _ = self.sweep_angles()

        if abs(current_angle - start_angle) < 2:
            current_angle = start_angle + 2 * self.side

        outer_points = []
        inner_points = []

        for i in range(steps + 1):
            t = i / steps
            angle = start_angle + (current_angle - start_angle) * t
            rotated = rotate(base, math.radians(angle))

            outer_point = self.clipped_point(active_tile_map, center, rotated, outer)

            if center.distance_to(outer_point) <= inner:
                inner_point = outer_point
            else:
                inner_point = center + rotated * inner

            outer_points.append((int(outer_point.x), int(outer_point.y)))
            inner_points.append((int(inner_point.x), int(inner_point.y)))

        self.polygon = outer_points + inner_points[::-1]
        return self.polygon

    def update_hitbox(self, player, monsters, damage_monster, damage, tile_map=None):
        self.build_polygon(player, tile_map)

        if self.has_hit_enemy:
            return

        if len(self.polygon) < 3:
            return

        start = player_center(player)

        for monster in monsters:
            rect = entity_rect(monster)
            monster_center = pygame.Vector2(rect.centerx, rect.centery)

            if monster_alive(monster) and rect_hits_polygon(rect, self.polygon):
                if line_blocked_by_wall(tile_map, start, monster_center):
                    continue

                damage_monster(monster, damage)
                self.has_hit_enemy = True
                break

    def draw_fan(self, screen, player):
        polygon = self.build_polygon(player)

        if len(polygon) < 3:
            return

        pygame.draw.polygon(screen, FLAG_DARK, polygon)
        pygame.draw.lines(screen, FLAG_LIGHT, True, polygon, 3)

        center = player_center(player)
        base = self.attack_direction()

        params = self.fan_params()
        inner = params["inner"]
        outer = params["outer"]

        _, current_angle, _ = self.sweep_angles()

        sweep_dir = rotate(base, math.radians(current_angle))

        if sweep_dir.length() == 0:
            sweep_dir = pygame.Vector2(0, 1)

        sweep_dir = sweep_dir.normalize()

        p2 = self.clipped_point(self.tile_map, center, sweep_dir, outer)

        if center.distance_to(p2) <= inner:
            p1 = p2
        else:
            p1 = center + sweep_dir * inner

        pygame.draw.line(
            screen,
            WHITE,
            (int(p1.x), int(p1.y)),
            (int(p2.x), int(p2.y)),
            4,
        )

    def draw_hitbox(self, screen):
        if len(self.polygon) >= 3:
            pygame.draw.lines(screen, WHITE, True, self.polygon, 3)


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

        raw_end = start + d * self.data["range"]
        end = clip_line_end_for_melee_visual(context.tile_map, start, raw_end)

        width = self.data["size"]

        damage_monsters_on_line(context, start, end, width, self.data["damage"])

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

            system.bullets.append(
                BulletProjectile.create(
                    context.player,
                    context.player_direction,
                    damage=self.data["damage"],
                    size=self.data["size"],
                    speed=system.bullet_speed,
                )
            )

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
            direction=pygame.Vector2(
                context.player_direction.x,
                context.player_direction.y,
            ),
            side=system.flag_side,
            duration=system.flag_duration,
            timer=system.flag_duration,
            tile_map=context.tile_map,
        )

        system.flag_swing.build_polygon(context.player, context.tile_map)
        system.attack_cooldown_timer = self.cooldown

    def draw_icon(self, system, screen, player, player_direction):
         draw_flag(screen, player, player_direction, system)

class SpearWeapon(BaseWeapon):
    def use(self, system, context):
        if system.attack_cooldown_timer <= 0:
            if not self.try_spend_energy(context):
                return

            system.spears.append(
                SpearProjectile.create(context.player, context.player_direction, self.data)
            )

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

        end = find_walkable_dash_end(
            player_rect,
            start,
            target_pos,
            context.screen_rect,
            context.tile_map,
        )

        player_rect.center = (int(end.x), int(end.y))
        player_rect.clamp_ip(context.screen_rect)

        end = pygame.Vector2(player_rect.centerx, player_rect.centery)

        sync_player_tile_position_from_rect(context.player, context.tile_map)

        width = self.data["slash_width"]

        damage_monsters_on_line(context, start, end, width, self.data["damage"])

        system.dash_slash = DashSlashEffect(
            start=start,
            end=end,
            width=width,
            timer=system.dash_slash_duration,
        )

        system.attack_cooldown_timer = self.cooldown

    def draw_icon(self, system, screen, player, player_direction):
        draw_dual_blades_in_hand(screen, player, player_direction)


class BoomerangWeapon(BaseWeapon):
    def use(self, system, context):
        if system.attack_cooldown_timer <= 0:
            if not self.try_spend_energy(context):
                return

            system.boomerangs.append(
                BoomerangProjectile.create(context.player, context.player_direction, self.data)
            )

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

    def use_weapon(self, player, player_direction, monsters, damage_monster, screen_rect, width, height, tile_map=None):
        context = WeaponUseContext(
            player=player,
            player_direction=player_direction,
            monsters=monsters,
            damage_monster=damage_monster,
            screen_rect=screen_rect,
            width=width,
            height=height,
            tile_map=tile_map,
        )

        self.current.use(self, context)

    def update(self, player, player_direction, monsters, damage_monster, screen_rect, tile_map=None):
        self.flag_wave += 1

        if self.sword_slash is not None and not self.sword_slash.update():
            self.sword_slash = None

        if self.dash_slash is not None and not self.dash_slash.update():
            self.dash_slash = None

        if self.flag_swing is not None:
            if not self.flag_swing.update_timer():
                self.flag_swing = None
            elif self.current.name == "Flag":
                self.flag_swing.update_hitbox(
                    player,
                    monsters,
                    damage_monster,
                    self.current.data["damage"],
                    tile_map,
                )

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
            bullet
            for bullet in self.bullets
            if bullet.update(monsters, damage_monster, screen_rect, tile_map)
        ]

        self.spears = [
            spear
            for spear in self.spears
            if spear.update(self, monsters, damage_monster, screen_rect, tile_map)
        ]

        self.boomerangs = [
            b
            for b in self.boomerangs
            if b.update(player, monsters, damage_monster, screen_rect, tile_map)
        ]

        self.shockwaves = [
            wave
            for wave in self.shockwaves
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