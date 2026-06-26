from level import LevelSystem, StatUpgradeSystem


class DummyPlayer:
    def __init__(self):
        self.level = 1
        self.exp = 0
        self.exp_need = 100
        self.stat_points = 0
        self.max_hp = 100
        self.hp = 60
        self.max_armor = 50
        self.armor = 20
        self.max_energy = 100
        self.energy = 40
        self.damage = 10
        self.speed = 3


def test_level_up_grants_manual_stat_point_without_auto_max_upgrade():
    player = DummyPlayer()
    level_system = LevelSystem(player)

    did_level_up = level_system.add_exp(player.exp_need)

    assert did_level_up is True
    assert player.level == 2
    assert player.stat_points == 1
    assert player.max_hp == 100
    assert player.max_armor == 50
    assert player.max_energy == 100


def test_hp_armor_energy_upgrades_are_manually_selectable():
    player = DummyPlayer()
    player.stat_points = 3
    stat_system = StatUpgradeSystem(player)

    assert stat_system.upgrade("hp") is True
    assert player.max_hp == 120
    assert player.hp == 120

    assert stat_system.upgrade("armor") is True
    assert player.max_armor == 60
    assert player.armor == 60

    assert stat_system.upgrade("energy") is True
    assert player.max_energy == 120
    assert player.energy == 120
    assert player.stat_points == 0


def test_resource_upgrade_fails_without_points():
    player = DummyPlayer()
    stat_system = StatUpgradeSystem(player)

    assert stat_system.upgrade("energy") is False
    assert player.max_energy == 100
    assert player.energy == 40
