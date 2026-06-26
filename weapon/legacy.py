"""Backward-compatible module state and functions for the weapon package."""

from __future__ import annotations

import pygame

from .models import BoomerangProjectile, BulletProjectile, SpearProjectile, WeaponSystem
from .rendering import *

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


def use_weapon(player, player_direction, monsters, damage_monster, screen_rect, width, height, tile_map=None):
    _sync_system_from_exports()
    _default_system.use_weapon(player, player_direction, monsters, damage_monster, screen_rect, width, height, tile_map)
    _sync_exports_from_system()


def update(player, player_direction, monsters, damage_monster, screen_rect, tile_map=None):
    _sync_system_from_exports()
    _default_system.update(player, player_direction, monsters, damage_monster, screen_rect, tile_map)
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
