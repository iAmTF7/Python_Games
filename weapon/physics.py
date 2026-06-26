"""Weapon geometry, collision, and shared helper functions."""

from __future__ import annotations

import math
from typing import Callable

import pygame

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


def projectile_blocked_by_wall(tile_map, projectile_rect, previous_center=None):
    """Return True when a player projectile touches or crosses a wall tile.

    Gun bullets and thrown spears move more than one pixel per update, so this
    checks both the projectile's final rect and the swept center line from the
    previous frame.  Inflating wall rects by the projectile size approximates
    swept-rect collision and prevents fast shots from slipping across tile
    seams.
    """
    if tile_map is None:
        return False

    is_walkable = getattr(tile_map, "is_pixel_rect_walkable", None)
    if callable(is_walkable) and not is_walkable(projectile_rect, include_exit=True):
        return True

    if previous_center is None:
        return False

    iter_wall_rects = getattr(tile_map, "iter_wall_rects_between", None)
    if not callable(iter_wall_rects):
        return False

    start = (int(previous_center[0]), int(previous_center[1]))
    end = projectile_rect.center
    if start == end:
        return False

    inflate_x = max(2, projectile_rect.width)
    inflate_y = max(2, projectile_rect.height)
    for wall_rect in iter_wall_rects(start, end):
        if wall_rect.inflate(inflate_x, inflate_y).clipline(start, end):
            return True

    return False
def line_blocked_by_wall(tile_map, start, end, step=4):
    if tile_map is None:
        return False

    start = pygame.Vector2(start)
    end = pygame.Vector2(end)

    direction = end - start
    distance = direction.length()

    if distance <= 0:
        return False

    is_walkable = getattr(tile_map, "is_pixel_rect_walkable", None)

    if callable(is_walkable):
        direction = direction.normalize()
        steps = max(1, int(distance // step))

        for i in range(steps + 1):
            point = start + direction * step * i

            test_rect = pygame.Rect(
                int(point.x) - 5,
                int(point.y) - 5,
                10,
                10,
            )

            if not is_walkable(test_rect, include_exit=True):
                return True

        return False

    iter_wall_rects = getattr(tile_map, "iter_wall_rects_between", None)

    if callable(iter_wall_rects):
        line_start = (int(start.x), int(start.y))
        line_end = (int(end.x), int(end.y))

        for wall_rect in iter_wall_rects(line_start, line_end):
            if wall_rect.clipline(line_start, line_end):
                return True

    return False

def clipped_line_end_by_wall(tile_map, start, end, step=4):
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

        for wall_rect in iter_wall_rects(line_start, line_end):
            clipped = wall_rect.clipline(line_start, line_end)
            if clipped:
                hit_point = pygame.Vector2(clipped[0])
                return start + direction * max(0, start.distance_to(hit_point) - 4)

    return end

def _tile_size_for(tile_map, default=32):
    return int(getattr(tile_map, "tile_size", default) or default)


def sync_player_tile_position_from_rect(player, tile_map=None):
    """Keep tile-space player coordinates aligned with the pixel rect."""
    if player is None or not hasattr(player, "rect"):
        return

    tile_size = _tile_size_for(tile_map)
    sync_tile_position = getattr(player, "sync_tile_position_from_rect", None)
    if callable(sync_tile_position):
        try:
            sync_tile_position(tile_size)
        except TypeError:
            sync_tile_position()
        return

    if hasattr(player, "map_x"):
        player.map_x = player.rect.centerx / tile_size
    if hasattr(player, "map_y"):
        player.map_y = player.rect.centery / tile_size


def find_walkable_dash_end(player_rect, start, desired_end, screen_rect, tile_map=None):
    """Return the farthest dash endpoint whose player rect stays walkable.

    Boundary clamping alone is not enough for dungeon maps because a dash can
    cross or finish inside interior wall tiles.  This samples the swept player
    rect along the dash and stops at the last walkable center before collision.
    """
    target_rect = player_rect.copy()
    target_rect.center = (int(desired_end.x), int(desired_end.y))
    target_rect.clamp_ip(screen_rect)
    desired_end = pygame.Vector2(target_rect.centerx, target_rect.centery)

    is_walkable = getattr(tile_map, "is_pixel_rect_walkable", None) if tile_map is not None else None
    if not callable(is_walkable):
        return desired_end

    dash = desired_end - start
    distance = dash.length()
    if distance <= 0:
        return pygame.Vector2(start.x, start.y)

    step_size = max(2, min(6, player_rect.width // 4, player_rect.height // 4))
    steps = max(1, int(math.ceil(distance / step_size)))
    last_safe = pygame.Vector2(start.x, start.y)

    test_rect = player_rect.copy()
    for step in range(1, steps + 1):
        candidate = start.lerp(desired_end, step / steps)
        test_rect.center = (int(candidate.x), int(candidate.y))
        test_rect.clamp_ip(screen_rect)

        if is_walkable(test_rect, include_exit=True):
            last_safe = pygame.Vector2(test_rect.centerx, test_rect.centery)
            continue

        break

    return last_safe


# =========================
