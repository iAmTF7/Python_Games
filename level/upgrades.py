"""Polymorphic player stat upgrades."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable


@dataclass(frozen=True)
class StatUpgrade:
    """Base class for a stat upgrade."""

    name: str
    cost: int = 1

    def can_apply(self, player: Any) -> bool:
        return player.stat_points >= self.cost

    def apply(self, player: Any) -> bool:
        """Apply the upgrade if the player can afford it."""
        if not self.can_apply(player):
            return False

        self.apply_effect(player)
        player.stat_points -= self.cost
        return True

    def apply_effect(self, player: Any) -> None:
        raise NotImplementedError("StatUpgrade subclasses must implement apply_effect().")


@dataclass(frozen=True)
class HpUpgrade(StatUpgrade):
    name: str = "hp"
    amount: int = 20

    def apply_effect(self, player: Any) -> None:
        player.max_hp += self.amount
        player.hp = player.max_hp


@dataclass(frozen=True)
class DamageUpgrade(StatUpgrade):
    name: str = "damage"
    amount: int = 5

    def apply_effect(self, player: Any) -> None:
        player.damage += self.amount


@dataclass(frozen=True)
class SpeedUpgrade(StatUpgrade):
    name: str = "speed"
    amount: float = 0.5

    def apply_effect(self, player: Any) -> None:
        player.speed += self.amount


@dataclass(frozen=True)
class ArmorUpgrade(StatUpgrade):
    name: str = "armor"
    amount: int = 10

    def apply_effect(self, player: Any) -> None:
        player.max_armor += self.amount
        player.armor = player.max_armor


@dataclass(frozen=True)
class EnergyUpgrade(StatUpgrade):
    name: str = "energy"
    amount: int = 20

    def apply_effect(self, player: Any) -> None:
        player.max_energy += self.amount
        player.energy = player.max_energy


class StatUpgradeSystem:
    """Owns player stat upgrades."""

    def __init__(self, player: Any, upgrades: Iterable[StatUpgrade] | None = None):
        self.player = player
        self.upgrades: Dict[str, StatUpgrade] = {}

        for upgrade in upgrades or self.default_upgrades():
            self.register(upgrade)

    @staticmethod
    def default_upgrades() -> tuple[StatUpgrade, ...]:
        return (
            HpUpgrade(),
            ArmorUpgrade(),
            EnergyUpgrade(),
            DamageUpgrade(),
            SpeedUpgrade(),
        )

    def bind_player(self, player: Any) -> None:
        self.player = player

    def register(self, upgrade: StatUpgrade) -> None:
        self.upgrades[upgrade.name] = upgrade

    def upgrade(self, stat_name: str) -> bool:
        try:
            upgrade = self.upgrades[stat_name]
        except KeyError as exc:
            available = ", ".join(sorted(self.upgrades))
            raise ValueError(f"Unknown stat upgrade '{stat_name}'. Available: {available}") from exc

        return upgrade.apply(self.player)

    def upgrade_hp(self) -> bool:
        return self.upgrade("hp")

    def upgrade_damage(self) -> bool:
        return self.upgrade("damage")

    def upgrade_speed(self) -> bool:
        return self.upgrade("speed")

    def upgrade_armor(self) -> bool:
        return self.upgrade("armor")

    def upgrade_energy(self) -> bool:
        return self.upgrade("energy")

    def update(self, state: Any = None) -> None:
        """Compatibility hook for the shared system architecture."""
        return None
