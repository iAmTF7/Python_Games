"""Polymorphic item effects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ItemEffect:
    """Base class for an item effect."""

    item_type: str

    def apply(self, player: Any) -> None:
        raise NotImplementedError("Item effects must implement apply().")


@dataclass(frozen=True)
class RestoreStatEffect(ItemEffect):
    """Restores a stat without passing its maximum value."""

    stat_name: str
    max_stat_name: str
    amount: int | float

    def apply(self, player: Any) -> None:
        current_value = getattr(player, self.stat_name)
        max_value = getattr(player, self.max_stat_name)
        setattr(player, self.stat_name, min(max_value, current_value + self.amount))


@dataclass(frozen=True)
class UnlockRegenEffect(ItemEffect):
    """Unlocks a regen upgrade once per player."""

    regen_stat_name: str
    regen_value: int | float

    def apply(self, player: Any) -> None:
        if self.item_type in player.special_items:
            return

        setattr(player, self.regen_stat_name, self.regen_value)
        player.special_items.append(self.item_type)


ITEM_EFFECTS: dict[str, ItemEffect] = {
    "heal": RestoreStatEffect("heal", "hp", "max_hp", 20),
    "armor": RestoreStatEffect("armor", "armor", "max_armor", 20),
    "energy": RestoreStatEffect("energy", "energy", "max_energy", 30),
    "regen_hp": UnlockRegenEffect("regen_hp", "hp_regen", 0.2),
    "regen_armor": UnlockRegenEffect("regen_armor", "armor_regen", 0.2),
    "regen_energy": UnlockRegenEffect("regen_energy", "energy_regen", 0.25),
}
