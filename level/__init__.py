"""Level package public API."""

from .config import LevelConfig
from .legacy import upgrade_armor, upgrade_damage, upgrade_energy, upgrade_hp, upgrade_speed
from .progression import LevelSystem, LevelUpResult
from .upgrades import (
    ArmorUpgrade,
    DamageUpgrade,
    EnergyUpgrade,
    HpUpgrade,
    SpeedUpgrade,
    StatUpgrade,
    StatUpgradeSystem,
)

__all__ = [
    "LevelConfig",
    "LevelSystem",
    "LevelUpResult",
    "StatUpgrade",
    "HpUpgrade",
    "DamageUpgrade",
    "SpeedUpgrade",
    "ArmorUpgrade",
    "EnergyUpgrade",
    "StatUpgradeSystem",
    "upgrade_hp",
    "upgrade_damage",
    "upgrade_energy",
    "upgrade_speed",
    "upgrade_armor",
]
