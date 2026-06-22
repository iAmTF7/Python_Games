"""Monster package.

Canonical OOP monster module for the game.

Exports the public classes so other modules can import from ``monster``
instead of reaching into the internal sub-packages.
"""

from .Entity.base import Entity
from .Monster.base import Monster
from .Monster.melee import MeleeMonster
from .Monster.ranged import RangedMonster
from .Combat.projectile import Projectile
from .Combat.spawner import MonsterSpawner
from .Config.settings import Colors, Settings, MonsterConfig

__all__ = [
    "Entity",
    "Monster",
    "MeleeMonster",
    "RangedMonster",
    "Projectile",
    "MonsterSpawner",
    "Colors",
    "Settings",
    "MonsterConfig",
]

__version__ = "1.1.0"
__author__ = "Thanh"
__part__ = "Combat cua quai"
