import pygame

from weapon.weapons import BoomerangProjectile


class DummyPlayer:
    def __init__(self, center):
        self.rect = pygame.Rect(0, 0, 24, 24)
        self.rect.center = center


class OneWallTileMap:
    def __init__(self, wall_rect):
        self.wall_rect = wall_rect
        self.tile_size = wall_rect.width

    def is_pixel_rect_walkable(self, rect, *, include_exit=True):
        return not rect.colliderect(self.wall_rect)

    def iter_wall_rects_between(self, start_pos, end_pos, *, padding_tiles=1):
        yield self.wall_rect


def make_boomerang(x, y, *, direction=(1, 0), returning=False):
    rect = pygame.Rect(x, y, 16, 16)
    return BoomerangProjectile(
        rect=rect,
        pos=pygame.Vector2(x, y),
        dir=pygame.Vector2(direction),
        damage=15,
        speed=30,
        return_speed=30,
        timer=25,
        size=16,
        returning=returning,
    )


def test_boomerang_turns_around_instead_of_passing_through_wall_outbound():
    wall = pygame.Rect(80, 40, 32, 32)
    tile_map = OneWallTileMap(wall)
    screen_rect = pygame.Rect(0, 0, 200, 120)
    player = DummyPlayer((48, 56))
    boomerang = make_boomerang(52, 48, direction=(1, 0), returning=False)

    still_active = boomerang.update(player, [], lambda monster, damage: None, screen_rect, tile_map)

    assert still_active is True
    assert boomerang.returning is True
    assert boomerang.rect == pygame.Rect(52, 48, 16, 16)
    assert not boomerang.rect.colliderect(wall)


def test_returning_boomerang_is_removed_when_a_wall_blocks_its_return_path():
    wall = pygame.Rect(80, 40, 32, 32)
    tile_map = OneWallTileMap(wall)
    screen_rect = pygame.Rect(0, 0, 200, 120)
    player = DummyPlayer((48, 56))
    boomerang = make_boomerang(116, 48, direction=(-1, 0), returning=True)

    still_active = boomerang.update(player, [], lambda monster, damage: None, screen_rect, tile_map)

    assert still_active is False
