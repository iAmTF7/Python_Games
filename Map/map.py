import pygame
import random

TILE = 32
MAP_W, MAP_H = 36, 24
SCREEN_W, SCREEN_H = MAP_W * TILE, MAP_H * TILE

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock = pygame.time.Clock()

FLOOR = 0
WALL = 1
EXIT = 2

LEVEL = 0


def generate_map(level=0):
    grid = [[WALL for _ in range(MAP_W)] for _ in range(MAP_H)]
    rooms = []

    cols, rows = 4, 3
    sector_w = MAP_W // cols
    sector_h = MAP_H // rows

    for sy in range(rows):
        for sx in range(cols):
            w = random.randint(5, 9)
            h = random.randint(4, 7)
            min_x = sx * sector_w + 1
            min_y = sy * sector_h + 1
            max_x = min((sx + 1) * sector_w - w - 1, MAP_W - w - 2)
            max_y = min((sy + 1) * sector_h - h - 1, MAP_H - h - 2)

            if max_x <= min_x or max_y <= min_y:
                continue

            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)
            room = pygame.Rect(x, y, w, h)

            if any(room.colliderect(other.inflate(1, 1)) for other in rooms):
                continue

            rooms.append(room)
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    grid[yy][xx] = FLOOR

    if not rooms:
        rooms.append(pygame.Rect(2, 2, 6, 5))
        for yy in range(2, 7):
            for xx in range(2, 8):
                grid[yy][xx] = FLOOR

    rooms.sort(key=lambda room: (room.centery, room.centerx))
    for i in range(1, len(rooms)):
        x1, y1 = rooms[i - 1].center
        x2, y2 = rooms[i].center

        if random.choice([True, False]):
            for x in range(min(x1, x2), max(x1, x2) + 1):
                grid[y1][x] = FLOOR
            for y in range(min(y1, y2), max(y1, y2) + 1):
                grid[y][x2] = FLOOR
        else:
            for y in range(min(y1, y2), max(y1, y2) + 1):
                grid[y][x1] = FLOOR
            for x in range(min(x1, x2), max(x1, x2) + 1):
                grid[y2][x] = FLOOR

    start_room = rooms[0]
    exit_room = rooms[-1]
    start_pos = start_room.center
    exit_x = exit_room.x + exit_room.w // 2
    exit_y = exit_room.y + exit_room.h // 2
    grid[exit_y][exit_x] = EXIT

    return grid, rooms, start_pos, (exit_x, exit_y)


def load_level(level):
    global game_map, rooms, player_x, player_y, exit_pos, LEVEL

    LEVEL = level
    game_map, rooms, (player_x, player_y), exit_pos = generate_map(level)
    pygame.display.set_caption(f"Map {LEVEL + 1}")


load_level(0)

import math

PLAYER_RADIUS = 0.28  # in tile units
SPEED = 0.1


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def is_wall_at(tx, ty):
    return 0 <= tx < MAP_W and 0 <= ty < MAP_H and game_map[ty][tx] == WALL


def collides(px, py):
    left = math.floor(px - PLAYER_RADIUS)
    right = math.floor(px + PLAYER_RADIUS)
    top = math.floor(py - PLAYER_RADIUS)
    bottom = math.floor(py + PLAYER_RADIUS)

    for ty in range(top, bottom + 1):
        for tx in range(left, right + 1):
            if not is_wall_at(tx, ty):
                continue

            closest_x = clamp(px, tx, tx + 1)
            closest_y = clamp(py, ty, ty + 1)

            dx = px - closest_x
            dy = py - closest_y
            if dx * dx + dy * dy < PLAYER_RADIUS * PLAYER_RADIUS:
                return True

    return False


def find_max_safe_move(px, py, dx, dy):
    low = 0.0
    high = dx if dx != 0 else dy

    for _ in range(8):
        mid = (low + high) / 2.0
        test_x = px + mid if dx != 0 else px
        test_y = py + mid if dy != 0 else py
        if collides(test_x, test_y):
            high = mid
        else:
            low = mid

    return px + low if dx != 0 else py + low


def move_player(px, py, dx, dy):
    if dx != 0:
        target_x = px + dx
        if collides(target_x, py):
            px = find_max_safe_move(px, py, dx, 0)
        else:
            px = target_x

    if dy != 0:
        target_y = py + dy
        if collides(px, target_y):
            py = find_max_safe_move(px, py, 0, dy)
        else:
            py = target_y

    return px, py

running = True
while running:
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    dx = keys[pygame.K_d] - keys[pygame.K_a]
    dy = keys[pygame.K_s] - keys[pygame.K_w]

    player_x, player_y = move_player(player_x, player_y, dx * SPEED, dy * SPEED)

    if int(player_x) == exit_pos[0] and int(player_y) == exit_pos[1]:
        load_level(LEVEL + 1)

    for y, row in enumerate(game_map):
        for x, tile in enumerate(row):
            if tile == FLOOR:
                color = (70, 70, 70)
            elif tile == EXIT:
                color = (60, 180, 80)
            else:
                color = (25, 25, 25)
            pygame.draw.rect(screen, color, (x * TILE, y * TILE, TILE, TILE))

    pygame.draw.circle(
        screen,
        (220, 60, 60),
        (int(player_x * TILE), int(player_y * TILE)),
        int(PLAYER_RADIUS * TILE)
    )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()