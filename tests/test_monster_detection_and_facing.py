from monster import MeleeMonster, MonsterConfig


class FakeTileMap:
    def __init__(self, has_line_of_sight=True):
        self._has_line_of_sight = has_line_of_sight

    def has_line_of_sight(self, start_pos, end_pos):
        return self._has_line_of_sight

    def is_pixel_rect_walkable(self, rect, *, include_exit=True):
        return True


class DummyTarget:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 30
        self.damage_taken = 0

    def take_damage(self, amount):
        self.damage_taken += amount


def test_melee_facing_tracks_player_during_windup():
    monster = MeleeMonster(100, 100, screen_width=500, screen_height=500)
    target = DummyTarget(100, 100 + MonsterConfig.MELEE_ATTACK_RANGE - 1)

    monster.update(target, [])
    assert monster._state == monster.STATE_WINDUP
    assert abs(monster._facing_x - 0.0) < 0.0001
    assert abs(monster._facing_y - 1.0) < 0.0001

    target.x = 100 + MonsterConfig.MELEE_ATTACK_RANGE - 1
    target.y = 100
    monster.update(target, [])

    assert abs(monster._facing_x - 1.0) < 0.0001
    assert abs(monster._facing_y - 0.0) < 0.0001


def test_detection_ranges_are_larger_than_attack_ranges_where_needed():
    assert MonsterConfig.MELEE_DETECT_RANGE > MonsterConfig.MELEE_ATTACK_RANGE
    assert MonsterConfig.RANGED_DETECT_RANGE > MonsterConfig.RANGED_ATTACK_RANGE


def test_melee_does_not_chase_or_face_player_through_wall():
    monster = MeleeMonster(100, 100, screen_width=500, screen_height=500)
    target = DummyTarget(100 + MonsterConfig.MELEE_ATTACK_RANGE + 20, 100)
    tile_map = FakeTileMap(has_line_of_sight=False)

    monster.update(target, [], tile_map)

    assert monster.position == (100, 100)
    assert monster._state == monster.STATE_CHASING
    assert abs(monster._facing_x - 0.0) < 0.0001
    assert abs(monster._facing_y - 1.0) < 0.0001


def test_melee_does_not_enter_windup_through_wall_in_attack_range():
    monster = MeleeMonster(100, 100, screen_width=500, screen_height=500)
    target = DummyTarget(100 + MonsterConfig.MELEE_ATTACK_RANGE - 1, 100)
    tile_map = FakeTileMap(has_line_of_sight=False)

    monster.update(target, [], tile_map)

    assert monster._state == monster.STATE_CHASING
    assert monster._windup_timer == 0


def test_melee_cancels_windup_if_player_breaks_line_of_sight():
    monster = MeleeMonster(100, 100, screen_width=500, screen_height=500)
    target = DummyTarget(100 + MonsterConfig.MELEE_ATTACK_RANGE - 1, 100)
    visible_map = FakeTileMap(has_line_of_sight=True)
    hidden_map = FakeTileMap(has_line_of_sight=False)

    monster.update(target, [], visible_map)
    assert monster._state == monster.STATE_WINDUP

    monster._windup_timer = 1
    monster.update(target, [], hidden_map)

    assert monster._state == monster.STATE_CHASING
    assert monster._windup_timer == 0
    assert target.damage_taken == 0
