from monster import MeleeMonster, MonsterConfig


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
