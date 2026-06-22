import random

from map import TileMap, WALL
from monster import MonsterSpawner


def rect_is_walkable(tile_map, rect):
    return tile_map.is_pixel_rect_walkable(rect, include_exit=False)


def test_default_map_has_large_playable_spawn_area():
    random.seed(123)
    tile_map = TileMap()

    walkable_tiles = sum(tile != WALL for row in tile_map.grid for tile in row)
    spawn_tiles = list(tile_map.iter_walkable_tiles(clearance=1, include_exit=False))

    assert len(tile_map.rooms) >= 4
    assert walkable_tiles >= 300
    assert len(spawn_tiles) >= 100


def test_map_aware_spawner_places_monsters_on_clear_floor():
    random.seed(123)
    tile_map = TileMap()
    spawner = MonsterSpawner.with_defaults(*tile_map.screen_size)
    target_x, target_y = tile_map.tile_to_pixel_center(*tile_map.start_pos)

    monsters = spawner.spawn_wave(3, target_x, target_y, tile_map)

    assert len(monsters) == spawner.get_enemy_count(3)
    for monster in monsters:
        assert rect_is_walkable(tile_map, monster.get_rect())


def test_monsters_do_not_move_through_map_walls():
    random.seed(456)
    tile_map = TileMap()
    spawner = MonsterSpawner.with_defaults(*tile_map.screen_size)
    target_x, target_y = tile_map.tile_to_pixel_center(*tile_map.start_pos)
    monsters = spawner.spawn_wave(4, target_x, target_y, tile_map)

    class DummyTarget:
        x = target_x
        y = target_y

        def take_damage(self, amount):
            pass

    target = DummyTarget()
    projectiles = []
    for _ in range(120):
        for monster in monsters:
            monster.update(target, projectiles, tile_map)
            monster.separate_from_others(monsters, tile_map)
            assert rect_is_walkable(tile_map, monster.get_rect())
