"""Compatibility module for stat upgrades."""

from .legacy import upgrade_armor, upgrade_damage, upgrade_energy, upgrade_hp, upgrade_speed
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
    "ArmorUpgrade",
    "DamageUpgrade",
    "EnergyUpgrade",
    "HpUpgrade",
    "SpeedUpgrade",
    "StatUpgrade",
    "StatUpgradeSystem",
    "upgrade_armor",
    "upgrade_damage",
    "upgrade_energy",
    "upgrade_hp",
    "upgrade_speed",
]
