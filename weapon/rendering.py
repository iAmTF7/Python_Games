"""Weapon rendering helpers."""

from __future__ import annotations

import math

import pygame

from .constants import *
from .physics import entity_rect, normalized_direction, rotate


# =========================
# DRAW HELPERS
# =========================
def _active_system():
    from .legacy import _default_system

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

    system.flag_swing.update_hitbox(
        player,
        monsters,
        damage_monster,
        system.current.data["damage"],
    )


def draw_flag_cloth(screen, px, py, direction, system=None):
    if system is None:
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

    if len(points) >= 3:
        pygame.draw.polygon(screen, FLAG_RED, points)
        pygame.draw.lines(screen, WHITE, True, points, 2)


def draw_flag(screen, player, player_direction, system=None):
    if system is None:
        system = _active_system()

    rect = entity_rect(player)

    if system.flag_swing is not None:
        d = pygame.Vector2(
            system.flag_swing.direction.x,
            system.flag_swing.direction.y,
        )
    else:
        d = pygame.Vector2(
            player_direction.x,
            player_direction.y,
        )

    d = normalized_direction(d)

    if system.flag_swing is not None:
        d = rotate(d, math.radians(system.flag_swing.angle()))

    end = pygame.Vector2(rect.centerx, rect.centery) + d * 52

    pygame.draw.line(
        screen,
        BROWN,
        rect.center,
        (int(end.x), int(end.y)),
        6,
    )

    pygame.draw.circle(
        screen,
        LIGHT_GRAY,
        (int(end.x), int(end.y)),
        7,
    )

    draw_flag_cloth(screen, end.x, end.y, d, system)


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
    d = spear["dir"]
    rect = spear["rect"]

    if d.length() == 0:
        d = pygame.Vector2(0, 1)
    else:
        d = d.normalize()

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

    points = [
        (int(end.x), int(end.y)),
        (int(end.x + left.x), int(end.y + left.y)),
        (int(end.x + right.x), int(end.y + right.y)),
    ]

    pygame.draw.polygon(screen, SPEAR_TIP, points)
    pygame.draw.lines(screen, WHITE, True, points, 1)


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

    pygame.draw.circle(
        screen,
        WHITE,
        (int(long_start.x), int(long_start.y)),
        4,
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (int(short_start.x), int(short_start.y)),
        4,
    )
