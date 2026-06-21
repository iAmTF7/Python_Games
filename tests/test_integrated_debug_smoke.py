"""Import/smoke checks for the integrated debug runner."""

from game.debug_game import IntegratedDebugGame
from player import Player
from map import TileMap
from weapon import WeaponSystem
from monster import MonsterSpawner
from level import LevelSystem
from item import DropTable


def test_core_integration_classes_import():
    assert IntegratedDebugGame is not None
    assert Player is not None
    assert TileMap is not None
    assert WeaponSystem is not None
    assert MonsterSpawner is not None
    assert LevelSystem is not None
    assert DropTable is not None
